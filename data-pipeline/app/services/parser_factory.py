# app/services/parser_factory.py
"""
Parser Factory - Dynamic parser instantiation based on DataSource configuration
"""
from typing import Dict, Any
from datetime import datetime

from app.models import DataSource
from app.parser_services.base_parser import BaseParser
from app.logger import logger


class ParserFactory:
    """
    Factory for instantiating parsers based on DataSource config.
    
    Supports dynamic parser creation without direct imports in the pipeline.
    Add new parsers by:
    1. Creating parser class inheriting from BaseParser
    2. Adding to PARSER_REGISTRY
    3. Updating _instantiate_parser with parser-specific parameters
    """
    
    PARSER_REGISTRY: Dict[str, type] = {}
    
    @classmethod
    def register(cls, parser_type: str, parser_class: type) -> None:
        """
        Register a parser class.
        
        Args:
            parser_type: Unique identifier (e.g., "apk_inform")
            parser_class: Parser class inheriting from BaseParser
        """
        cls.PARSER_REGISTRY[parser_type] = parser_class
        logger.info(f"Registered parser: {parser_type}")
    
    @classmethod
    def create_parser(cls, data_source: DataSource) -> BaseParser:
        """
        Create a parser instance from DataSource configuration.
        
        Args:
            data_source: DataSource model instance with config
            
        Returns:
            Initialized parser instance
            
        Raises:
            ValueError: If parser_type is unknown or config is invalid
            RuntimeError: If parser instantiation fails
        """
        if not data_source.config:
            raise ValueError(f"DataSource '{data_source.name}' has no config")
        
        parser_type = data_source.config.get("parser_type")
        
        if not parser_type:
            raise ValueError(f"DataSource '{data_source.name}' config missing 'parser_type'")
        
        if parser_type not in cls.PARSER_REGISTRY:
            available = ", ".join(cls.PARSER_REGISTRY.keys())
            raise ValueError(
                f"Unknown parser type: '{parser_type}'. "
                f"Available: {available}"
            )
        
        parser_class = cls.PARSER_REGISTRY[parser_type]
        
        try:
            parser = cls._instantiate_parser(parser_class, data_source.config)
            logger.info(
                f"Created {parser_type} parser for DataSource '{data_source.name}' "
                f"(ID: {data_source.id})"
            )
            return parser
            
        except Exception as e:
            logger.error(
                f"Failed to create {parser_type} parser for DataSource "
                f"'{data_source.name}': {e}"
            )
            raise RuntimeError(f"Parser instantiation failed: {e}") from e
    
    @classmethod
    def _instantiate_parser(cls, parser_class: type, config: Dict[str, Any]) -> BaseParser:
        """
        Instantiate specific parser with config parameters.
        
        Add new parser-specific logic here.
        
        Args:
            parser_class: Parser class to instantiate
            config: Configuration dictionary
            
        Returns:
            Initialized parser instance
            
        Raises:
            ValueError: If required config fields are missing
        """
        parser_type = config.get("parser_type")
        
        if parser_type == "apk_inform":
            from app.parser_services.apk_inform_parser import APKInformParser
            regions = config.get("regions", [])
            return APKInformParser(regions=regions)
        
        elif parser_type == "investing_com":
            from app.parser_services.investingcom_parser import InvestingComParser
            
            instruments = config.get("instruments", [])
            if not instruments:
                raise ValueError("investing_com parser requires 'instruments' in config")
            
            start_date_str = config.get("start_date")
            end_date_str = config.get("end_date")
            
            start_date = cls._parse_datetime(start_date_str) if start_date_str else None
            end_date = cls._parse_datetime(end_date_str) if end_date_str else None
            
            return InvestingComParser(
                instrument_cfg=instruments[0] if instruments else {},
                start_date=start_date,
                end_date=end_date
            )
        
        elif parser_type == "tripoli_land":
            from app.parser_services.tripoli_land_parser import TripoliLandParser
            
            companies = config.get("companies", [])
            return TripoliLandParser(companies=companies)
        
        elif parser_type == "yfinance":
            from app.parser_services.yfinance_parser import YFinanceParser
            
            tickers = config.get("tickers", [])
            if not tickers:
                raise ValueError("yfinance parser requires 'tickers' in config")
            
            period = config.get("period", "2y")
            interval = config.get("interval", "1d")
            
            return YFinanceParser(
                tickers=tickers,
                period=period,
                interval=interval
            )
        
        elif parser_type == "currency":
            from app.parser_services.currency_parser import CurrencyParser
            
            return CurrencyParser()
        
        elif parser_type == "graintradecomua":
            from app.parser_services.graintradecomua_parser import GraintradeComuaParser
            
            regions = config.get("regions", [])
            return GraintradeComuaParser(regions=regions)
        
        else:
            raise ValueError(f"Unknown parser type: {parser_type}")
    
    @staticmethod
    def _parse_datetime(date_str: str) -> datetime:
        """
        Parse datetime string in multiple formats.
        
        Args:
            date_str: Date string in format YYYY-MM-DD or ISO format
            
        Returns:
            datetime object
            
        Raises:
            ValueError: If date string format is invalid
        """
        if isinstance(date_str, datetime):
            return date_str
        
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Cannot parse date: {date_str}")
    
    @classmethod
    def get_supported_parsers(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all supported parsers.
        
        Returns:
            Dictionary with parser info
        """
        return {
            "apk_inform": {
                "description": "APK-Inform Ukrainian grain prices",
                "source_type": "web_scraping",
                "required_config": ["parser_type"],
                "optional_config": ["regions", "upload_to_storage", "storage_type"]
            },
            "investing_com": {
                "description": "Investing.com financial data",
                "source_type": "api",
                "required_config": ["parser_type", "instruments"],
                "optional_config": ["start_date", "end_date", "retry_attempts"]
            },
            "tripoli_land": {
                "description": "Tripoli Land company prices",
                "source_type": "web_scraping",
                "required_config": ["parser_type"],
                "optional_config": ["companies", "base_url", "storage_type"]
            },
            "yfinance": {
                "description": "Yahoo Finance market data",
                "source_type": "api",
                "required_config": ["parser_type", "tickers"],
                "optional_config": ["period", "interval", "progress"]
            },
            "currency": {
                "description": "Currency exchange rates",
                "source_type": "api",
                "required_config": ["parser_type"],
                "optional_config": []
            },
            "graintradecomua": {
                "description": "Grain Trade com UA Ukrainian prices",
                "source_type": "web_scraping",
                "required_config": ["parser_type"],
                "optional_config": ["regions", "commodities"]
            }
        }
