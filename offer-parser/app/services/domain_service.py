"""Domain vocabulary and lookup service"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from ..config import settings

logger = logging.getLogger(__name__)


class DomainService:
    """Manages domain vocabulary (crops, ports, regions, etc.)"""
    
    def __init__(self):
        """Initialize with domain data from JSON files"""
        self.crops = self._load_json(settings.crops_list_path, default_crops())
        self.ports = self._load_json(settings.ports_list_path, default_ports())
        self.regions = self._load_json(settings.regions_list_path, default_regions())
        self.delivery_terms = self._load_json(
            settings.delivery_terms_path, 
            default_delivery_terms()
        )
        self.currencies = self._load_json(
            "./data/currencies.json",
            default_currencies()
        )
        
        logger.info(
            f"Domain vocabulary loaded: {len(self.crops)} crops, "
            f"{len(self.ports)} ports, {len(self.regions)} regions"
        )
    
    @staticmethod
    def _load_json(file_path: str, default: List[str]) -> List[str]:
        """Load JSON list from file or return default"""
        try:
            if Path(file_path).exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}. Using defaults.")
        return default
    
    def find_crop(self, text: str) -> Optional[str]:
        """Find closest matching crop from text"""
        return self._find_closest_match(text.lower(), self.crops)
    
    def find_port(self, text: str) -> Optional[str]:
        """Find closest matching port from text"""
        return self._find_closest_match(text.lower(), self.ports)
    
    def find_region(self, text: str) -> Optional[str]:
        """Find closest matching region from text"""
        return self._find_closest_match(text.lower(), self.regions)
    
    def find_delivery_term(self, text: str) -> Optional[str]:
        """Find closest matching delivery term"""
        return self._find_closest_match(text.upper(), self.delivery_terms)
    
    def normalize_currency(self, text: str) -> Optional[str]:
        """Normalize currency code"""
        normalized = text.upper()
        # Check direct match
        if normalized in self.currencies:
            return normalized
        
        # Check common aliases
        aliases = {
            "DOLLAR": "USD",
            "EURO": "EUR",
            "POUND": "GBP",
            "HRYVNIA": "UAH",
            "ГРИВНЯ": "UAH",
        }
        return aliases.get(normalized)
    
    @staticmethod
    def _find_closest_match(
        text: str,
        candidates: List[str],
        threshold: float = 0.6
    ) -> Optional[str]:
        """Find closest match in candidates list using string similarity"""
        text_lower = text.lower()
        
        # Exact match first
        for candidate in candidates:
            if candidate.lower() == text_lower:
                return candidate
        
        # Partial match (substring)
        for candidate in candidates:
            if candidate.lower() in text_lower or text_lower in candidate.lower():
                return candidate
        
        # Fuzzy match
        best_match = None
        best_ratio = threshold
        
        for candidate in candidates:
            ratio = SequenceMatcher(None, text_lower, candidate.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = candidate
        
        return best_match
    
    def is_valid_crop(self, crop: str) -> bool:
        """Check if crop is in domain vocabulary"""
        return crop.lower() in [c.lower() for c in self.crops]
    
    def is_valid_port(self, port: str) -> bool:
        """Check if port is in domain vocabulary"""
        return port.lower() in [p.lower() for p in self.ports]
    
    def is_valid_delivery_term(self, term: str) -> bool:
        """Check if delivery term is valid"""
        return term.upper() in self.delivery_terms


def default_crops() -> List[str]:
    """Default crop types (English & Ukrainian)"""
    return [
        # Grains (English)
        "Wheat", "Corn", "Barley", "Rye", "Oats", "Millet",
        # Grains (Ukrainian)
        "Пшениця", "Кукурудза", "Ячмінь", "Жито", "Овес", "Просо",
        # Legumes (English)
        "Soybean", "Pea", "Chickpea", "Lentil", "Bean",
        # Legumes (Ukrainian)
        "Соя", "Горох", "Нут", "Сочевиця", "Боби",
        # Oil seeds (English)
        "Sunflower", "Rapeseed", "Safflower", "Sesame",
        # Oil seeds (Ukrainian)
        "Соняшник", "Ріпак", "Сафлор", "Кунжут",
        # Seeds (English & Ukrainian)
        "Seed Wheat", "Seed Barley", "Seed Sunflower",
        "Насіння пшениці", "Насіння ячменю", "Насіння соняшнику",
        # Fertilizers (English & Ukrainian)
        "Urea", "Ammonia Nitrate", "DAP", "MAP", "Potassium Chloride",
        "Сечовина", "Аміачна селітра", "Суперфосфат", "Хлористий калій",
        # Other
        "Flour", "Meal", "Hay", "Straw", "Sugar Beet", "Rice", "Buckwheat",
        "Борошно", "Мука", "Сіно", "Солома", "Цукровий буряк", "Рис", "Гречка"
    ]


def default_ports() -> List[str]:
    """Default Ukrainian and regional ports (English & Ukrainian)"""
    return [
        # Ukrainian Danube ports
        "Izmail", "Reni", "Kilia",
        "Ізмаїл", "Рені", "Кілія",
        # Ukrainian Sea ports
        "Odesa", "Chornomorsk", "Pivdennyy",
        "Одеса", "Чорноморськ", "Південний",
        # Belarusian
        "Brest", "Minsk",
        # Turkish
        "Samsun", "Rize", "Trabzon",
        # Romanian
        "Constanta", "Galati", "Констанца", "Галац",
        # Bulgarian
        "Varna", "Burgas",
        # Middle Eastern
        "Alexandria", "Port Said", "Suez",
    ]


def default_regions() -> List[str]:
    """Default regions in Ukraine and surroundings (English & Ukrainian)"""
    return [
        # Ukrainian regions (English)
        "Kyiv", "Kharkiv", "Odesa", "Dnipropetrovsk", "Donetsk", "Luhansk",
        "Zaporizhzhia", "Kherson", "Mykolaiv", "Cherkasy", "Poltava",
        "Chernihiv", "Sumy", "Zhytomyr", "Vinnytsia", "Khmelnytskyi",
        "Ternopil", "Ivano-Frankivsk", "Lviv", "Volyn",
        # Ukrainian regions (Ukrainian)
        "Київ", "Харків", "Одеса", "Дніпропетровськ", "Донецьк", "Луганськ",
        "Запоріжжя", "Херсон", "Миколаїв", "Черкаси", "Полтава",
        "Чернігів", "Суми", "Житомир", "Вінниця", "Хмельницький",
        "Тернопіль", "Івано-Франківськ", "Львів", "Волинь",
        # Cities
        "Shpola", "Cherkaska",
        "Шпола", "Черкаська",
        # Neighboring countries
        "Poland", "Moldova", "Romania", "Hungary", "Slovakia", "Belarus", "Russia",
        "Польща", "Молдова", "Румунія", "Угорщина", "Словаччина", "Білорусь", "Росія",
    ]


def default_delivery_terms() -> List[str]:
    """Default Incoterms"""
    return [
        "FOB",   # Free on Board
        "CIF",   # Cost, Insurance and Freight
        "DDP",   # Delivered Duty Paid
        "EXW",   # Ex Works
        "FAS",   # Free Alongside Ship
        "CFR",   # Cost and Freight
        "CPT",   # Carriage Paid To
        "DAP",   # Delivered at Place
        "DAT",   # Delivered at Terminal
        "FCA",   # Free Carrier
        "CPT",   # Carriage and Insurance Paid To
    ]


def default_currencies() -> List[str]:
    """Default currencies"""
    return [
        "USD", "EUR", "UAH", "GBP", "CAD", "AUD", "CHF",
        "CNY", "JPY", "INR", "BRL", "RUB", "TRY", "PLN",
    ]
