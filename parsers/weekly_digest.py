# weekly_digest.py
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path

# --- CONFIG ---
# Yahoo tickers to query (futures or ETFs). Replace/add as needed.
TICKERS = {
    "Wheat (ZW)": {
        "ticker": "ZW=F",
        "unit": "bushel",
        "kg_per_unit": 27.2155,
        "label": "Wheat (CBOT)",
        "cents_per_dollar": 100,  # CBOT grain futures quoted in cents/bushel
    },
    "Corn (ZC)": {
        "ticker": "ZC=F",
        "unit": "bushel",
        "kg_per_unit": 25.4012,
        "label": "Corn (CBOT)",
        "cents_per_dollar": 100,  # CBOT grain futures quoted in cents/bushel
    },
    "Soybeans (ZS)": {
        "ticker": "ZS=F",
        "unit": "bushel",
        "kg_per_unit": 27.2155,
        "label": "Soybeans (CBOT)",
        "cents_per_dollar": 100,  # CBOT grain futures quoted in cents/bushel
    },
    "Oats (ZO)": {
        "ticker": "ZO=F",
        "unit": "bushel",
        "kg_per_unit": 14.5150,
        "label": "Oats (CBOT)",
        "cents_per_dollar": 100,  # CBOT grain futures quoted in cents/bushel
    },
    "Rough Rice (ZR)": {
        "ticker": "ZR=F",
        "unit": "cwt",
        "kg_per_unit": 45.359237,
        "cents_per_dollar": 100,  # CBOT futures quoted in cents/cwt
    },  # cwt = 100 lb = 45.359237 kg
    # Example ETF (financial instrument) — note: not direct physical price
    "Wheat ETF (WEAT)": {
        "ticker": "WEAT",
        "unit": "share",
        "kg_per_unit": None,
        "label": "WEAT (ETF)",
        "cents_per_dollar": 1,  # ETF already quoted in dollars/share
    },
}

# Optional: local CSV path with Ukrainian prices (columns: commodity, price_uah_per_ton, price_type, source)
UKR_PRICES_CSV = Path("ukraine_prices.csv")  # optional; if exists it will be read

# Exchange rate API
EXCHANGE_API = "https://api.exchangerate.host/latest?base=USD&symbols=UAH"

# Output
OUTPUT_MD = Path("digest.md")


# --- HELPERS ---
def fetch_usd_to_uah():
    try:
        r = requests.get(EXCHANGE_API, timeout=8)
        r.raise_for_status()
        data = r.json()
        return float(data["rates"]["UAH"])
    except Exception as e:
        # fallback static if API fails
        print("Warning: failed to fetch USD→UAH rate:", e)
        return 41.0


