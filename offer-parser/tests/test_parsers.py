"""Unit tests for offer parser"""

import pytest
from app.models import ParseOfferRequest, IntentEnum
from app.parsers.regex_parser import RegexOfferParser
from app.validators.offer_validator import OfferValidator


class TestRegexParser:
    """Test regex-based parser"""
    
    @pytest.fixture
    def parser(self):
        return RegexOfferParser()
    
    @pytest.mark.asyncio
    async def test_parse_wheat_offer(self, parser):
        """Test parsing wheat sell offer"""
        text = "Sell wheat 2 grade in Izmail port Ukraine on FOB 234.56 dollars per ton 560 t amount price actual until 09/02/2026 protein at least 23%"
        
        parsed_data, confidence, method = await parser.parse(text)
        
        assert parsed_data["intent"] == "create_offer"
        assert parsed_data["offer_type"] == "sell"
        assert parsed_data.get("crop") is not None
        assert parsed_data.get("quantity") == 560
        assert parsed_data.get("price") == 234.56
        assert confidence > 0.7
        assert method == "regex"
    
    @pytest.mark.asyncio
    async def test_parse_search_query(self, parser):
        """Test parsing search query"""
        text = "Find me top 5 latest offers of corn to delivery in Shpola Cherkaska oblast Ukraine including cost for delivery DDP by price not more 8600 UAH per ton total amount 200 t until 02/02/2026"
        
        parsed_data, confidence, method = await parser.parse(text)
        
        assert parsed_data["intent"] == "search"
        assert "crop" in parsed_data
        assert confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_parse_simple_buy_offer(self, parser):
        """Test parsing simple buy offer"""
        text = "Buying 300 tonnes barley FOB Chornomorsk $280/t"
        
        parsed_data, confidence, method = await parser.parse(text)
        
        assert parsed_data.get("offer_type") == "buy"
        assert parsed_data.get("quantity") == 300
        assert parsed_data.get("price") == 280


class TestOfferValidator:
    """Test offer validator"""
    
    @pytest.fixture
    def validator(self):
        return OfferValidator()
    
    def test_validate_offer_success(self, validator):
        """Test successful offer validation"""
        offer_data = {
            "offer_type": "sell",
            "crop": "wheat",
            "quantity": 500,
            "price": 250,
            "location": "Odesa",
            "raw_text": "test"
        }
        
        validated_offer, warnings = validator.validate_offer(offer_data, 0.95)
        
        assert validated_offer is not None
        assert len(warnings) == 0
    
    def test_validate_offer_missing_crop(self, validator):
        """Test validation fails without crop"""
        offer_data = {
            "offer_type": "sell",
            "quantity": 500,
            "price": 250,
        }
        
        validated_offer, warnings = validator.validate_offer(offer_data, 0.95)
        
        assert validated_offer is None
        assert len(warnings) > 0
    
    def test_validate_offer_low_confidence(self, validator):
        """Test validation with low confidence"""
        offer_data = {
            "offer_type": "sell",
            "crop": "wheat",
            "quantity": 500,
            "price": 250,
            "location": "Odesa",
            "raw_text": "test"
        }
        
        validated_offer, warnings = validator.validate_offer(offer_data, 0.5)
        
        assert validated_offer is not None
        # Should have warning about low confidence
        assert any("confidence" in w.lower() for w in warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
