# src/data_pipeline/schemas/prediction_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PredictionRequest(BaseModel):
    """Request for price prediction"""
    commodity_name: str = Field(..., description="Commodity to predict")
    region: str = Field(..., description="Region for prediction")
    prediction_horizon_days: int = Field(..., ge=1, le=365, description="Days ahead to predict")
    model_name: Optional[str] = Field(None, description="Specific model to use")


class PredictionResponse(BaseModel):
    """Prediction result"""
    id: int
    commodity_name: str
    region: str
    predicted_price: float
    currency: str
    prediction_date: datetime
    prediction_horizon_days: Optional[int]
    confidence_score: Optional[float]
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    model_name: Optional[str]
    model_version: Optional[str]
    features_used: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True