def fetch_price_yf(ticker):
    """Return last close price or None. Handle anomalies in rice futures."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")  # Get more days to detect anomalies
        if hist.empty:
            return None

        # Special handling for rough rice futures (ZR=F) due to pricing anomalies
        if ticker == "ZR=F" and len(hist) > 1:
            recent_prices = hist["Close"].tail(5)
            latest_price = recent_prices.iloc[-1]
            # If latest price is dramatically different from recent average, use previous value
            if len(recent_prices) > 1:
                avg_previous = recent_prices.iloc[:-1].mean()
                if (
                    abs(latest_price - avg_previous) / avg_previous > 0.5
                ):  # 50% difference threshold
                    print(
                        f"Warning: {ticker} latest price {latest_price:.2f} differs significantly from recent average {avg_previous:.2f}, using previous price"
                    )
                    return float(recent_prices.iloc[-2])

        return float(hist["Close"].iloc[-1])
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def unit_to_usd_per_ton(price, kg_per_unit):
    """Convert price quoted per unit (e.g., per bushel or per cwt) into USD/tonne.
    kg_per_unit: how many kg in 1 quoted unit. If None, return None."""
    if price is None or kg_per_unit is None:
        return None
    # 1 tonne = 1000 kg, factor = 1000 / kg_per_unit
    factor = 1000.0 / kg_per_unit
    return price * factor


# --- MAIN LOGIC ---
def build_digest():
    usd_uah = fetch_usd_to_uah()
    rows = []

    for key, cfg in TICKERS.items():
        price = fetch_price_yf(cfg["ticker"])
        usd_per_ton = None
        uah_per_ton = None
        note = ""

        # Convert from cents to dollars if needed
        if price is not None:
            price_in_dollars = price / cfg.get("cents_per_dollar", 1)
        else:
            price_in_dollars = None

        if cfg["unit"] == "share":
            # ETF / share: we keep share price and approximate UAH/share
            if price_in_dollars is not None:
                uah_equiv = price_in_dollars * usd_uah
                rows.append(
                    {
                        "name": cfg.get("label", key),
                        "ticker": cfg["ticker"],
                        "raw_price": price_in_dollars,
                        "unit": "USD/share",
                        "usd_per_ton": None,
                        "uah_per_ton": None,
                        "uah_equiv": uah_equiv,
                        "note": "ETF/financial instrument — not direct physical price",
                    }
                )
            else:
                rows.append(
                    {
                        "name": cfg.get("label", key),
                        "ticker": cfg["ticker"],
                        "raw_price": None,
                        "unit": "USD/share",
                        "usd_per_ton": None,
                        "uah_per_ton": None,
                        "uah_equiv": None,
                        "note": "no data",
                    }
                )
            continue

        # For physical futures quoted in bushel/cwt
        if price_in_dollars is not None and cfg.get("kg_per_unit"):
            usd_per_ton = unit_to_usd_per_ton(price_in_dollars, cfg["kg_per_unit"])
            if usd_per_ton is not None:
                uah_per_ton = usd_per_ton * usd_uah
        else:
            note = (
                "no conversion (missing kg_per_unit)"
                if price_in_dollars is not None
                else "no data"
            )

        rows.append(
            {
                "name": cfg.get("label", key),
                "ticker": cfg["ticker"],
                "raw_price": price_in_dollars,
                "unit": cfg["unit"],
                "usd_per_ton": usd_per_ton,
                "uah_per_ton": uah_per_ton,
                "uah_equiv": None,
                "note": note,
            }
        )

    df_world = pd.DataFrame(rows)

    # Read optional Ukrainian local prices for comparison
    df_ukr = None
    if UKR_PRICES_CSV.exists():
        try:
            df_ukr = pd.read_csv(UKR_PRICES_CSV)
            # Expect columns: commodity (string matching label), price_uah_per_ton (numeric), price_type (EXW/CPT), source
        except Exception as e:
            print("Warning: failed to read ukraine_prices.csv:", e)
            df_ukr = None

    # Build telegram-ready message
    now = datetime.now()
    header = f"📆 *Дайджест зернового ринку* — {now.strftime('%d.%m.%Y')}\n"
    header += f"💱 USD→UAH: {usd_uah:.2f}\n\n"

    body_lines = []
    body_lines.append(
        "🌍 *Світові біржові котирування* (підрахунок у USD/т та UAH/т where applicable):\n"
    )
    for _, r in df_world.iterrows():
        if r["unit"] == "USD/share":
            price_txt = (
                f"{r['raw_price']:.2f} USD/share" if pd.notna(r["raw_price"]) else "—"
            )
            uah_eq = f"{r['uah_equiv']:.0f} ₴/share" if r["uah_equiv"] else ""
            body_lines.append(
                f"• {r['name']} ({r['ticker']}): {price_txt} {uah_eq} — {r['note']}"
            )
        else:
            if pd.notna(r["raw_price"]) and r["usd_per_ton"] is not None:
                body_lines.append(
                    f"• {r['name']} ({r['ticker']}): {r['raw_price']:.2f} USD/{r['unit']} "
                    f"≈ {r['usd_per_ton']:.2f} USD/t ≈ {r['uah_per_ton']:.0f} ₴/t"
                )
            else:
                body_lines.append(f"• {r['name']} ({r['ticker']}): дані недоступні")

    # Add Ukrainian local prices comparison (if provided)
    comp_lines = []
    if df_ukr is not None and not df_ukr.empty:
        comp_lines.append("\n🇺🇦 *Українські ціни (локально, EXW/CPT)*:\n")
        for _, u in df_ukr.iterrows():
            try:
                name = u.get("commodity")
                if not name:
                    continue
                price_uah = float(u.get("price_uah_per_ton", 0))
                price_type = u.get("price_type", "")
                source = u.get("source", "")
                # find corresponding world row by partial matching name
                world_row = df_world[
                    df_world["name"].str.contains(str(name), case=False, na=False)
                ]
                if not world_row.empty and pd.notna(world_row.iloc[0]["usd_per_ton"]):
                    world_uah = world_row.iloc[0]["uah_per_ton"]
                    diff_pct = (
                        ((price_uah - world_uah) / world_uah) * 100
                        if world_uah
                        else None
                    )
                    diff_txt = (
                        f"{diff_pct:.0f}% {'higher' if diff_pct > 0 else 'lower'}"
                        if diff_pct is not None
                        else ""
                    )
                else:
                    diff_txt = ""
                comp_lines.append(
                    f"• {name}: {price_uah:.0f} ₴/t ({price_type}) {source} {diff_txt}"
                )
            except Exception:
                comp_lines.append(
                    f"• {u.get('commodity')}: {u.get('price_uah_per_ton')} ₴/t"
                )

    # Explanations for traders
    explain = (
        "\nℹ️ *Пояснення для трейдерів:*\n"
        "• Світові котирування — це ф'ючерси/ETF (CME/ICE/NYSE) у USD (часто USD/bu або USD/cwt).\n"
        "• Щоб співставити з українською ціною: конвертуйте бушель→тонна (1 т = 1000 / kg_per_unit), "
        "помножте на курс USD→UAH і врахуйте базис/логістику (EXW vs FOB/CPT).\n"
        "• ETF (напр., WEAT) — фінансовий інструмент. Ціна акції не дорівнює USD/т без додатковних перерахунків.\n"
    )

    footer = f"\n🕐 Оновлено: {now.strftime('%H:%M %d.%m.%Y')}\n"
    footer += "🔎 Джерела: Yahoo Finance (ф'ючерси/ETF), локальні дані (якщо надані).\n"

    message = header + "\n".join(body_lines)
    if comp_lines:
        message += "\n" + "\n".join(comp_lines)
    message += "\n" + explain + footer

    # Save markdown file
    try:
        OUTPUT_MD.write_text(message, encoding="utf-8")
        print(f"Saved digest to {OUTPUT_MD}")
    except Exception as e:
        print("Warning: failed to save digest.md:", e)

    # Return message (can be posted to Telegram via your bot)
    return message


if __name__ == "__main__":
    m = build_digest()
    print("\n--- Telegram message preview ---\n")
    print(m)
