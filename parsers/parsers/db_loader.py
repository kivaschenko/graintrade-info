import os
import json
from typing import List, Dict, Any

from dotenv import load_dotenv

from .openai_extractor import extract_offers_with_openai
from .parser_1 import insert_offers_to_db


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _offer_to_db_dict(offer: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure all required fields for DB insert are present
    return {
        "category_id": offer.get("category_id"),
        "offer_type": offer.get("offer_type") or "buy",
        "title": offer.get("title")
        or (
            f"Закупка {offer.get('category_name')}"
            if offer.get("category_name")
            else "Пропозиція"
        ),
        "description": offer.get("description"),
        "price": offer.get("price"),
        "currency": offer.get("currency") or "UAH",
        "amount": offer.get("amount") or 1,
        "measure": offer.get("measure") or "t",
        "terms_delivery": offer.get("terms_delivery") or "exw",
        "location": offer.get("location") or offer.get("region"),
    }


def process_and_insert(input_file: str, dry_run: bool = False) -> List[Dict[str, Any]]:
    with open(input_file, "r", encoding="utf-8") as f:
        messages = json.load(f)

    all_offers: List[Dict[str, Any]] = []
    for msg in messages:
        text = msg["message"] if isinstance(msg, dict) else str(msg)
        result = extract_offers_with_openai(text)
        for o in result.offers:
            all_offers.append(_offer_to_db_dict(o.model_dump()))

    if not dry_run and all_offers:
        insert_offers_to_db(all_offers)
    return all_offers


if __name__ == "__main__":
    in_file = os.getenv(
        "INPUT_FILE",
        os.path.join(
            BASE_DIR, "results", "Zernovaya_Birzha_messages_20250911_193215.json"
        ),
    )
    dry = os.getenv("DRY_RUN", "1") == "1"
    offers = process_and_insert(in_file, dry_run=dry)
    print(f"Prepared {len(offers)} offers. {'Dry run' if dry else 'Inserted into DB.'}")
