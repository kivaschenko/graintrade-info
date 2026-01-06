# src/data_pipeline/schemas/commodity_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CommodityBase(BaseModel):
    name: str = Field(..., description="Commodity name (e.g., wheat, corn)")
    variety: Optional[str] = Field(None, description="Variety of commodity")
    region: str = Field(..., description="Region (e.g., Ukraine, Russia)")
    price: float = Field(..., gt=0, description="Price value")
    currency: str = Field(default="USD", description="Currency code")
    unit: str = Field(default="ton", description="Unit of measurement")


class CommodityCreate(CommodityBase):
    quality_grade: Optional[str] = None
    protein_content: Optional[float] = None
    moisture_content: Optional[float] = None
    date: datetime
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    notes: Optional[str] = None


class CommodityResponse(CommodityBase):
    id: int
    quality_grade: Optional[str]
    protein_content: Optional[float]
    moisture_content: Optional[float]
    date: datetime
    source_type: Optional[str]
    source_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_validated: bool
    
    class Config:
        from_attributes = True


class CommodityQuery(BaseModel):
    """Query parameters for filtering commodities"""
    name: Optional[str] = None
    region: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)
