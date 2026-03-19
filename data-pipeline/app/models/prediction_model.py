# src/data_pipeline/models/prediction_model.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class Prediction(Base):
    """
    ML model predictions for commodity prices
    Stores predicted prices and model metadata
    """
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Commodity reference
    commodity_name = Column(String(100), nullable=False, index=True)
    region = Column(String(100), index=True)
    
    # Prediction details
    predicted_price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    prediction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    prediction_horizon_days = Column(Integer)  # How many days ahead
    
    # Confidence metrics
    confidence_score = Column(Float)  # 0-1
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    
    # Model information
    model_name = Column(String(100))
    model_version = Column(String(50))
    features_used = Column(JSON)  # List of features used in prediction
    
    # Actual value (for evaluation)
    actual_price = Column(Float)
    prediction_error = Column(Float)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_validated = Column(Boolean, default=False)
    notes = Column(Text)
    
    def __repr__(self):
        return f"<Prediction(commodity={self.commodity_name}, predicted_price={self.predicted_price}, date={self.prediction_date})>"
