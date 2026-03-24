# src/data_pipeline/models/data_source_model.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class DataSource(Base):
    """
    Metadata about data sources
    Tracks different data sources used for ingestion
    """
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # csv, json, api, telegram, web_scraping
    description = Column(Text)
    
    # Connection details
    url = Column(String(500))
    file_path = Column(String(500))
    api_endpoint = Column(String(500))
    credentials_required = Column(Boolean, default=False)
    
    # Configuration
    config = Column(JSON)  # Store flexible configuration as JSON
    
    # Schedule
    update_frequency = Column(String(50))  # daily, hourly, real-time, weekly
    last_ingestion = Column(DateTime(timezone=True))
    next_scheduled_ingestion = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<DataSource(name={self.name}, type={self.source_type}, active={self.is_active})>"
