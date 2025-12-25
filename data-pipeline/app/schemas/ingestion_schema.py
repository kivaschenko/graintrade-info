# src/data_pipeline/schemas/ingestion_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IngestionJobRequest(BaseModel):
    """Request to start an ingestion job"""
    data_source_id: int = Field(..., description="Data source ID to ingest")
    layer: str = Field(..., description="Target layer: bronze, silver, or gold")
    force: bool = Field(default=False, description="Force re-ingestion even if recent")


class IngestionLogResponse(BaseModel):
    """Ingestion log details"""
    id: int
    data_source_id: int
    job_id: str
    status: str
    layer: Optional[str]
    records_read: int
    records_written: int
    records_failed: int
    execution_time_seconds: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    input_path: Optional[str]
    output_path: Optional[str]
    
    class Config:
        from_attributes = True
