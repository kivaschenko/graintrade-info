# app/services/config_validator.py
"""
Configuration validator for DataSource configs
"""
from typing import Dict, Any, List, Tuple
from app.logger import logger


class ConfigValidator:
    """Validate DataSource config based on parser type"""
    
    REQUIRED_FIELDS = {
        "apk_inform": ["parser_type"],
        "investing_com": ["parser_type", "instruments"],
        "tripoli_land": ["parser_type"],
        "yfinance": ["parser_type", "tickers"],
        "currency": ["parser_type"],
        "graintradecomua": ["parser_type"],
    }
    
    FIELD_TYPES = {
        "apk_inform": {
            "parser_type": str,
            "regions": list,
            "upload_to_storage": bool,
            "storage_type": str,
        },
        "investing_com": {
            "parser_type": str,
            "instruments": list,
            "start_date": str,
            "end_date": str,
            "retry_attempts": int,
        },
        "tripoli_land": {
            "parser_type": str,
            "companies": list,
            "base_url": str,
            "storage_type": str,
            "output_format": str,
        },
        "yfinance": {
            "parser_type": str,
            "tickers": list,
            "period": str,
            "interval": str,
            "progress": bool,
        },
        "currency": {
            "parser_type": str,
        },
        "graintradecomua": {
            "parser_type": str,
            "regions": list,
            "commodities": list,
        }
    }
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate config has all required fields and correct types.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not config:
            return False, ["Config is empty"]
        
        parser_type = config.get("parser_type")
        
        if not parser_type:
            return False, ["Config missing 'parser_type'"]
        
        # Check required fields
        required = ConfigValidator.REQUIRED_FIELDS.get(parser_type, [])
        missing = [field for field in required if field not in config]
        
        if missing:
            errors.append(f"Missing required fields for {parser_type}: {missing}")
        
        # Check field types
        field_types = ConfigValidator.FIELD_TYPES.get(parser_type, {})
        
        for field, expected_type in field_types.items():
            if field in config:
                value = config[field]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field}' should be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
        
        # Type-specific validation
        errors.extend(ConfigValidator._validate_parser_specific(parser_type, config))
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_parser_specific(parser_type: str, config: Dict[str, Any]) -> List[str]:
        """Perform parser-specific validation"""
        errors = []
        
        if parser_type == "investing_com":
            instruments = config.get("instruments", [])
            if instruments:
                if not isinstance(instruments, list):
                    errors.append("'instruments' must be a list")
                elif not all(isinstance(i, dict) for i in instruments):
                    errors.append("Each instrument must be a dictionary")
                elif not any(i.get("symbol") for i in instruments):
                    errors.append("At least one instrument must have a 'symbol'")
        
        elif parser_type == "yfinance":
            tickers = config.get("tickers", [])
            if tickers:
                if not isinstance(tickers, list):
                    errors.append("'tickers' must be a list")
                elif not tickers:
                    errors.append("'tickers' cannot be empty")
            
            period = config.get("period", "2y")
            valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
            if period not in valid_periods:
                errors.append(f"'period' must be one of {valid_periods}")
        
        elif parser_type == "apk_inform":
            if "regions" in config:
                regions = config["regions"]
                if not isinstance(regions, list):
                    errors.append("'regions' must be a list")
        
        elif parser_type == "tripoli_land":
            if "companies" in config:
                companies = config["companies"]
                if not isinstance(companies, list):
                    errors.append("'companies' must be a list")
        
        return errors
    
    @staticmethod
    def is_valid(config: Dict[str, Any]) -> bool:
        """Quick check if config is valid (returns boolean only)"""
        is_valid, _ = ConfigValidator.validate(config)
        return is_valid
    
    @staticmethod
    def get_errors(config: Dict[str, Any]) -> List[str]:
        """Get validation errors (returns empty list if valid)"""
        _, errors = ConfigValidator.validate(config)
        return errors
    
    @staticmethod
    def log_validation(config: Dict[str, Any]) -> bool:
        """Validate and log results"""
        is_valid, errors = ConfigValidator.validate(config)
        
        if is_valid:
            parser_type = config.get("parser_type", "unknown")
            logger.info(f"Config validation passed for {parser_type}")
            return True
        else:
            for error in errors:
                logger.error(f"Config validation error: {error}")
            return False


# Example usage
if __name__ == "__main__":
    # Valid config
    config1 = {
        "parser_type": "apk_inform",
        "regions": ["Odesa", "Mykolaiv"]
    }
    
    is_valid, errors = ConfigValidator.validate(config1)
    print(f"Config 1 valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    
    # Invalid config
    config2 = {
        "parser_type": "yfinance",
        "period": "invalid"
    }
    
    is_valid, errors = ConfigValidator.validate(config2)
    print(f"\nConfig 2 valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  - {error}")
