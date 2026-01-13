# src/data_pipeline/models/ingestion_log_model.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class IngestionLog(Base):
    """
    Log of data ingestion operations
    Tracks each ingestion job for monitoring and debugging
    """
    __tablename__ = "ingestion_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source reference
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    parser_name = Column(String(50), nullable=True)  # apk_inform, yfinance, etc.
    
    # Execution details
    job_id = Column(String(100), unique=True, index=True)
    status = Column(String(20), nullable=False)  # started, running, completed, failed
    layer = Column(String(20))  # bronze, silver, gold
    
    # Metrics
    records_read = Column(Integer, default=0)
    records_written = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    execution_time_seconds = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(Text)
    
    # File/path tracking
    input_path = Column(String(500))
    output_path = Column(String(500))
    
    def __repr__(self):
        return f"<IngestionLog(job_id={self.job_id}, status={self.status}, records={self.records_written})>"
