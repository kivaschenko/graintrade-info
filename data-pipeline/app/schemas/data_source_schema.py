# src/data_pipeline/schemas/data_source_schema.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime


class DataSourceBase(BaseModel):
    name: str = Field(..., description="Data source name")
    source_type: str = Field(..., description="Type: csv, json, api, telegram, web_scraping")
    description: Optional[str] = None
    update_frequency: Optional[str] = Field(None, description="Update frequency: daily, hourly, real-time")


class DataSourceCreate(DataSourceBase):
    url: Optional[str] = None
    file_path: Optional[str] = None
    api_endpoint: Optional[str] = None
    credentials_required: bool = False
    config: Optional[Dict[str, Any]] = None
    is_active: bool = True


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    api_endpoint: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    update_frequency: Optional[str] = None
    is_active: Optional[bool] = None


class DataSourceResponse(DataSourceBase):
    id: int
    url: Optional[str]
    file_path: Optional[str]
    api_endpoint: Optional[str]
    credentials_required: bool
    config: Optional[Dict[str, Any]]
    last_ingestion: Optional[datetime]
    next_scheduled_ingestion: Optional[datetime]
    is_active: bool
    is_validated: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
