"""End-to-end pipeline for parsing, transforming, and forecasting grain prices."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import sys
import pandas as pd
import yfinance as yf
from pandas.api.types import is_datetime64tz_dtype

from app.data_sources.investing import InvestingDataSourceError, fetch_investing_history
from app.config import settings
from app.database import SessionLocal
from app.logger import logger
from app.models import Commodity, Prediction
from app.parser_services.yfinance_parser import COMMODITIES
from app.spark_services.spark_session import get_spark_session
from app.utils.rates import fetch_usd_to_uah

# When running this file directly, ensure repository package root is on sys.path
# so `from app...` imports resolve (useful for debugging / direct execution).
if __package__ is None:
    try:
        repo_root = Path(__file__).resolve().parents[2]
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)
    except Exception:
        pass

PIPELINE_SOURCE_NAME = "Yahoo Finance Predictive Pipeline"
MOST_USED_COMMODITIES = [
    "Wheat Futures",
    "Corn Futures",
    "Soybeans Futures",
    "Oats Futures",
    "Rough Rice Futures",
    "Wheat ETF",
    "Corn ETF",
]

COMMODITY_METADATA_OVERRIDES: Dict[str, Dict[str, str]] = {
    "Wheat Futures": {"region": "CBOT", "variety": "Soft Red Winter"},
    "Corn Futures": {"region": "CBOT", "variety": "No.2 Yellow"},
    "Soybeans Futures": {"region": "CBOT", "variety": "No.1 Yellow"},
    "Oats Futures": {"region": "CBOT", "variety": "US Oats"},
    "Rough Rice Futures": {"region": "CBOT", "variety": "US Long Grain"},
    "Wheat ETF": {"region": "NYSE", "variety": "Teucrium Wheat Fund"},
    "Corn ETF": {"region": "NYSE", "variety": "Teucrium Corn Fund"},
    "Soybeans ETF": {"region": "NYSE", "variety": "Teucrium Soybean Fund"},
    "Agricultural Basket": {"region": "NYSE", "variety": "DB Agriculture"},
    "Sugar ETF": {"region": "NYSE", "variety": "CANE"},
}

ADDITIONAL_MARKET_SIGNALS: Dict[str, Dict[str, str]] = {
    "Brent Oil Futures": {
        "ticker": "BZ=F",
        "unit": "barrel",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "macro",
        "description": "ICE Brent crude front-month",
        "region": "ICE",
    },
    "WTI Oil Futures": {
        "ticker": "CL=F",
        "unit": "barrel",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "macro",
        "description": "NYMEX WTI crude front-month",
        "region": "NYMEX",
    },
    "Natural Gas Futures": {
        "ticker": "NG=F",
        "unit": "mmBtu",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "macro",
        "description": "Henry Hub natural gas",
        "region": "NYMEX",
    },
    "US Dollar Index": {
        "ticker": "DX-Y.NYB",
        "unit": "index",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "currency",
        "description": "ICE U.S. Dollar Index",
        "region": "Global",
    },
    # As indicator about war/peace situation in Ukraine and its impact on grain exports
    "Gold Futures": {
        "ticker": "GC=F",
        "unit": "ounce",
        "kg_per_unit": 32.1507,
        "cents_per_dollar": 1,
        "category": "macro",
        "description": "COMEX Gold futures",
        "region": "COMEX",
    },
    "USD/UAH": {
        "ticker": "UAH=X",
        "unit": "pair",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "currency",
        "description": "USD to UAH FX rate",
        "region": "Ukraine",
    },
    "S&P GSCI Agriculture": {
        "ticker": "SPGSAG",
        "unit": "index",
        "kg_per_unit": None,
        "cents_per_dollar": 1,
        "category": "macro",
        "description": "S&P GSCI Agriculture Index",
        "region": "Global",
        "data_source": "investing",
        "investing": {
            "type": "index",
            "symbol": "S&P GSCI Agriculture",
            "country": "world",
        },
    },
}


def _safe_float(value):
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    if pd.isna(value):  # type: ignore[arg-type]
        return None
    return float(value)


def _to_utc_datetime(value) -> datetime:
    # Handle pandas Series by extracting the first value
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            return value.to_pydatetime().replace(tzinfo=timezone.utc)
        return value.to_pydatetime().astimezone(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    raise TypeError(f"Unsupported type for _to_utc_datetime: {type(value)}")


def _ensure_scalar(value):
    """Return a Python scalar when the input is a single-element array/Series.

    If the input is a pandas Series or numpy array with exactly one element,
    return that element as a Python scalar. Otherwise return the value unchanged.
    This avoids ambiguous truth-value checks on Series objects.
    """
    if isinstance(value, (pd.Series, np.ndarray)):
        try:
            if getattr(value, "size", None) == 1:
                return value.item()
        except Exception:
            pass
    return value


class GrainForecastPipeline:
    """High-level orchestrator that parses, transforms, and forecasts grain prices."""

    def __init__(self, history_period: str = "2y", forecast_horizon: int = 7) -> None:
        self.history_period = history_period
        self.forecast_horizon = forecast_horizon
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.artifacts_dir = self.base_dir / "parsers_results" / "grain_forecast"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.bronze_delta_path = f"{settings.BRONZE_LAYER_PATH}/yfinance_grain_bronze"
        self.silver_delta_path = f"{settings.SILVER_LAYER_PATH}/yfinance_grain_silver"
        self.master_config = self._build_master_config()

    def run(self) -> Dict[str, int | float | str]:
        logger.info("Starting grain forecast pipeline")
        usd_to_uah = fetch_usd_to_uah()
        raw_df = self._download_market_history(usd_to_uah)
        if raw_df.empty:
            logger.warning("No market data downloaded: aborting run")
            return {"status": "no_data"}

        bronze_artifact = self._write_parquet_artifact(raw_df, "bronze")
        self._write_delta_table(raw_df, self.bronze_delta_path)

        features_df = self._engineer_features(raw_df)
        silver_artifact = self._write_parquet_artifact(features_df, "silver")
        self._write_delta_table(features_df, self.silver_delta_path)

        synced_records = self._sync_latest_commodities(features_df)
        prediction_payloads = self._make_forecasts(features_df)
        stored_predictions = self._persist_predictions(prediction_payloads)

        summary = {
            "status": "completed",
            "records_ingested": len(raw_df),
            "records_transformed": len(features_df),
            "commodities_updated": synced_records,
            "predictions_saved": stored_predictions,
            "usd_uah_rate": usd_to_uah,
            "bronze_artifact": str(bronze_artifact) if bronze_artifact else "",
            "silver_artifact": str(silver_artifact) if silver_artifact else "",
        }
        logger.info("Grain forecast pipeline completed: %s", summary)
        return summary

    def _build_master_config(self) -> Dict[str, Dict[str, str]]:
        combined: Dict[str, Dict[str, str]] = {}
        for name, cfg in COMMODITIES.items():
            combined[name] = {**cfg}
            combined[name].update(COMMODITY_METADATA_OVERRIDES.get(name, {}))
        for name, cfg in ADDITIONAL_MARKET_SIGNALS.items():
            combined[name] = {**cfg}
        return combined

    def _resolve_history_window(self) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        period = self.history_period.lower()
        days = 365
        try:
            if period.endswith("mo"):
                qty = int(period[:-2])
                days = max(30, qty * 30)
            elif period.endswith("w"):
                qty = int(period[:-1])
                days = max(7, qty * 7)
            elif period.endswith("d"):
                qty = int(period[:-1])
                days = max(1, qty)
            elif period.endswith("y"):
                qty = int(period[:-1])
                days = max(365, qty * 365)
        except ValueError:
            logger.warning("Unable to parse history_period '%s', defaulting to 1y", self.history_period)
        start_date = now - timedelta(days=days)
        return start_date, now

    def _fetch_from_yfinance(self, ticker: str) -> pd.DataFrame:
        try:
            hist = yf.download(
                tickers=ticker,
                period=self.history_period,
                interval="1d",
                auto_adjust=False,
                progress=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to download %s from Yahoo Finance: %s", ticker, exc)
            return pd.DataFrame()

        if hist.empty:
            return hist

        hist = hist.reset_index().rename(columns={"Date": "date"})
        hist["date"] = pd.to_datetime(hist["date"], utc=True)
        return hist

    def _fetch_from_investing(
        self,
        cfg: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        instrument_cfg = cfg.get("investing")
        if not instrument_cfg:
            logger.warning("Missing Investing.com configuration for %s", cfg.get("description", cfg.get("ticker")))
            return pd.DataFrame()
        try:
            return fetch_investing_history(instrument_cfg, start_date, end_date)
        except InvestingDataSourceError as exc:
            logger.error(
                "Investing.com download failed for %s: %s",
                cfg.get("description", instrument_cfg.get("symbol")),
                exc,
            )
            return pd.DataFrame()

    def _download_market_history(self, usd_to_uah: float) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        history_start, history_end = self._resolve_history_window()
        for name, cfg in self.master_config.items():
            if not cfg.get("enabled", True):
                logger.info(
                    "Skipping %s: data source disabled%s",
                    name,
                    f" ({cfg.get('disabled_reason')})" if cfg.get("disabled_reason") else "",
                )
                continue
            data_source = cfg.get("data_source", "yfinance").lower()
            if data_source == "investing":
                hist = self._fetch_from_investing(cfg, history_start, history_end)
            else:
                ticker = cfg.get("ticker")
                if not ticker:
                    logger.warning("Skipping %s: ticker not configured", name)
                    continue
                hist = self._fetch_from_yfinance(ticker)

            if hist.empty:
                logger.warning("No data returned for %s", name)
                continue

            hist = hist.copy()
            if "date" not in hist.columns:
                logger.warning("Skipping %s: history missing 'date' column", name)
                continue
            hist["name"] = name
            hist["ticker"] = cfg.get("ticker") or cfg.get("investing", {}).get("symbol") or name
            hist["category"] = cfg.get("category", "futures")
            hist["unit"] = cfg.get("unit", "unit")
            hist["kg_per_unit"] = cfg.get("kg_per_unit")
            hist["cents_per_dollar"] = cfg.get("cents_per_dollar", 1)
            hist["description"] = cfg.get("description")
            hist["region"] = cfg.get("region", "Global")
            hist["variety"] = cfg.get("variety")

            # compute price in dollars using the configured cents_per_dollar
            cents_per_dollar = float(cfg.get("cents_per_dollar", 1))
            price_in_dollars = hist["Close"].astype(float) / cents_per_dollar
            hist["price_in_dollars"] = price_in_dollars

            kg_per_unit = cfg.get("kg_per_unit")
            if kg_per_unit:
                factor = 1000.0 / kg_per_unit
                hist["usd_per_ton"] = price_in_dollars * factor
            else:
                hist["usd_per_ton"] = np.nan

            hist["uah_price"] = price_in_dollars * usd_to_uah
            hist["uah_per_ton"] = hist["usd_per_ton"] * usd_to_uah
            hist["source_name"] = PIPELINE_SOURCE_NAME

            frames.append(hist)

        if not frames:
            return pd.DataFrame()
        # TODO: verify empty or all-NA entries before combining
        combined_df = pd.concat(frames, ignore_index=True)
        combined_df.sort_values(["ticker", "date"], inplace=True)
        return combined_df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        df.sort_values(["ticker", "date"], inplace=True)
        df["return_1d"] = df.groupby("ticker")["price_in_dollars"].pct_change()
        df["return_7d"] = df.groupby("ticker")["price_in_dollars"].pct_change(periods=7)
        df["return_30d"] = df.groupby("ticker")["price_in_dollars"].pct_change(periods=30)

        df["volatility_30d"] = df.groupby("ticker")["return_1d"].transform(
            lambda s: s.rolling(window=30, min_periods=5).std()
        )
        df["ma_7"] = df.groupby("ticker")["price_in_dollars"].transform(
            lambda s: s.rolling(window=7, min_periods=3).mean()
        )
        df["ma_30"] = df.groupby("ticker")["price_in_dollars"].transform(
            lambda s: s.rolling(window=30, min_periods=10).mean()
        )
        df["momentum_ratio"] = df["ma_7"] / df["ma_30"]
        df["usd_per_ton_filled"] = df.groupby("ticker")["usd_per_ton"].transform(
            lambda s: s.fillna(method="ffill")
        )
        df["uah_per_ton_filled"] = df.groupby("ticker")["uah_per_ton"].transform(
            lambda s: s.fillna(method="ffill")
        )
        return df

    def _write_parquet_artifact(self, df: pd.DataFrame, layer_name: str) -> Path | None:
        try:
            timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            file_path = self.artifacts_dir / f"{layer_name}_{timestamp_slug}.parquet"
            df.to_parquet(file_path, index=False)
            logger.info("Saved %s layer snapshot to %s", layer_name, file_path)
            return file_path
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to write %s artifact: %s", layer_name, exc)
            return None

    def _write_delta_table(self, df: pd.DataFrame, path: str) -> None:
        try:
            export_df = df.copy()
            for column in export_df.columns:
                if is_datetime64tz_dtype(export_df[column]):
                    export_df[column] = (
                        export_df[column].dt.tz_convert("UTC").dt.tz_localize(None)
                    )
            spark = get_spark_session("GrainForecastPipeline")
            spark_df = spark.createDataFrame(export_df)
            (spark_df.write.format("delta").mode("overwrite").option("mergeSchema", "true").save(path))
            logger.info("Persisted Delta table: %s", path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to persist Delta table %s: %s", path, exc)

    def _sync_latest_commodities(self, df: pd.DataFrame) -> int:
        target_df = df[df["category"].isin(["futures", "etf"])]
        if target_df.empty:
            return 0
        latest_records = (
            target_df.sort_values("date").groupby("name", as_index=False).tail(1)
        )
        session = SessionLocal()
        inserted = 0
        try:
            for _, row in latest_records.iterrows():
                record_date = _to_utc_datetime(row["date"])
                usd_per_ton_raw = _ensure_scalar(row.get("usd_per_ton"))
                price_in_dollars_raw = _ensure_scalar(row.get("price_in_dollars"))

                if not pd.isna(usd_per_ton_raw):
                    price_value = float(usd_per_ton_raw)
                    unit = "ton"
                else:
                    price_value = float(price_in_dollars_raw) if not pd.isna(price_in_dollars_raw) else 0.0
                    unit = row.get("unit", "unit")
                existing = (
                    session.query(Commodity)
                    .filter(
                        Commodity.name == row["name"],
                        Commodity.region == row.get("region", "Global"),
                        Commodity.date == record_date,
                        Commodity.source_name == PIPELINE_SOURCE_NAME,
                    )
                    .first()
                )
                notes_payload = {
                    "ma_7": _safe_float(row.get("ma_7")),
                    "ma_30": _safe_float(row.get("ma_30")),
                    "volatility_30d": _safe_float(row.get("volatility_30d")),
                    "momentum_ratio": _safe_float(row.get("momentum_ratio")),
                    "uah_price": _safe_float(row.get("uah_price")),
                }
                notes_str = json.dumps(notes_payload, ensure_ascii=False)
                if existing:
                    existing.price = float(price_value)
                    existing.currency = "USD"
                    existing.unit = unit
                    existing.notes = notes_str
                    session.add(existing)
                    continue

                commodity_row = Commodity(
                    name=row["name"],
                    variety=row.get("variety"),
                    region=row.get("region", "Global"),
                    price=float(price_value),
                    currency="USD",
                    unit=unit,
                    date=record_date,
                    source_type="historical",
                    source_name=PIPELINE_SOURCE_NAME,
                    notes=notes_str,
                )
                session.add(commodity_row)
                inserted += 1
            session.commit()
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logger.error("Failed to sync commodities: %s", exc)
            raise
        finally:
            session.close()
        return inserted

    def _make_forecasts(self, df: pd.DataFrame) -> List[Dict[str, object]]:
        """Generate price forecasts for the most used commodities."""
        logger.info("Generating forecasts for commodities")
        payloads: List[Dict[str, object]] = []
        for commodity_name in MOST_USED_COMMODITIES:
            subset = df[df["name"] == commodity_name].sort_values("date")
            if subset.empty:
                logger.warning("No data to forecast for %s", commodity_name)
                continue
            if subset["price_in_dollars"].dropna().empty:
                continue

            use_ton = subset["usd_per_ton"].notna().any()
            target_series = (
                subset["usd_per_ton"].dropna() if use_ton else subset["price_in_dollars"].dropna()
            )
            if len(target_series) < 20:
                logger.warning("Insufficient history for %s", commodity_name)
                continue

            forecast_stats = self._linear_trend_forecast(target_series)
            last_row = subset.iloc[-1]
            last_date = _to_utc_datetime(last_row["date"])
            price_basis = "usd_per_ton" if use_ton else "price_in_dollars"

            for horizon, predicted_price in enumerate(forecast_stats["predictions"], start=1):
                prediction_date = last_date + timedelta(days=horizon)
                conf_delta = 1.96 * forecast_stats["sigma"]
                lower = max(0.0, predicted_price - conf_delta)
                upper = max(lower, predicted_price + conf_delta)
                confidence_score = float(
                    max(
                        0.05,
                        min(
                            0.95,
                            1.0 - forecast_stats["sigma"] / (abs(predicted_price) + 1e-6),
                        ),
                    )
                )
                features_used = {
                    "window_days": forecast_stats["window"],
                    "history_observations": forecast_stats["history_length"],
                    "slope": forecast_stats["slope"],
                    "intercept": forecast_stats["intercept"],
                    "volatility_30d": _safe_float(last_row.get("volatility_30d")),
                    "ma_7": _safe_float(last_row.get("ma_7")),
                    "ma_30": _safe_float(last_row.get("ma_30")),
                    "price_basis": price_basis,
                    "last_price": _safe_float(target_series.iloc[-1]),
                }
                payloads.append(
                    {
                        "commodity_name": commodity_name,
                        "region": last_row.get("region", "Global"),
                        "predicted_price": float(predicted_price),
                        "currency": "USD",
                        "prediction_date": prediction_date,
                        "prediction_horizon_days": horizon,
                        "confidence_score": confidence_score,
                        "lower_bound": float(lower),
                        "upper_bound": float(upper),
                        "model_name": "LinearTrendRegressor",
                        "model_version": "0.1.0",
                        "features_used": features_used,
                    }
                )
        logger.info("Generated %d forecast payloads", len(payloads))
        return payloads

    def _linear_trend_forecast(self, series: pd.Series, window: int = 90) -> Dict[str, object]:
        clean_series = series.tail(window).astype(float)
        history_length = len(clean_series)
        x = np.arange(history_length)
        slope, intercept = np.polyfit(x, clean_series, 1)
        baseline = slope * x + intercept
        residuals = clean_series - baseline
        sigma = float(residuals.std(ddof=1)) if history_length > 1 else 0.0
        predictions = []
        for step in range(1, self.forecast_horizon + 1):
            idx = history_length + step - 1
            predictions.append(float(slope * idx + intercept))
        return {
            "predictions": predictions,
            "sigma": sigma,
            "slope": float(slope),
            "intercept": float(intercept),
            "history_length": history_length,
            "window": min(window, history_length),
        }

    def _persist_predictions(self, payloads: List[Dict[str, object]]) -> int:
        logger.info("Persisting %d predictions to database", len(payloads))
        if not payloads:
            return 0
        session = SessionLocal()
        upserted = 0
        try:
            for payload in payloads:
                prediction_date = _to_utc_datetime(payload["prediction_date"])
                existing = (
                    session.query(Prediction)
                    .filter(
                        Prediction.commodity_name == payload["commodity_name"],
                        Prediction.region == payload["region"],
                        Prediction.prediction_date == prediction_date,
                        Prediction.prediction_horizon_days == payload["prediction_horizon_days"],
                        Prediction.model_name == payload["model_name"],
                    )
                    .first()
                )

                if existing:
                    existing.predicted_price = payload["predicted_price"]
                    existing.currency = payload["currency"]
                    existing.confidence_score = payload["confidence_score"]
                    existing.lower_bound = payload["lower_bound"]
                    existing.upper_bound = payload["upper_bound"]
                    existing.features_used = payload["features_used"]
                else:
                    session.add(
                        Prediction(
                            commodity_name=payload["commodity_name"],
                            region=payload["region"],
                            predicted_price=payload["predicted_price"],
                            currency=payload["currency"],
                            prediction_date=prediction_date,
                            prediction_horizon_days=payload["prediction_horizon_days"],
                            confidence_score=payload["confidence_score"],
                            lower_bound=payload["lower_bound"],
                            upper_bound=payload["upper_bound"],
                            model_name=payload["model_name"],
                            model_version=payload["model_version"],
                            features_used=payload["features_used"],
                        )
                    )
                    upserted += 1
            session.commit()
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logger.error("Failed to persist predictions: %s", exc)
            raise
        finally:
            session.close()
        return upserted


if __name__ == "__main__":
    pipeline = GrainForecastPipeline()
    pipeline.run()
