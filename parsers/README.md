OpenAI-powered message extraction
---------------------------------

This module adds an OpenAI-based extractor that turns Telegram posts/messages about commodity offers into structured objects ready for DB loading.

Setup
- Add an `.env` file in `parsers/` with:
	- `OPENAI_API_KEY=sk-...`
	- optional: `OPENAI_MODEL=gpt-4o-mini`
	- optional: `OPENAI_BASE_URL=...` (if using Azure/OpenRouter/other gateway)

Install deps (Poetry):
- Run inside `parsers/` env.

Usage
- Place input JSON with key `message` per item, e.g. `results/Zernovaya_Birzha_messages_*.json`.
- Run the extractor script to produce `results/processed_messages_openai.json`.

Notes
- Output includes `category_id` mapped to backend categories when possible.
- No DB writes are performed here; integrate with your loader after reviewing output.


File upload/download API for items
----------------------------------
Endpoints (service in `parsers/parsers/api.py`):
- POST `/items/upload/` accepts `.csv`, `.xls`, `.xlsx` via multipart form field `file`. Returns parsed items as JSON.
- GET `/items/download/?format=csv|xls` returns a sample file.
- GET `/health/` health check.

Run locally
- Ensure env is set up (Poetry or venv) and deps installed.
- Start server:
	- python -m uvicorn parsers.api:app --reload --port 8077
- Open http://localhost:8077/docs

Sample files
- `parsers/results/sample_items.csv`
- `parsers/results/sample_items.xls`
- Template: `parsers/results/items_template.xls` (headers + example row)
- Regenerate: `python parsers/results/generate_samples.py`

