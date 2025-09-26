import re
import spacy
from typing import Dict, Optional
import json


class MessageExtractor:
    def __init__(self):
        # Load Ukrainian language model
        self.nlp = spacy.load("uk_core_news_lg")

        # Compile regex patterns
        self.patterns = {
            "phone": r"(?:\+?\d{1,3})?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
            "amount": r"(\d+(?:[\.,]\d+)?)\s*(?:т(?:он)?н?|t)",
            "price": r"(\d+(?:[\.,]\d+)?)\s*(?:грн|UAH|₴)",
            "protein": r"(\d+(?:\.\d+)?)\s*%\s*(?:білк(?:а|у)|прот(?:еїн)?)",
        }

        # Define categories mapping (can be expanded)
        self.categories = {
            "пшениц": "Wheat",
            "соняшник": "Sunflower",
            "кукурудз": "Corn",
            "соя": "Soy",
            "ячмін": "Barley",
            "горох": "Peas",
            "рапс": "Rapeseed",
            "льон": "Flax",
            "жито": "Rye",
            "овес": "Oats",
        }

    def _extract_with_regex(self, text: str, pattern: str) -> Optional[str]:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    def _clean_price(self, price_str: Optional[str]) -> Optional[float]:
        if not price_str:
            return None
        # Extract just the number from price string
        number = re.search(r"\d+(?:[\.,]\d+)?", price_str)
        return float(number.group(0).replace(",", ".")) if number else None

    def _extract_category(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for key, value in self.categories.items():
            if key in text_lower:
                return value
        return None

    def _extract_region(self, text: str) -> Optional[str]:
        # Simple region extraction based on common patterns
        regions = {
            "одес": "Одеська обл.",
            "київ": "Київська обл.",
            "харків": "Харківська обл.",
            # Add more regions as needed
        }

        text_lower = text.lower()
        for key, value in regions.items():
            if key in text_lower:
                return value
        return None

    def extract_info(self, message: str) -> Dict[str, Optional[str]]:
        """
        Extract structured information from a message
        """
        result = {
            "country": "Ukraine",  # Default value
            "region": self._extract_region(message),
            "category": self._extract_category(message),
            "amount": None,
            "price": None,
            "currency": "UAH",  # Default value
            "description": None,
            "phone": None,
        }

        # Process text with spaCy for better entity recognition
        doc = self.nlp(message)

        # Extract numeric values using regex
        amount_match = self._extract_with_regex(message, self.patterns["amount"])
        if amount_match:
            number_match = re.search(r"\d+(?:[\.,]\d+)?", amount_match)
            if number_match:
                try:
                    result["amount"] = str(
                        float(number_match.group(0).replace(",", "."))
                    )
                except ValueError:
                    pass

        price_str = self._extract_with_regex(message, self.patterns["price"])
        price_value = self._clean_price(price_str)
        if price_value is not None:
            result["price"] = str(price_value)

        # Extract phone numbers
        phone = self._extract_with_regex(message, self.patterns["phone"])
        if phone:
            # Clean up phone number format
            phone = re.sub(r"[^\d+]", "", phone)
            if not phone.startswith("+"):
                phone = "+" + phone
            result["phone"] = phone

        # Extract description elements
        description_elements = []

        # Add protein content if found
        protein_match = self._extract_with_regex(message, self.patterns["protein"])
        if protein_match:
            description_elements.append(protein_match)

        # Look for quality indicators like "Ф1", "1кл", etc.
        quality_match = re.search(r"(?:Ф|клас|кл\.)\s*\d+", message)
        if quality_match:
            description_elements.append(quality_match.group(0))

        # Use spaCy for additional quality-related terms
        quality_terms = []
        for token in doc:
            if token.text.lower() in ["високий", "якісний", "чистий", "сухий"]:
                quality_terms.append(token.text)
        if quality_terms:
            description_elements.extend(quality_terms)

        if description_elements:
            result["description"] = ", ".join(description_elements)

        return result


# Example usage
def process_messages(input_file: str, output_file: str):
    extractor = MessageExtractor()

    with open(input_file, "r", encoding="utf-8") as f:
        messages = json.load(f)

    processed_messages = []
    for msg in messages:
        extracted_info = extractor.extract_info(msg["message"])
        processed_messages.append(
            {"original_message": msg["message"], "extracted_info": extracted_info}
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_messages, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    input_file = "parsers/results/zernou_messages_20250926_104355.json"
    output_file = "parsers/results/zernou_processed_messages.json"
    process_messages(input_file, output_file)
