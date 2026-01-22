# Ukrainian Language Support - Offer Parser

## Overview

The Offer Parser now supports **both English and Ukrainian** languages for parsing agricultural commodity offers. Language detection is automatic or can be explicitly specified.

## 🇺🇦 Ukrainian Features

### 1. **Auto-Detection**

The parser automatically detects the language of your input:

```bash
# English input - automatically detected
POST /parse
{
  "text": "Sell wheat 560 tonnes FOB $234.56/t"
}
# Result: language detected as 'en'

# Ukrainian input - automatically detected
POST /parse
{
  "text": "Продаю пшеницю 560 тонн FOB 234.56 доларів за тонну"
}
# Result: language detected as 'uk'
```

### 2. **Explicit Language Specification**

You can also specify the language explicitly:

```json
{
  "text": "Продаю пшеницю 560 тонн",
  "language": "uk",
  "user_id": "user_123",
  "source": "chat"
}
```

**Language Options:**
- `"auto"` — Auto-detect (default)
- `"en"` — English
- `"uk"` — Ukrainian (Українська)

### 3. **Supported Ukrainian Terms**

#### Intent Keywords (Sell/Buy)
```
Sell: продаю, продажа, пропоную, мають на продаж
Buy: купую, покупаю, шукаю, потребую, знайти
Search: пошук, знайти мені
```

#### Quantity Units (Tonnes)
```
Tonne (singular): тонна, т
Tonne (plural): тонни, тонн
```

#### Crops (Ukrainian Names)
```
Wheat: Пшениця
Corn: Кукурудза
Barley: Ячмінь
Rye: Жито
Oats: Овес
Sunflower: Соняшник
Soybean: Соя
```

#### Locations (Ukrainian Cities/Ports)
```
Izmail: Ізмаїл
Odesa: Одеса
Chornomorsk: Чорноморськ
Mykolaiv: Миколаїв
Kherson: Херсон
```

#### Quality Specs (Ukrainian)
```
Protein: білок
Moisture: вологість
Ash: зола
Fiber: клітковина
Fat: жир
Gluten: глютен
```

#### Currency
```
Hryvnia: грн, гривня, гривні
```

#### Delivery Terms
```
FOB, CIF, DDP (same in both languages)
```

### 4. **Ukrainian Regex Patterns**

The regex parser includes Ukrainian patterns for:

| Pattern | English | Ukrainian |
|---------|---------|-----------|
| **Quantity** | "560 tonnes" | "560 тонн" |
| **Price** | "$234.56 per ton" | "234.56 доларів за тонну" |
| **Intent** | "Sell wheat" | "Продаю пшеницю" |
| **Quality** | "protein 23%" | "білок 23%" |
| **Date** | "until 09/02/2026" | "до 09/02/2026" |

### 5. **LLM Prompt (Bilingual)**

When using LLM parser (OpenAI/Anthropic), the system prompt is bilingual and includes:

```
Supports English and Ukrainian languages.
For OFFER: extract offer_type, crop, quantity, price, location, delivery_terms...
Для ПРОПОЗИЦІЇ: витягти offer_type, crop, quantity, price, location...
```

## 📝 Examples

### Example 1: Ukrainian Wheat Offer

**Input:**
```
Продаю пшеницю 2 клас в Ізмаїлі на FOB 234.56 доларів за тонну 560 т до 09/02/2026 білок мінімум 23%
```

**Parsed Output:**
```json
{
  "success": true,
  "offer": {
    "offer_type": "sell",
    "crop": "Wheat",
    "quantity": 560,
    "quantity_unit": "tonnes",
    "price": 234.56,
    "price_unit": "USD/tonne",
    "location": "Ізмаїл, Україна",
    "delivery_terms": "FOB",
    "expiry_date": "2026-02-09",
    "quality_specs": [{"name": "protein", "min": 23, "unit": "%"}]
  },
  "intent": "create_offer",
  "confidence": 0.95,
  "parsing_method": "regex"
}
```

### Example 2: Ukrainian Search Query

**Input:**
```
Шукаю пропозиції кукурудзи в Черкаській області України включаючи вартість доставки DDP не більше 8600 гривні за тонну 200 т до 02/02/2026
```

**Parsed Output:**
```json
{
  "success": true,
  "search_query": {
    "crop": "Corn",
    "offer_type": "sell",
    "max_quantity": 200,
    "max_price": 8600,
    "price_currency": "UAH",
    "location": "Черкаська область, Україна",
    "delivery_terms": ["DDP"],
    "include_delivery_cost": true,
    "expiry_by": "2026-02-02"
  },
  "intent": "search",
  "confidence": 0.92
}
```

### Example 3: Mixed Language Input

**Input:**
```
Sell пшеницю in Ізмаїлі 560 т FOB 234.56 USD за тонну
```

**Detection & Parsing:**
- Language: Ukrainian (detected by special chars і, ї)
- Parsed successfully
- Confidence: 0.85+

