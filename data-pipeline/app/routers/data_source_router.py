# src/data_pipeline/routers/data_source_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from ..models import DataSource
from ..schemas import DataSourceCreate, DataSourceResponse, DataSourceUpdate

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


@router.post("/", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
def create_data_source(data_source: DataSourceCreate, db: Session = Depends(get_db)):
    """Create a new data source"""
    db_data_source = DataSource(**data_source.model_dump())
    db.add(db_data_source)
    db.commit()
    db.refresh(db_data_source)
    return db_data_source


@router.get("/", response_model=List[DataSourceResponse])
def list_data_sources(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all data sources"""
    query = db.query(DataSource)
    
    if active_only:
        query = query.filter(DataSource.is_active == True)
    
    data_sources = query.offset(skip).limit(limit).all()
    return data_sources


@router.get("/{data_source_id}", response_model=DataSourceResponse)
def get_data_source(data_source_id: int, db: Session = Depends(get_db)):
    """Get a specific data source by ID"""
    data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_source


@router.patch("/{data_source_id}", response_model=DataSourceResponse)
def update_data_source(
    data_source_id: int,
    data_source_update: DataSourceUpdate,
    db: Session = Depends(get_db)
):
    """Update a data source"""
    db_data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not db_data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    update_data = data_source_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_data_source, key, value)
    
    db.commit()
    db.refresh(db_data_source)
    return db_data_source


@router.delete("/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data_source(data_source_id: int, db: Session = Depends(get_db)):
    """Delete a data source"""
    data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    db.delete(data_source)
    db.commit()
    return None
