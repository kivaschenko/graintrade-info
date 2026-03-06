# src/data_pipeline/routers/commodity_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from ..models import Commodity
from ..schemas import CommodityCreate, CommodityResponse, CommodityQuery

router = APIRouter(prefix="/commodities", tags=["commodities"])


@router.post("/", response_model=CommodityResponse, status_code=201)
def create_commodity(commodity: CommodityCreate, db: Session = Depends(get_db)):
    """Create a new commodity record"""
    db_commodity = Commodity(**commodity.model_dump())
    db.add(db_commodity)
    db.commit()
    db.refresh(db_commodity)
    return db_commodity


@router.get("/", response_model=List[CommodityResponse])
def list_commodities(
    name: Optional[str] = Query(None, description="Filter by commodity name"),
    region: Optional[str] = Query(None, description="Filter by region"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    """List commodities with optional filters"""
    query = db.query(Commodity)
    
    if name:
        query = query.filter(Commodity.name.ilike(f"%{name}%"))
    if region:
        query = query.filter(Commodity.region.ilike(f"%{region}%"))
    if start_date:
        query = query.filter(Commodity.date >= start_date)
    if end_date:
        query = query.filter(Commodity.date <= end_date)
    
    commodities = query.offset(offset).limit(limit).all()
    return commodities


@router.get("/{commodity_id}", response_model=CommodityResponse)
def get_commodity(commodity_id: int, db: Session = Depends(get_db)):
    """Get a specific commodity by ID"""
    commodity = db.query(Commodity).filter(Commodity.id == commodity_id).first()
    if not commodity:
        raise HTTPException(status_code=404, detail="Commodity not found")
    return commodity


@router.delete("/{commodity_id}", status_code=204)
def delete_commodity(commodity_id: int, db: Session = Depends(get_db)):
    """Delete a commodity record"""
    commodity = db.query(Commodity).filter(Commodity.id == commodity_id).first()
    if not commodity:
        raise HTTPException(status_code=404, detail="Commodity not found")
    
    db.delete(commodity)
    db.commit()
    return None
