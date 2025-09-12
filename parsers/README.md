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

