"""Language detection utilities"""

import re
from typing import Literal


class LanguageDetector:
    """Detect language of offer text (English or Ukrainian)"""
    
    # Ukrainian-specific characters and keywords
    UKRAINIAN_CHARS = re.compile(r'[є ї і ґ]', re.IGNORECASE | re.UNICODE)
    UKRAINIAN_KEYWORDS = {
        'продаю', 'продажа', 'пропоную', 'шукаю', 'купую', 'покупаю',
        'пшениця', 'кукурудза', 'ячмінь', 'жито', 'овес',
        'тонні', 'тонна', 'тонн', 'грн', 'гривня', 'гривні',
        'порт', 'ізмаїл', 'одеса', 'чорноморськ',
        'украї' , 'україна', 'українськ',
        'білок', 'вологість', 'кількість', 'ціна', 'доставка',
        'до', 'по', 'з', 'від', 'на', 'у', 'в',
    }
    
    # English-specific keywords
    ENGLISH_KEYWORDS = {
        'sell', 'selling', 'buy', 'buying', 'purchase',
        'wheat', 'corn', 'barley', 'rye', 'oats',
        'tonnes', 'tons', 'ton', 't', 'mt',
        'usd', 'eur', 'price', 'cost', 'rate',
        'port', 'izmail', 'odesa', 'ukraine',
        'protein', 'moisture', 'quality', 'delivery',
        'fob', 'cif', 'ddp', 'exw',
        'find', 'offer', 'amount', 'total',
    }
    
    @staticmethod
    def detect(text: str) -> Literal['en', 'uk']:
        """
        Detect language of text (English or Ukrainian).
        
        Returns:
            'uk' for Ukrainian
            'en' for English
        """
        if not text:
            return 'en'
        
        text_lower = text.lower()
        
        # Check for Ukrainian-specific characters (most reliable)
        if LanguageDetector.UKRAINIAN_CHARS.search(text):
            return 'uk'
        
        # Count keyword matches
        ukrainian_score = sum(1 for kw in LanguageDetector.UKRAINIAN_KEYWORDS if kw in text_lower)
        english_score = sum(1 for kw in LanguageDetector.ENGLISH_KEYWORDS if kw in text_lower)
        
        # If clear pattern, use that
        if ukrainian_score > english_score:
            return 'uk'
        elif english_score > ukrainian_score:
            return 'en'
        
        # Check for Cyrillic characters (Ukrainian/Russian)
        cyrillic_count = len(re.findall(r'[а-яёґєії]', text, re.IGNORECASE | re.UNICODE))
        latin_count = len(re.findall(r'[a-z]', text, re.IGNORECASE))
        
        if cyrillic_count > latin_count:
            return 'uk'
        
        # Default to English
        return 'en'
    
    @staticmethod
    def get_language_hint(language: str) -> str:
        """Get a language-specific hint for prompts"""
        if language == 'uk':
            return "Ukrainian language input detected."
        return "English language input detected."