## 🔧 API Usage

### Endpoint: `/parse`

**Request with Language Specification:**

```bash
curl -X POST http://localhost:8005/parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Продаю пшеницю 560 тонн FOB 234.56 доларів за тонну",
    "user_id": "user_123",
    "source": "chat",
    "language": "uk"
  }'
```

**Request with Auto-Detection:**

```bash
curl -X POST http://localhost:8005/parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Продаю пшеницю 560 тонн FOB 234.56 доларів за тонну",
    "user_id": "user_123",
    "source": "chat",
    "language": "auto"
  }'
```

## 🧪 Testing Ukrainian Support

### Run Tests

```bash
pytest tests/test_parsers.py::TestLanguageDetector -v
pytest tests/test_parsers.py::TestRegexParser::test_parse_ukrainian_offer -v
```

### Manual Testing

Use the interactive API docs:

```
http://localhost:8005/docs
```

Try these inputs:

**English:**
```
Sell wheat 560 tonnes FOB $234/t in Izmail
```

**Ukrainian:**
```
Продаю пшеницю 560 тонн FOB 234 доларів у Ізмаїлі
```

## 📊 Language Detection Logic

The `LanguageDetector` class uses this priority:

1. **Ukrainian Special Characters** (highest priority)
   - Detects: є, ї, і, ґ
   - Reliable indicator of Ukrainian text

2. **Keyword Matching** (second priority)
   - Counts Ukrainian/English keywords
   - Threshold-based detection

3. **Character Distribution** (third priority)
   - Cyrillic vs Latin character count
   - Falls back to English if unclear

**Example:**
```python
from app.utils.language_detector import LanguageDetector

# Auto-detect
lang = LanguageDetector.detect("Продаю пшеницю")  # Returns 'uk'
lang = LanguageDetector.detect("Sell wheat")       # Returns 'en'
```

## 🌐 Integration Notes

### For Backend Developers

When integrating with your chat service:

```python
@router.post("/create-from-text")
async def create_offer_from_text(text: str, user_id: str):
    """Accept offer text in Ukrainian or English"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://offer-parser:8005/parse",
            json={
                "text": text,
                "user_id": user_id,
                "source": "chat",
                "language": "auto"  # Let parser detect language
            }
        )
    
    parsed = response.json()
    if parsed.get("success"):
        # Language auto-detected and offer parsed
        offer = parsed.get("offer")
        # Store offer in database
    
    return parsed
```

### User Communication

Users can now write offers naturally in their preferred language:

- **English speakers:** "Sell wheat 560t FOB $234/t"
- **Ukrainian speakers:** "Продаю пшеницю 560 т FOB 234 доларів за т"
- **Mixed:** "Sell пшеницю 560 т FOB доларів"

The parser will handle all variants automatically.

## 🐛 Troubleshooting

### Issue: Ukrainian text not detected

**Solution:** Ensure text contains Ukrainian-specific characters (є, ї, і) or Ukrainian keywords.

```python
# Good: Contains Ukrainian char 'і'
text = "Продаю пшеницю в Ізмаїлі"  # ✓ Detected as UK

# Less reliable: Only Cyrillic without special chars
text = "Prodaju pshenicu"  # May detect as EN
```

### Issue: Low confidence on Ukrainian text

**Solution:** Use explicit `language: "uk"` parameter or switch to OpenAI parser for better accuracy.

```json
{
  "text": "Продаю пшеницю...",
  "language": "uk",
  "user_id": "user_123"
}
```

### Issue: Mixed language not detected correctly

**Solution:** Ukrainian special characters take priority. If mixing, ensure Ukrainian text dominates or use explicit `language` parameter.

## 📚 Further Reading

- [LanguageDetector Code](app/utils/language_detector.py)
- [Ukrainian Regex Patterns](app/parsers/regex_parser.py) (lines 23-52)
- [Ukrainian Domain Vocabulary](app/services/domain_service.py)
- [Tests](tests/test_parsers.py)

## 🔄 Future Enhancements

Planned Ukrainian language improvements:

- [ ] Transliteration support (Cyrillic to Latin)
- [ ] Regional dialect support (Eastern vs Western Ukrainian)
- [ ] Russian language support (shares Cyrillic but different patterns)
- [ ] Machine learning-based language detection (more accurate for edge cases)
- [ ] Ukrainian-specific date format handling (e.g., "19 січня 2026")

## 📞 Support

For Ukrainian language issues:

1. Check text contains Ukrainian characters or keywords
2. Review logs: `LOG_LEVEL=debug`
3. Test with explicit `language: "uk"` parameter
4. Try OpenAI parser for higher accuracy: `LLM_PROVIDER=openai`

---

**Status:** ✅ Production-ready  
**Languages Supported:** English, Ukrainian  
**Auto-Detection:** Yes  
**Version:** 1.0.0 with Ukrainian support
