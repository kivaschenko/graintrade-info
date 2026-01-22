"""Main FastAPI application for Offer Parser service"""

import logging
import time
from typing import List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    ParseOfferRequest, ParseOfferResponse, HealthResponse,
    BatchParseRequest, BatchParseResponse
)
from .parsers.llm_parser import LLMOfferParser
from .validators.offer_validator import OfferValidator
from .services.domain_service import DomainService

# Configure logging
logging.basicConfig(
    level=settings.log_level.upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Offer Parser Service",
    description="Natural language parser for agricultural commodity offers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
parser = LLMOfferParser()
validator = OfferValidator()
domain_service = DomainService()


# ============= HEALTH & STATUS =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        llm_provider=settings.llm_provider,
        redis_connected=await _check_redis_connection(),
        db_connected=await _check_db_connection() if settings.database_url else None
    )


@app.get("/status")
async def get_status():
    """Service status and configuration"""
    return {
        "service": "offer-parser",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "llm_provider": settings.llm_provider,
            "min_confidence": settings.min_confidence_threshold,
            "regex_fallback_enabled": settings.enable_regex_fallback,
            "debug": settings.debug,
        },
        "domain_vocab_size": {
            "crops": len(domain_service.crops),
            "ports": len(domain_service.ports),
            "regions": len(domain_service.regions),
            "currencies": len(domain_service.currencies),
        }
    }


# ============= MAIN PARSING ENDPOINTS =============

@app.post("/parse", response_model=ParseOfferResponse)
async def parse_offer(request: ParseOfferRequest) -> ParseOfferResponse:
    """
    Parse natural language text into structured offer or search query.
    
    Supports both offer creation and search intents.
    Uses LLM if configured, falls back to regex parsing.
    """
    start_time = time.time()
    
    try:
        # Validate input
        if len(request.text.strip()) < 10:
            return ParseOfferResponse(
                success=False,
                timestamp=datetime.utcnow(),
                error="Text too short (minimum 10 characters)",
                intent="unknown",
                confidence=0.0,
                parsing_method="none"
            )
        
        if len(request.text) > settings.max_text_length:
            return ParseOfferResponse(
                success=False,
                timestamp=datetime.utcnow(),
                error=f"Text too long (maximum {settings.max_text_length} characters)",
                intent="unknown",
                confidence=0.0,
                parsing_method="none"
            )
        
        # Parse text
        parsed_data, confidence, parsing_method = await parser.parse(request.text, request.user_id)
        
        if not parsed_data:
            return ParseOfferResponse(
                success=False,
                timestamp=datetime.utcnow(),
                error="Failed to parse text",
                intent="unknown",
                confidence=0.0,
                parsing_method=parsing_method
            )
        
        intent = parsed_data.get("intent", "unknown")
        
        # Validate and structure data
        if intent == "create_offer":
            parsed_data["raw_text"] = request.text
            offer, warnings = validator.validate_offer(parsed_data, confidence)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ParseOfferResponse(
                success=offer is not None,
                timestamp=datetime.utcnow(),
                offer=offer,
                search_query=None,
                intent=intent,
                confidence=confidence,
                error=None if offer else "Validation failed",
                error_details={"warnings": warnings} if warnings else None,
                parsing_method=parsing_method,
                processing_time_ms=processing_time,
                suggestions=warnings
            )
        
        elif intent == "search":
            search_query, warnings = validator.validate_search_query(parsed_data, confidence)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ParseOfferResponse(
                success=search_query is not None,
                timestamp=datetime.utcnow(),
                offer=None,
                search_query=search_query,
                intent=intent,
                confidence=confidence,
                error=None if search_query else "Validation failed",
                error_details={"warnings": warnings} if warnings else None,
                parsing_method=parsing_method,
                processing_time_ms=processing_time,
                suggestions=warnings
            )
        
        else:
            return ParseOfferResponse(
                success=False,
                timestamp=datetime.utcnow(),
                error="Could not determine intent (offer or search)",
                intent="unknown",
                confidence=confidence,
                parsing_method=parsing_method
            )
    
    except Exception as e:
        logger.exception(f"Error parsing offer: {e}")
        
        return ParseOfferResponse(
            success=False,
            timestamp=datetime.utcnow(),
            error="Internal server error during parsing",
            error_details={"exception": str(e)},
            intent="unknown",
            confidence=0.0,
            parsing_method="error"
        )


