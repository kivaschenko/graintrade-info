"""Offer validation against domain vocabulary"""

import logging
from typing import Optional, List
from datetime import datetime

from ..models import ParsedOffer, SearchCriteria, DeliveryTermsEnum
from ..services.domain_service import DomainService

logger = logging.getLogger(__name__)


class OfferValidator:
    """Validates parsed offers against domain constraints"""
    
    def __init__(self):
        self.domain = DomainService()
        self.min_confidence = 0.7
    
    def validate_offer(self, offer_data: dict, confidence: float) -> tuple[Optional[ParsedOffer], List[str]]:
        """
        Validate parsed offer data.
        
        Returns:
            (validated_offer_object, list_of_warnings)
        """
        warnings = []
        
        # Check minimum confidence
        if confidence < self.min_confidence:
            warnings.append(f"Low confidence score ({confidence:.2f}). Manual review recommended.")
        
        # Validate crop
        if "crop" not in offer_data or not offer_data.get("crop"):
            warnings.append("Missing crop type")
            return None, warnings
        
        # Validate and normalize crop
        crop = offer_data.get("crop", "").strip()
        normalized_crop = self.domain.find_crop(crop)
        if not normalized_crop:
            warnings.append(f"Crop '{crop}' not recognized. Using as-is.")
            normalized_crop = crop
        offer_data["crop"] = normalized_crop
        
        # Validate quantity
        if "quantity" not in offer_data or offer_data.get("quantity") <= 0:
            warnings.append("Invalid or missing quantity")
            return None, warnings
        
        # Validate price
        if "price" not in offer_data or offer_data.get("price") <= 0:
            warnings.append("Invalid or missing price")
            return None, warnings
        
        # Validate location
        if "location" not in offer_data or not offer_data.get("location"):
            warnings.append("Missing location information")
            # Don't fail, location can be optional in some cases
        else:
            location = offer_data.get("location", "").strip()
            normalized_location = self.domain.find_port(location) or self.domain.find_region(location)
            if not normalized_location:
                warnings.append(f"Location '{location}' not recognized. Using as-is.")
                normalized_location = location
            offer_data["location"] = normalized_location
        
        # Validate delivery terms
        if offer_data.get("delivery_terms"):
            terms = offer_data.get("delivery_terms", "").upper()
            if not self.domain.is_valid_delivery_term(terms):
                warnings.append(f"Unknown delivery term: {terms}")
                offer_data["delivery_terms"] = "Unknown"
        
        # Validate expiry date format
        if offer_data.get("expiry_date"):
            try:
                expiry_str = offer_data.get("expiry_date")
                # Try to parse and re-format to ISO
                from dateutil import parser as date_parser
                parsed = date_parser.parse(expiry_str)
                offer_data["expiry_date"] = parsed.strftime("%Y-%m-%d")
                
                # Check if date is in the past
                if parsed.date() < datetime.now().date():
                    warnings.append(f"Expiry date is in the past: {parsed.date()}")
            except Exception as e:
                warnings.append(f"Invalid expiry date format: {e}")
                offer_data.pop("expiry_date", None)
        
        # Validate quality specs
        if offer_data.get("quality_specs"):
            valid_specs = []
            for spec in offer_data.get("quality_specs", []):
                if isinstance(spec, dict) and "name" in spec:
                    # Validate numeric values
                    if spec.get("value") is not None:
                        try:
                            spec["value"] = float(spec["value"])
                            valid_specs.append(spec)
                        except ValueError:
                            warnings.append(f"Invalid quality spec value: {spec}")
                    else:
                        valid_specs.append(spec)
            offer_data["quality_specs"] = valid_specs
        
        # Build ParsedOffer object
        try:
            parsed_offer = ParsedOffer(**offer_data)
            return parsed_offer, warnings
        except Exception as e:
            warnings.append(f"Failed to construct offer object: {e}")
            return None, warnings
    
    def validate_search_query(self, query_data: dict, confidence: float) -> tuple[Optional[SearchCriteria], List[str]]:
        """
        Validate parsed search query.
        
        Returns:
            (validated_search_criteria, list_of_warnings)
        """
        warnings = []
        
        # Check minimum confidence
        if confidence < 0.5:  # Lower threshold for search queries
            warnings.append(f"Low confidence score ({confidence:.2f}). Results may be inaccurate.")
        
        # Validate crop
        if "crop" not in query_data or not query_data.get("crop"):
            warnings.append("Missing crop type for search")
            return None, warnings
        
        crop = query_data.get("crop", "").strip()
        normalized_crop = self.domain.find_crop(crop)
        if not normalized_crop:
            warnings.append(f"Crop '{crop}' not recognized. Searching anyway.")
            normalized_crop = crop
        query_data["crop"] = normalized_crop
        
        # Validate quantity constraints
        if query_data.get("min_quantity") and query_data.get("max_quantity"):
            if query_data["min_quantity"] > query_data["max_quantity"]:
                warnings.append("Quantity range invalid (min > max). Swapping.")
                query_data["min_quantity"], query_data["max_quantity"] = \
                    query_data["max_quantity"], query_data["min_quantity"]
        
        # Validate price
        if query_data.get("max_price") and query_data["max_price"] <= 0:
            warnings.append("Invalid maximum price constraint")
            query_data.pop("max_price", None)
        
        # Build SearchCriteria object
        try:
            search_criteria = SearchCriteria(**query_data)
            return search_criteria, warnings
        except Exception as e:
            warnings.append(f"Failed to construct search criteria: {e}")
            return None, warnings
