"""Regex-based fallback parser for offers"""

import re
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dateutil import parser as date_parser

from ..services.domain_service import DomainService

logger = logging.getLogger(__name__)


class RegexOfferParser:
    """Regex-based parser for structured agricultural offer extraction"""
    
    def __init__(self):
        self.domain = DomainService()
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for common offer formats (English & Ukrainian)"""
        
        # Intent patterns (English & Ukrainian)
        self.intent_sell = re.compile(
            r'\b(sell|selling|sale|vend|offer|have for sale|продаю|продажа|пропоную|мають на продаж)\b', 
            re.IGNORECASE | re.UNICODE
        )
        self.intent_buy = re.compile(
            r'\b(buy|buying|purchase|looking for|need|want|find me|купую|покупаю|шукаю|потребую|знайти)\b', 
            re.IGNORECASE | re.UNICODE
        )
        
        # Quantity patterns: "560 tonnes", "200t", "100 tons", "560 t", "560 тонн", "200 т"
        self.quantity_pattern = re.compile(
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:tonnes?|tons?|metric\s+tons?|m\.?t\.?|t(?:\s|$|[^a-z])|тонн[и]?|т(?:\s|$|[^а-я]))',
            re.IGNORECASE | re.UNICODE
        )
        
        # Price patterns: "$320/t", "234.56 USD per tonne", "8600 UAH", "320 грн за тонну"
        self.price_pattern = re.compile(
            r'(?:price|cost|rate|fee|ціна|вартість|коштує)?\s*(?:\$|€|¥|₴)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:per|\/|\s|за)(\w+)?',
            re.IGNORECASE | re.UNICODE
        )
        
        # Currency pattern: "USD", "UAH", "EUR", "грн"
        self.currency_pattern = re.compile(r'\b([A-Z]{3}|грн|зл)\b', re.UNICODE)
        
        # Date patterns: various formats (English & Ukrainian)
        self.date_pattern = re.compile(
            r'(?:until|by|before|till|deadline|expir[ey]|valid|до|по|на|листопада|грудня|січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня)\s*(?:date|дата)?\s*(?:of|is|з|на)?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            re.IGNORECASE | re.UNICODE
        )
        
        # Delivery terms: FOB, CIF, DDP, etc. + Ukrainian variants
        self.delivery_terms_pattern = re.compile(
            r'\b(FOB|CIF|DDP|EXW|FAS|CFR|CPT|DAP|DAT|FCA)\b',
            re.IGNORECASE
        )
        
        # Quality specs: "protein at least 23%", "moisture max 15%", "білок щонайменше 23%"
        self.quality_pattern = re.compile(
            r'(protein|moisture|ash|fiber|fat|acid|gluten|starch|falling|wet|білок|вологість|зола|клітковина|жир|кислота|крохмаль)\s*(?:at\s|щонайменше|максимум)?(?:least|max|minimum|maximum|>|<|=)?\s*(\d+(?:\.\d+)?)\s*(%)?',
            re.IGNORECASE | re.UNICODE
        )
        
        # Port pattern
        self.port_keywords = re.compile(
            r'\b(port|harbor|dock|terminal|pier)\b',
            re.IGNORECASE
        )
    
    async def parse(self, text: str) -> tuple[Dict[str, Any], float, str]:
        """
        Parse offer using regex patterns.
        
        Returns:
            (parsed_data_dict, confidence_score, parsing_method)
        """
        result = {
            "raw_text": text,
            "confidence": 0.0,
            "intent": self._detect_intent(text),
        }
        
        confidence_score = 0.0
        extracted_count = 0
        
        # Detect intent
        if result["intent"] == "create_offer":
            result.update(self._extract_offer(text))
            # Calculate confidence based on extracted fields
            extracted_count = sum(1 for k, v in result.items() if v and k != "raw_text")
            confidence_score = min(1.0, extracted_count / 5.0)  # Normalize to key fields
        else:
            result.update(self._extract_search_query(text))
            extracted_count = sum(1 for k, v in result.items() if v and k != "raw_text")
            confidence_score = min(1.0, extracted_count / 4.0)
        
        result["confidence"] = confidence_score
        return result, confidence_score, "regex"
    
    def _detect_intent(self, text: str) -> str:
        """Detect if user intends to create offer or search"""
        text_lower = text.lower()
        
        sell_match = self.intent_sell.search(text)
        buy_match = self.intent_buy.search(text)
        
        # If both mentioned, check keyword order or context
        if sell_match and buy_match:
            sell_pos = sell_match.start()
            buy_pos = buy_match.start()
            return "create_offer" if sell_pos < buy_pos else "search"
        elif sell_match:
            return "create_offer"
        elif buy_match:
            return "search" if "find me" in text_lower or "find " in text_lower else "create_offer"
        else:
            return "unknown"
    
    def _extract_offer(self, text: str) -> Dict[str, Any]:
        """Extract offer data from text"""
        offer = {}
        
        # Offer type
        if self.intent_sell.search(text):
            offer["offer_type"] = "sell"
        elif self.intent_buy.search(text):
            offer["offer_type"] = "buy"
        
        # Crop
        crop = self._extract_crop(text)
        if crop:
            offer["crop"] = crop
        
        # Grade
        grade = self._extract_grade(text)
        if grade:
            offer["grade"] = grade
        
        # Quantity
        qty_data = self._extract_quantity(text)
        if qty_data:
            offer.update(qty_data)
        
        # Price
        price_data = self._extract_price(text)
        if price_data:
            offer.update(price_data)
        
        # Location
        location = self._extract_location(text)
        if location:
            offer["location"] = location
        
        # Delivery terms
        terms = self._extract_delivery_terms(text)
        if terms:
            offer["delivery_terms"] = terms
        
        # Expiry date
        expiry = self._extract_expiry_date(text)
        if expiry:
            offer["expiry_date"] = expiry
        
        # Quality specs
        specs = self._extract_quality_specs(text)
        if specs:
            offer["quality_specs"] = specs
        
        return offer
    
    def _extract_search_query(self, text: str) -> Dict[str, Any]:
        """Extract search query from text"""
        query = {
            "intent": "search",
            "offer_type": "sell" if self.intent_buy.search(text) else "buy",
        }
        
        # Crop
        crop = self._extract_crop(text)
        if crop:
            query["crop"] = crop
        
        # Quantity range
        qty_data = self._extract_quantity(text)
        if qty_data:
            query["min_quantity"] = qty_data.get("quantity", qty_data.get("min_quantity"))
            query["max_quantity"] = qty_data.get("quantity", qty_data.get("max_quantity"))
        
        # Price constraint
        price_data = self._extract_price(text)
        if price_data:
            query["max_price"] = price_data.get("price")
            query["price_currency"] = price_data.get("price_unit", "").split("/")[0]
        
        # Location
        location = self._extract_location(text)
        if location:
            query["location"] = location
        
        # Delivery terms
        terms = self._extract_delivery_terms(text)
        if terms:
            query["delivery_terms"] = [terms]
        
        # Expiry
        expiry = self._extract_expiry_date(text)
        if expiry:
            query["expiry_by"] = expiry
        
        # Delivery cost inclusion
        if "including" in text.lower() and "cost" in text.lower():
            query["include_delivery_cost"] = True
        
        return query
    
    def _extract_crop(self, text: str) -> Optional[str]:
        """Extract crop type from text"""
        # Find the most likely crop name in domain
        words = text.split()
        for word in words:
            crop = self.domain.find_crop(word)
            if crop:
                return crop
        return None
    
    def _extract_grade(self, text: str) -> Optional[str]:
        """Extract grade (usually 1-4 for grains)"""
        # Look for "grade 1", "grade 2", "1st grade", etc.
        grade_pattern = re.compile(r'grade\s*(\d)\b|(\d)(?:st|nd|rd|th)?\s*grade', re.IGNORECASE)
        match = grade_pattern.search(text)
        if match:
            return match.group(1) or match.group(2)
        return None
    
    def _extract_quantity(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract quantity and unit"""
        match = self.quantity_pattern.search(text)
        if match:
            qty_str = match.group(1).replace(",", "")
            try:
                quantity = float(qty_str)
                return {
                    "quantity": quantity,
                    "quantity_unit": "tonnes"
                }
            except ValueError:
                pass
        return None
    
    def _extract_price(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract price and currency"""
        # Try to find price patterns
        price_match = self.price_pattern.search(text)
        if price_match:
            price_str = price_match.group(1).replace(",", "")
            try:
                price = float(price_str)
                
                # Find currency
                currency = None
                currency_match = self.currency_pattern.search(text)
                if currency_match:
                    currency = self.domain.normalize_currency(currency_match.group(1))
                
                if not currency:
                    # Default to USD if not specified
                    currency = "USD"
                
                return {
                    "price": price,
                    "price_unit": f"{currency}/tonne"
                }
            except ValueError:
                pass
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location (port, city, region)"""
        # Look for port names
        for port in self.domain.ports:
            if port.lower() in text.lower():
                return port
        
        # Look for region names
        for region in self.domain.regions:
            if region.lower() in text.lower():
                return region
        
        return None
    
    def _extract_delivery_terms(self, text: str) -> Optional[str]:
        """Extract delivery terms (FOB, CIF, etc.)"""
        match = self.delivery_terms_pattern.search(text)
        if match:
            return match.group(1).upper()
        return None
    
    def _extract_expiry_date(self, text: str) -> Optional[str]:
        """Extract expiry/deadline date"""
        match = self.date_pattern.search(text)
        if match:
            date_str = match.group(1)
            try:
                parsed_date = date_parser.parse(date_str)
                return parsed_date.strftime("%Y-%m-%d")
            except Exception as e:
                logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None
    
    def _extract_quality_specs(self, text: str) -> list:
        """Extract quality specifications"""
        specs = []
        for match in self.quality_pattern.finditer(text):
            param_name = match.group(1).lower()
            value_str = match.group(2)
            try:
                value = float(value_str)
                spec = {
                    "name": param_name,
                    "min": value,
                    "unit": "%"
                }
                specs.append(spec)
            except ValueError:
                pass
        return specs