@app.post("/parse/batch", response_model=BatchParseResponse)
async def parse_batch(request: BatchParseRequest) -> BatchParseResponse:
    """
    Parse multiple offers in a single request.
    
    Useful for bulk processing or imports.
    """
    results = []
    succeeded = 0
    failed = 0
    
    for offer_req in request.offers:
        response = await parse_offer(offer_req)
        results.append(response)
        
        if response.success:
            succeeded += 1
        else:
            failed += 1
    
    return BatchParseResponse(
        success=failed == 0,
        total=len(request.offers),
        succeeded=succeeded,
        failed=failed,
        results=results
    )


# ============= DOMAIN DATA ENDPOINTS =============

@app.get("/domain/crops")
async def get_crops_vocabulary():
    """Get list of recognized crops"""
    return {
        "crops": domain_service.crops,
        "count": len(domain_service.crops)
    }


@app.get("/domain/ports")
async def get_ports_vocabulary():
    """Get list of recognized ports"""
    return {
        "ports": domain_service.ports,
        "count": len(domain_service.ports)
    }


@app.get("/domain/regions")
async def get_regions_vocabulary():
    """Get list of recognized regions"""
    return {
        "regions": domain_service.regions,
        "count": len(domain_service.regions)
    }


@app.get("/domain/delivery-terms")
async def get_delivery_terms():
    """Get list of recognized delivery terms (Incoterms)"""
    return {
        "delivery_terms": domain_service.delivery_terms,
        "count": len(domain_service.delivery_terms)
    }


@app.get("/domain/currencies")
async def get_currencies():
    """Get list of recognized currencies"""
    return {
        "currencies": domain_service.currencies,
        "count": len(domain_service.currencies)
    }


# ============= UTILITY ENDPOINTS =============

@app.get("/examples")
async def get_examples():
    """Get example inputs and outputs"""
    return {
        "examples": [
            {
                "input": "Sell wheat 2 grade in Izmail port Ukraine on FOB 234.56 dollars per ton 560 t amount price actual until 09/02/2026 protein at least 23%",
                "expected_intent": "create_offer",
                "description": "Seller listing wheat with specific grade, quantity, price, location, delivery terms, expiry, and quality specs"
            },
            {
                "input": "Find me top 5 latest offers of corn to delivery in Shpola Cherkaska oblast Ukraine including cost for delivery DDP by price not more 8600 UAH per ton total amount 200 t until 02/02/2026",
                "expected_intent": "search",
                "description": "Buyer searching for corn with price limit, delivery location, delivery cost included, and deadline"
            },
            {
                "input": "Buying 300 tonnes barley FOB Chornomorsk $280/t",
                "expected_intent": "create_offer",
                "description": "Simple buy offer with minimal details"
            },
            {
                "input": "Looking for sunflower seeds, must be delivered to Kyiv by next month",
                "expected_intent": "search",
                "description": "Simple search query"
            }
        ]
    }


# ============= ERROR HANDLERS =============

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============= HELPER FUNCTIONS =============

async def _check_redis_connection() -> bool:
    """Check Redis connectivity"""
    try:
        import aioredis
        redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis.ping()
        await redis.close()
        return True
    except Exception:
        return False


async def _check_db_connection() -> bool:
    """Check database connectivity"""
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


# ============= STARTUP/SHUTDOWN =============

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Offer Parser service starting...")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Min confidence threshold: {settings.min_confidence_threshold}")
    logger.info("Service ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Offer Parser service shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
