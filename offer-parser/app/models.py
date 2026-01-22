"""Pydantic models for request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ParseSourceEnum(str, Enum):
    """Source channel for parsed offer"""
    chat = "chat"
    form = "form"
    api = "api"
    whatsapp = "whatsapp"
    telegram = "telegram"
    email = "email"


class IntentEnum(str, Enum):
    """User intent in natural language"""
    create_offer = "create_offer"
    search = "search"
    unknown = "unknown"


class OfferTypeEnum(str, Enum):
    """Type of offer (sell or buy)"""
    sell = "sell"
    buy = "buy"


class DeliveryTermsEnum(str, Enum):
    """Common delivery terms"""
    fob = "FOB"  # Free on Board
    cif = "CIF"  # Cost, Insurance and Freight
    ddp = "DDP"  # Delivered Duty Paid
    exw = "EXW"  # Ex Works
    fas = "FAS"  # Free Alongside Ship
    cfr = "CFR"  # Cost and Freight
    cpt = "CPT"  # Carriage Paid To
    dap = "DAP"  # Delivered at Place
    unknown = "Unknown"


# ============= REQUEST MODELS =============

class ParseOfferRequest(BaseModel):
    """Request to parse natural language text into offer"""
    
    text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language text describing the offer or search"
    )
    user_id: str = Field(..., description="User ID for context/personalization")
    source: ParseSourceEnum = Field(default=ParseSourceEnum.api, description="Source channel")
    
    class Config:
        examples = [
            {
                "text": "Sell wheat 2 grade in Izmail port Ukraine on FOB 234.56 dollars per ton 560 t amount price actual until 09/02/2026 protein at least 23%",
                "user_id": "user_123",
                "source": "chat"
            },
            {
                "text": "Find me top 5 latest offers of corn to delivery in Shpola Cherkaska oblast Ukraine including cost for delivery DDP by price not more 8600 UAH per ton total amount 200 t until 02/02/2026",
                "user_id": "user_456",
                "source": "api"
            }
        ]


# ============= OFFER CREATION MODELS =============

class QualitySpec(BaseModel):
    """Quality specification for offer"""
    name: str = Field(..., description="Quality parameter (e.g., protein, moisture)")
    value: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    unit: str = Field(default="%", description="Unit of measurement")


class ParsedOffer(BaseModel):
    """Parsed and validated offer data"""
    
    # Core fields
    offer_type: OfferTypeEnum
    crop: str = Field(..., description="Crop type (wheat, corn, etc.)")
    grade: Optional[str] = None
    
    # Quantity
    quantity: float
    quantity_unit: str = Field(default="tonnes")
    
    # Price
    price: float
    price_unit: str = Field(default="USD/tonne")
    
    # Location & Delivery
    location: str = Field(..., description="Port, city, region, or country")
    delivery_terms: DeliveryTermsEnum = Field(default=DeliveryTermsEnum.unknown)
    
    # Timing
    expiry_date: Optional[str] = None  # ISO format YYYY-MM-DD or natural language date
    
    # Quality specs
    quality_specs: List[QualitySpec] = Field(default_factory=list)
    
    # Additional metadata
    description: Optional[str] = None
    raw_text: str = Field(..., description="Original input text")


# ============= SEARCH QUERY MODELS =============

class SearchCriteria(BaseModel):
    """Search query parsed from natural language"""
    
    # What to find
    offer_type: OfferTypeEnum = Field(default=OfferTypeEnum.buy)
    crop: str
    
    # Quantity constraints
    min_quantity: Optional[float] = None
    max_quantity: Optional[float] = None
    quantity_unit: str = Field(default="tonnes")
    
    # Price constraints
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_currency: Optional[str] = None
    
    # Location
    location: Optional[str] = None
    
    # Delivery
    delivery_terms: Optional[List[DeliveryTermsEnum]] = None
    include_delivery_cost: bool = False
    
    # Timing
    expiry_by: Optional[str] = None
    
    # Quality specs
    quality_specs: List[QualitySpec] = Field(default_factory=list)
    
    # Search options
    sort_by: str = Field(default="date_desc")  # date_desc, price_asc, relevance
    limit: int = Field(default=5, ge=1, le=100)


# ============= RESPONSE MODELS =============

class ParseOfferResponse(BaseModel):
    """Response from parsing endpoint"""
    
    success: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Parsed data (if successful)
    offer: Optional[ParsedOffer] = None
    search_query: Optional[SearchCriteria] = None
    
    # Metadata
    intent: IntentEnum
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Error handling
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Processing info
    parsing_method: str = Field(description="llm, regex, or hybrid")
    processing_time_ms: Optional[float] = None
    
    # Suggestions
    suggestions: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    llm_provider: str
    redis_connected: bool
    db_connected: Optional[bool] = None


class BatchParseRequest(BaseModel):
    """Request to parse multiple offers"""
    offers: List[ParseOfferRequest] = Field(..., min_items=1, max_items=100)


class BatchParseResponse(BaseModel):
    """Response for batch parsing"""
    success: bool
    total: int
    succeeded: int
    failed: int
    results: List[ParseOfferResponse]


# ============= DOMAIN MODEL =============

class DomainVocabulary(BaseModel):
    """Domain vocabulary for validation"""
    crops: List[str]
    ports: List[str]
    regions: List[str]
    delivery_terms: List[str]
    currencies: List[str]
