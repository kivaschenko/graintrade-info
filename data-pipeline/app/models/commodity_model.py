# src/data_pipeline/models/commodity_model.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class Commodity(Base):
    """
    Gold layer commodity data model
    Represents processed and cleaned commodity prices ready for analytics
    """
    __tablename__ = "commodities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # wheat, corn, barley, etc.
    variety = Column(String(100))  # e.g., "Soft Red Winter Wheat"
    region = Column(String(100), index=True)  # Black Sea, Ukraine, Russia, etc.
    
    # Price data
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    unit = Column(String(20), default="ton")  # ton, bushel, kg
    
    # Quality parameters
    quality_grade = Column(String(50))
    protein_content = Column(Float)
    moisture_content = Column(Float)
    
    # Temporal data
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Source tracking
    source_type = Column(String(50))  # historical, real-time, forecast
    source_name = Column(String(200))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_validated = Column(Boolean, default=False)
    notes = Column(Text)
    
    def __repr__(self):
        return f"<Commodity(name={self.name}, region={self.region}, price={self.price}, date={self.date})>"
