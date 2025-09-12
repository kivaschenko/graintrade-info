import os
import json
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
import backoff

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional at import time
    OpenAI = None  # type: ignore

if TYPE_CHECKING:
    from openai import OpenAI as OpenAIType  # type: ignore
else:
    OpenAIType = Any  # fallback for typing


# Load environment variables from parsers/.env if present
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


# Category mapping aligned with backend IDs
CATEGORY_MAP = {
    "пшениця": 1,
    "ячмінь": 2,
    "кукурудза": 3,
    "горох": 4,
    "соя": 5,
    "рапс": 6,
    "соняшник": 7,
    "льон": 8,
}


class Offer(BaseModel):
    category_id: Optional[int] = Field(None, description="Mapped category id for DB")
    category_name: Optional[str] = Field(
        None, description="Raw category name extracted from the text"
    )
    offer_type: Optional[str] = Field(
        None, description="buy or sell; default to buy if unsure"
    )
    title: Optional[str]
    description: Optional[str]
    price: Optional[float]
    currency: Optional[str] = Field(None, description="UAH or USD")
    amount: Optional[float]
    measure: Optional[str] = Field(None, description="t for tonnes")
    terms_delivery: Optional[str] = Field(None, description="exw/fca/cpt/dap etc")
    location: Optional[str] = Field(None, description="City or region")
    country: Optional[str] = Field(None, description="Country name if known")
    region: Optional[str] = Field(None, description="Region/oblast if known")
    phone: Optional[str] = Field(None, description="Contact phone if present")


class ExtractionResult(BaseModel):
    offers: List[Offer]


SYSTEM_PROMPT = (
    "You are an expert data extraction assistant for Ukrainian grain trade messages. "
    "Given a chat message, extract structured offers for commodities in Ukrainian. "
    "Return a concise JSON with fields present in the text; do not invent data. "
    "Infer offer_type (buy/sell) when obvious. currency must be one of UAH or USD. "
    "amount is numeric (tonnes). price is numeric per tonne if possible. "
    "Use 't' as measure for tonnes. Prefer short title like 'Закупка пшениця' or 'Продаж кукурудза'."
)


USER_INSTRUCTIONS = (
    "Extract all offers from the following message. If multiple commodities are listed, "
    "return multiple items in offers. Do not add fields not present. Phone is optional."
)


def _get_client() -> OpenAIType:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")  # optional for Azure/other gateways
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    if OpenAI is None:
        raise RuntimeError(
            "openai package not available. Ensure it's installed in this env."
        )
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _map_category_name_to_id(name: Optional[str]) -> Optional[int]:
    if not name:
        return None
    key = name.strip().lower()
    # simple normalization for common variants
    replacements = {
        "пшеница": "пшениця",
        "ячмень": "ячмінь",
        "кукуруза": "кукурудза",
        "подсолнечник": "соняшник",
        "лен": "льон",
    }
    key = replacements.get(key, key)
    for k in CATEGORY_MAP:
        if k in key or key in k:
            return CATEGORY_MAP[k]
    return CATEGORY_MAP.get(key)


@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def _call_openai(client: OpenAIType, content: str) -> Dict[str, Any]:
    # Prefer JSON mode with a clear schema hint
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{USER_INSTRUCTIONS}\n\nMESSAGE:\n{content}"},
        ],
    )
    txt = response.choices[0].message.content or "{}"
    return json.loads(txt)


def extract_offers_with_openai(message: str) -> ExtractionResult:
    # Try OpenAI first, otherwise fallback to local extractor
    try:
        client = _get_client()
        raw = _call_openai(client, message)
    except Exception:
        # Fallback: use local regex/spaCy extraction for a single offer
        try:
            from .message_extractor import MessageExtractor  # type: ignore
        except Exception:
            # No fallback available
            return ExtractionResult(offers=[])
        extractor = MessageExtractor()
        info = extractor.extract_info(message)
        cat = info.get("category")
        price_val = None
        amt_val = None
        if info.get("price"):
            try:
                price_val = float(str(info.get("price")).replace(",", "."))
            except Exception:
                price_val = None
        if info.get("amount"):
            try:
                amt_val = float(str(info.get("amount")).replace(",", "."))
            except Exception:
                amt_val = None

        offer = Offer(
            category_name=cat if isinstance(cat, str) else None,
            category_id=_map_category_name_to_id(cat if isinstance(cat, str) else None),
            offer_type="buy",  # conservative default
            title=(f"Закупка {cat.lower()}" if isinstance(cat, str) else None),
            description=info.get("description"),
            price=price_val,
            currency=info.get("currency"),
            amount=amt_val,
            measure="t",
            terms_delivery=None,
            location=info.get("region"),
            country=info.get("country"),
            region=info.get("region"),
            phone=info.get("phone"),
        )
        return ExtractionResult(offers=[offer])
    # Ensure required list exists
    offers = raw.get("offers")
    if not isinstance(offers, list):
        offers = []

    # Post-process and validate
    normalized: List[Offer] = []
    for item in offers:
        if not isinstance(item, dict):
            continue
        # map names to IDs
        cat_name = item.get("category_name") or item.get("category")
        if cat_name and not item.get("category_name"):
            item["category_name"] = cat_name
        item["category_id"] = item.get("category_id") or _map_category_name_to_id(
            item.get("category_name")
        )
        # normalize numeric fields
        for fld in ("price", "amount"):
            if fld in item and isinstance(item[fld], str):
                try:
                    item[fld] = float(str(item[fld]).replace(",", "."))
                except ValueError:
                    item[fld] = None
        # defaults
        item.setdefault("currency", None)
        item.setdefault("measure", "t")
        try:
            normalized.append(Offer(**item))
        except ValidationError:
            # Skip invalid offers but continue processing others
            continue

    return ExtractionResult(offers=normalized)


def process_messages_with_openai(input_file: str, output_file: str) -> None:
    with open(input_file, "r", encoding="utf-8") as f:
        messages = json.load(f)

    processed: List[Dict[str, Any]] = []
    for msg in messages:
        text = msg["message"] if isinstance(msg, dict) else str(msg)
        result = extract_offers_with_openai(text)
        processed.append(
            {
                "original_message": text,
                "extracted_offers": [o.model_dump() for o in result.offers],
            }
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Example CLI run
    in_file = os.getenv(
        "INPUT_FILE",
        os.path.join(
            BASE_DIR, "results", "Zernovaya_Birzha_messages_20250911_193215.json"
        ),
    )
    out_file = os.getenv(
        "OUTPUT_FILE",
        os.path.join(BASE_DIR, "results", "processed_messages_openai.json"),
    )
    process_messages_with_openai(in_file, out_file)
