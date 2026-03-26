"""
API endpoints for grain price forecasts.
"""
from datetime import datetime, timedelta, timezone, date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, Date
from sqlalchemy.orm import Session

from app.database import get_db
from app.logger import logger
from app.models import Prediction
from app.schemas.prediction_schema import PredictionResponse

router = APIRouter(prefix="/forecasts", tags=["forecasts"])

def _today_utc() -> date_type:
    """Helper function to get today's date in UTC timezone."""
    return datetime.now(timezone.utc).date()


@router.get("/", response_model=List[PredictionResponse])
def get_forecasts(
    commodity_name: Optional[str] = Query(None, description="Filter by commodity name"),
    region: Optional[str] = Query(None, description="Filter by region"),
    days_ahead: Optional[int] = Query(7, description="Number of days ahead to forecast", ge=1, le=30),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Get grain price forecasts for frontend display.
    
    Returns predictions for upcoming days filtered by commodity and region.
    Used on homepage above offers section.
    """
    query = db.query(Prediction)
    
    # Filter by commodity if specified
    if commodity_name:
        query = query.filter(Prediction.commodity_name == commodity_name)
    
    # Filter by region if specified
    if region:
        query = query.filter(Prediction.region == region)
    
    # Only future predictions within the specified horizon
    today = _today_utc()
    max_date = today + timedelta(days=days_ahead)
    query = query.filter(
        cast(Prediction.prediction_date, Date) >= today,
        cast(Prediction.prediction_date, Date) <= max_date,
    )
    
    # Order by prediction date and limit results
    predictions = query.order_by(
        Prediction.prediction_date.asc(),
        Prediction.commodity_name.asc()
    ).limit(limit).all()

    logger.info(
        "Fetched %d forecasts | commodity=%s | region=%s | days_ahead=%d",
        len(predictions),
        commodity_name or "ALL",
        region or "ALL",
        days_ahead,
    )

    return predictions


@router.get("/homepage", response_model=List[dict])
def get_homepage_forecasts(
    db: Session = Depends(get_db),
):
    """
    Get summarized forecasts for homepage display.
    
    Returns the most relevant forecasts for major commodities with
    simplified data structure optimized for frontend rendering.
    """
    # Focus on key commodities
    key_commodities = [
        "Wheat Futures",
        "Corn Futures", 
        "Soybeans Futures",
        "Wheat ETF",
    ]
    
    today = _today_utc()
    tomorrow = today + timedelta(days=1)
    week_ahead = today + timedelta(days=7)
    
    forecasts = []
    
    for commodity in key_commodities:
        # Get tomorrow's prediction
        next_day_pred = db.query(Prediction).filter(
            Prediction.commodity_name == commodity,
            cast(Prediction.prediction_date, Date) == tomorrow,
        ).order_by(Prediction.created_at.desc()).first()
        
        # Get 7-day ahead prediction
        week_pred = db.query(Prediction).filter(
            Prediction.commodity_name == commodity,
            cast(Prediction.prediction_date, Date) == week_ahead,
        ).order_by(Prediction.created_at.desc()).first()

        logger.debug(
            "Homepage forecast query | commodity=%s | tomorrow=%s | week_ahead=%s",
            commodity,
            next_day_pred.prediction_date if next_day_pred else "None",
            week_pred.prediction_date if week_pred else "None",
        )
        
        if next_day_pred or week_pred:
            forecast_item = {
                "commodity": commodity,
                "region": next_day_pred.region if next_day_pred else week_pred.region,
                "currency": "USD",
                "next_day": {
                    "date": str(tomorrow),
                    "price": float(next_day_pred.predicted_price) if next_day_pred else None,
                    "confidence": float(next_day_pred.confidence_score) if next_day_pred else None,
                } if next_day_pred else None,
                "week_ahead": {
                    "date": str(week_ahead),
                    "price": float(week_pred.predicted_price) if week_pred else None,
                    "confidence": float(week_pred.confidence_score) if week_pred else None,
                    "lower_bound": float(week_pred.lower_bound) if week_pred else None,
                    "upper_bound": float(week_pred.upper_bound) if week_pred else None,
                } if week_pred else None,
            }
            forecasts.append(forecast_item)
    logger.info("Returning %d homepage forecasts", len(forecasts))
    return forecasts


@router.get("/{commodity_name}", response_model=List[PredictionResponse])
def get_commodity_forecast(
    commodity_name: str,
    days_ahead: int = Query(14, description="Number of days ahead", ge=1, le=30),
    db: Session = Depends(get_db),
):
    """
    Get detailed forecast for a specific commodity.
    
    Returns predictions for the specified commodity across multiple horizons.
    """
    today = _today_utc()
    max_date = today + timedelta(days=days_ahead)
    
    predictions = db.query(Prediction).filter(
        Prediction.commodity_name == commodity_name,
        cast(Prediction.prediction_date, Date) >= today,
        cast(Prediction.prediction_date, Date) <= max_date,
    ).order_by(Prediction.prediction_date.asc()).all()
    
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"No forecasts found for commodity: {commodity_name}"
        )
    
    return predictions
