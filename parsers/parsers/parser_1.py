import re
import psycopg2
from uuid import uuid4
import spacy
from difflib import get_close_matches
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# --- NLP модель ---
nlp = spacy.load("uk_core_news_sm")

# --- Словник культур ---
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

# --- Регекс ціни ---
PRICE_PATTERN = re.compile(r"(\d{3,6})(?:\s?грн|💵)?", re.IGNORECASE)

# --- Ініціалізація геокодера ---
geolocator = Nominatim(user_agent="grain_parser")


def normalize_crop(text: str):
    """Нормалізує культуру (знаходить близький збіг зі словником)"""
    text = text.lower()
    matches = get_close_matches(text, CATEGORY_MAP.keys(), n=1, cutoff=0.6)
    return matches[0] if matches else None


def geocode_location(location: str):
    """Шукає координати та країну/регіон через Nominatim"""
    try:
        loc = geolocator.geocode(f"{location}, Україна", timeout=10)
        if loc:
            # Додатковий пошук регіону через reverse
            reverse = geolocator.reverse(
                (loc.latitude, loc.longitude), language="uk", timeout=10
            )
            region = None
            country = "Україна"
            if reverse and "address" in reverse.raw:
                addr = reverse.raw["address"]
                region = addr.get("state")
                country = addr.get("country", "Україна")
            return country, region, loc.latitude, loc.longitude
    except GeocoderTimedOut:
        return "Україна", None, 0.0, 0.0
    return "Україна", None, 0.0, 0.0


def extract_offers_nlp(message: str):
    offers = []
    current_location = None

    for line in message.splitlines():
        line = line.strip()
        if not line:
            continue

        # Локація (через spaCy GPE/LOC)
        doc_line = nlp(line)
        for ent in doc_line.ents:
            if ent.label_ in ("GPE", "LOC"):
                current_location = ent.text

        # Культура
        crop = None
        for word in line.split():
            normalized = normalize_crop(word)
            if normalized:
                crop = normalized
                break

        # Ціна
        match = PRICE_PATTERN.search(line)
        if crop and match:
            price = float(match.group(1))
            currency = "UAH" if "грн" in line.lower() else "USD"

            offers.append(
                {
                    "category_id": CATEGORY_MAP[crop],
                    "offer_type": "buy",
                    "title": f"Закупка {crop}",
                    "description": line,
                    "price": price,
                    "currency": currency,
                    "amount": 1,
                    "measure": "t",
                    "terms_delivery": "exw",
                    "location": current_location,
                }
            )

    return offers


def insert_offers_to_db(offers):
    conn = psycopg2.connect(
        dbname="grain", user="grain", password="secret", host="localhost"
    )
    cur = conn.cursor()

    for offer in offers:
        country, region, lat, lon = (
            geocode_location(offer["location"])
            if offer["location"]
            else ("Україна", None, 0.0, 0.0)
        )

        cur.execute(
            """
            INSERT INTO items (
                uuid, category_id, offer_type, title, description, price,
                currency, amount, measure, terms_delivery,
                country, region, latitude, longitude, geom
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            )
        """,
            (
                str(uuid4()),
                offer["category_id"],
                offer["offer_type"],
                offer["title"],
                offer["description"],
                offer["price"],
                offer["currency"],
                offer["amount"],
                offer["measure"],
                offer["terms_delivery"],
                country,
                region,
                lat,
                lon,
                lon,
                lat,
            ),
        )

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    SAMPLE_MESSAGE = """📍 Одесса
    🌾 Пшеница - 8300 грн
    🌻 Кукуруза - 212💵
    📍 Мена Черниговская обл.
    🌾 Горох - 240💵
    🌻 Подсолнух - 21200грн
    """

    offers = extract_offers_nlp(SAMPLE_MESSAGE)
    print("Extracted offers:", offers)
    # insert_offers_to_db(offers)
