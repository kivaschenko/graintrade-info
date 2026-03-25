"""LLM-based offer parser using OpenAI or Anthropic"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

from ..config import settings
from ..models import ParsedOffer, SearchCriteria, IntentEnum, OfferTypeEnum, DeliveryTermsEnum
from .regex_parser import RegexOfferParser

logger = logging.getLogger(__name__)


class LLMOfferParser:
    """Parse natural language offers using LLM"""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.regex_parser = RegexOfferParser()
        self.llm_prompt_template = self._build_prompt_template()
    
    async def parse(self, text: str, user_id: str) -> tuple[Dict[str, Any], float, str]:
        """
        Parse offer text using configured LLM provider.
        
        Returns:
            (parsed_data_dict, confidence_score, parsing_method)
        """
        if len(text.strip()) < 10:
            return {}, 0.0, "none"
        
        try:
            if self.provider == "openai":
                return await self._parse_with_openai(text)
            elif self.provider == "anthropic":
                return await self._parse_with_anthropic(text)
            else:  # fallback
                return await self._parse_with_fallback(text)
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}. Falling back to regex.")
            return await self._parse_with_fallback(text)
    
    async def _parse_with_openai(self, text: str) -> tuple[Dict[str, Any], float, str]:
        """Parse using OpenAI API"""
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured. Using fallback.")
            return await self._parse_with_fallback(text)
        
        try:
            import openai
            openai.api_key = settings.openai_api_key
            
            prompt = self.llm_prompt_template.format(user_text=text)
            
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert parser of agricultural commodity offers. Extract structured data from natural language text. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.choices[0].message.content
            parsed_data = json.loads(response_text)
            
            confidence = parsed_data.pop("confidence", 0.85)
            return parsed_data, confidence, "openai"
            
        except Exception as e:
            logger.error(f"OpenAI parsing error: {e}")
            raise
    
    async def _parse_with_anthropic(self, text: str) -> tuple[Dict[str, Any], float, str]:
        """Parse using Anthropic Claude API"""
        if not settings.anthropic_api_key:
            logger.warning("Anthropic API key not configured. Using fallback.")
            return await self._parse_with_fallback(text)
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            prompt = self.llm_prompt_template.format(user_text=text)
            
            response = await asyncio.to_thread(
                client.messages.create,
                model=settings.anthropic_model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            parsed_data = json.loads(response_text)
            
            confidence = parsed_data.pop("confidence", 0.85)
            return parsed_data, confidence, "anthropic"
            
        except Exception as e:
            logger.error(f"Anthropic parsing error: {e}")
            raise
    
    async def _parse_with_fallback(self, text: str) -> tuple[Dict[str, Any], float, str]:
        """Fallback to regex-based parser"""
        if settings.enable_regex_fallback:
            return await self.regex_parser.parse(text)
        return {}, 0.0, "none"
    
    def _build_prompt_template(self) -> str:
        """Build the LLM prompt for parsing (English & Ukrainian support)"""
        return """Parse the following agricultural offer text and extract structured data.
Supports English and Ukrainian languages.

User Input:
{user_text}

Determine if this is:
1. An OFFER (someone is selling or buying) / ПРОПОЗИЦІЯ (продаю або купую)
2. A SEARCH (someone is looking for offers) / ПОШУК (шукаю пропозиції)

For OFFER, extract / Для ПРОПОЗИЦІЇ:
- offer_type: "sell" or "buy" / "продаж" або "покупка"
- crop: crop type (e.g., wheat, corn, пшениця, кукурудза)
- grade: grade if mentioned (e.g., 1, 2)
- quantity: numeric quantity / числова кількість
- quantity_unit: unit (e.g., tonnes, kg, тонни, кг)
- price: numeric price / числова ціна
- price_unit: unit (e.g., USD/tonne, UAH/t)
- location: port, city, or region / порт, місто чи регіон
- delivery_terms: FOB, CIF, DDP, etc. (leave null if unknown)
- expiry_date: expiration date in YYYY-MM-DD format if mentioned / дата закінчення
- quality_specs: array of {name, value/min/max, unit} (e.g., protein >= 23%, білок >= 23%)
- confidence: confidence score 0.0-1.0

For SEARCH, extract / Для ПОШУКУ:
- intent: "search"
- crop: what crop to find / яку культуру знайти
- offer_type: "buy" or "sell"
- min_quantity, max_quantity: quantity range / діапазон кількості
- max_price: maximum price willing to pay / максимальна ціна
- price_currency: currency
- location: where to deliver / де доставити
- delivery_terms: preferred terms
- include_delivery_cost: boolean
- expiry_by: deadline / крайній термін
- limit: max number of results
- sort_by: date_desc, price_asc, relevance
- confidence: score 0.0-1.0

Return valid JSON only (without markdown formatting). Example:

{
  "intent": "create_offer",
  "offer_type": "sell",
  "crop": "wheat",
  "grade": 2,
  "quantity": 560,
  "quantity_unit": "tonnes",
  "price": 234.56,
  "price_unit": "USD/tonne",
  "location": "Izmail port, Ukraine",
  "delivery_terms": "FOB",
  "expiry_date": "2026-02-09",
  "quality_specs": [{"name": "protein", "min": 23, "unit": "%"}],
  "confidence": 0.98
}

Ukrainian example / Український приклад:
{
  "intent": "create_offer",
  "offer_type": "sell",
  "crop": "Пшениця",
  "quantity": 560,
  "quantity_unit": "тонни",
  "price": 8600,
  "price_unit": "UAH/tonne",
  "location": "Ізмаїл, Україна",
  "delivery_terms": "FOB",
  "expiry_date": "2026-02-09",
  "quality_specs": [{"name": "білок", "min": 23, "unit": "%"}],
  "confidence": 0.95
}"""
