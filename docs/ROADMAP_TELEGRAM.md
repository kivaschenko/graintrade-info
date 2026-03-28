# GrainTrade — Compact Roadmap: Telegram + AI MVP

Goal
- Pivot current project to a low-cost, AI-driven MVP distributed primarily via a Telegram channel/bot: daily/weekly market analytics, short forecasts, and targeted alerts for farmers.

Why
- Lower distribution friction (Telegram widely used by Ukrainian farmers).
- AI adds unique, defensible value (forecasts, automated analysis, personalized alerts).
- Minimizes running infra costs while validating product-market fit quickly.

High-level timeline (12 weeks)
- Week 0 (Ops): Audit running services, snapshot DB/backups, stop non-essential containers to cut costs.
- Weeks 1–2 (POC): Collect historical prices for 2 crops, build simple forecast endpoint (Prophet or lightweight model), and a Telegram bot that posts daily forecasts + short LLM analysis.
- Weeks 3–6 (MVP): Add subscriptions, region-based alerts, caching, basic analytics (CTR, opens, retention). Run 4-week marketing test (invite target audience, partner with local channels).
- Weeks 7–10 (Monetize/Test): Launch small paid pilot (premium alerts / richer forecasts); measure conversion, CAC, retention.
- Weeks 11–12 (Decision): Evaluate KPIs (retention, CTR, willingness-to-pay). Decide: scale, iterate, or conserve/archive.

Core MVP features (priority)
- Daily price forecasts + short auto-generated analysis (LLM summarization).
- Telegram bot/channel for distribution and alerts.
- Region-based subscription alerts (when price crosses threshold or forecast suggests action).
- Basic analytics dashboard (simple counts + engagement metrics).

AI hosting recommendation (quick TCO and path)
- Start: Hosted LLM APIs (OpenAI/Anthropic/etc.) + CPU time-series models (Prophet/N-BEATS small) — lowest time-to-market and ops cost.
- If demand grows: move heavy training/inference to cloud GPUs (rent hourly: Lambda/Paperspace/GCP) or managed vector DBs for retrieval augmentation.
- Self-hosted GPU: viable only if you plan steady heavy inference (many users) and can cover upfront hardware (~€1k–3k for GPU card + parts) + colocation/power (~€50–150+/mo) + ops overhead. For an early-stage MVP, recommended: NO — use hosted/cloud first.

Costs & quick budget notes
- Keep Hetzner AX41 for DB/Redis + static hosting if you want (~€40/mo). Disable unused services to cut to a minimal baseline.
- Hosted LLM usage for small-scale bot can be kept to €50–200/mo depending on volume. Cloud GPU for occasional heavy jobs rentable hourly; self-hosted GPU only if growth justifies TCO.

Success metrics (3 months)
- 3k channel impressions / month and CTR >5% OR 300 engaged users (opens/comments) AND
- 30‑day retention >10% AND
- Willingness-to-pay: >1% of active users convert to paid pilot.

Immediate next actions (doable now)
1. Stop non-essential containers and snapshot DB (reduce monthly bill).
2. Stand up Telegram channel + bot; schedule first 14 daily posts (use hosted LLM for text summaries).
3. Build forecast POC for 2 crops and automate posts.

Contact
- If you want, I can scaffold the Telegram bot and forecast endpoint next (small runnable repo + run commands).

— brief roadmap, keep it lean and executable.
