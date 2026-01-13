# Parser Configuration System - Visual Guide

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA PIPELINE SYSTEM                        │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ INPUT: User/API Request                                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST /data-sources                    POST /ingestion/start   │
│  {                                     {                       │
│    "name": "APK-Inform",              "data_source_id": 1,    │
│    "config": {                        "layer": "bronze"       │
│      "parser_type": "apk_inform",   }                         │
│      "regions": ["Odesa"]                                      │
│    }                                                           │
│  }                                                             │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ DATABASE: DataSource Table                                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  id  │ name        │ source_type  │ config (JSON)             │
│ ─────┼─────────────┼──────────────┼─────────────────────      │
│  1   │ APK-Inform  │ web_scraping │ {                        │
│      │             │              │   "parser_type": ...     │
│      │             │              │   "regions": [...]       │
│      │             │              │ }                        │
│  2   │ YFinance    │ api          │ {                        │
│      │             │              │   "parser_type": ...     │
│      │             │              │   "tickers": [...]       │
│      │             │              │ }                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ VALIDATION: ConfigValidator                                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Check required fields exist                                │
│  2. Type-check field values                                    │
│  3. Parser-specific validation                                │
│                                                                 │
│  IF ERROR:                                                     │
│  ┌──────────────────────────────────┐                         │
│  │ Return validation errors         │                         │
│  │ HTTP 400: Invalid Config         │                         │
│  └──────────────────────────────────┘                         │
│                                                                 │
│  IF VALID: Continue...                                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ FACTORY: ParserFactory.create_parser()                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Extract parser_type from config                           │
│  2. Look up in PARSER_REGISTRY                                │
│  3. Instantiate with config parameters                        │
│                                                                 │
│  REGISTRY:                                                    │
│  ┌──────────────────────────────────┐                         │
│  │ "apk_inform" → APKInformParser   │                         │
│  │ "yfinance" → YFinanceParser      │                         │
│  │ "investing_com" → InvestingCom   │                         │
│  │ "tripoli_land" → TripoliLand     │                         │
│  └──────────────────────────────────┘                         │
│                                                                 │
│  Returns: Parser instance ready to execute                    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ EXECUTION: parser.parse()                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Parser-specific execution:                                    │
│  ┌──────────────────────────────────┐                         │
│  │ APKInformParser(regions=[...])   │                         │
│  │  ├─ Fetch from website           │                         │
│  │  ├─ Parse HTML/data              │                         │
│  │  └─ Return DataFrame             │                         │
│  ├──────────────────────────────────┤                         │
│  │ YFinanceParser(tickers=[...])    │                         │
│  │  ├─ Fetch from API               │                         │
│  │  ├─ Transform data               │                         │
│  │  └─ Return DataFrame             │                         │
│  ├──────────────────────────────────┤                         │
│  │ Other parsers...                 │                         │
│  └──────────────────────────────────┘                         │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ STORAGE: Save to Bronze Layer                                  │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DataFrame → Spark → Delta Lake (Bronze)                      │
│                                                                 │
│  /data/delta/bronze/apk_inform_raw/                           │
│  ├─ part-000.parquet                                          │
│  ├─ part-001.parquet                                          │
│  ├─ _delta_log/                                               │
│  └─ ...                                                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ LOGGING: Update IngestionLog                                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Record execution details:                                     │
│                                                                 │
│  ┌────────────────────────────────────┐                        │
│  │ job_id: job_a1b2c3d4e5f6          │                        │
│  │ status: completed                  │                        │
│  │ records_read: 150                  │                        │
│  │ records_written: 150               │                        │
│  │ started_at: 2024-01-12 10:30:00   │                        │
│  │ completed_at: 2024-01-12 10:35:00 │                        │
│  │ output_path: /data/delta/bronze/.. │                        │
│  └────────────────────────────────────┘                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ OUTPUT: User gets job_id immediately (async)                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HTTP 202 Accepted                                            │
│  {                                                             │
│    "job_id": "job_a1b2c3d4e5f6",                             │
│    "status": "started",                                        │
│    "data_source_id": 1,                                        │
│    "layer": "bronze"                                           │
│  }                                                             │
│                                                                 │
│  User can check status:                                        │
│  GET /ingestion/jobs/job_a1b2c3d4e5f6                         │
│                                                                 │
│  Returns updated status as job progresses:                     │
│  ├─ started       (immediately)                                │
│  ├─ running       (seconds later)                              │
│  └─ completed     (minutes later)                              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
                    ┌──────────────────┐
                    │   User/API       │
                    └────────┬─────────┘
                             │
                             │ Register DataSource
                             │ with config
                             ↓
                    ┌──────────────────────┐
                    │  data_sources table  │
                    │  ├─ id               │
                    │  ├─ name             │
                    │  └─ config (JSON)    │
                    └────────┬─────────────┘
                             │
                             │ Trigger ingestion
                             │ Request parser data
                             ↓
                    ┌──────────────────────┐
                    │ ConfigValidator      │
                    │ Validate config      │
                    └────────┬─────────────┘
                             │
                    ┌────────┴────────┐
                    ↓                 ↓
            ✓ Valid            ✗ Invalid
              │                   │
              ↓                   ↓
        ParserFactory    Return Error 400
        Create parser
              │
              ↓
        ┌──────────────────┐
        │   Parser Class   │
        │   └─ parse()     │
        └────────┬─────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │   Fetch Data         │
        │   ├─ Website/API     │
        │   ├─ File            │
        │   └─ Database        │
        └────────┬─────────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │   Transform Data     │
        │   ├─ Clean           │
        │   ├─ Normalize       │
        │   └─ Validate        │
        └────────┬─────────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │   Return DataFrame   │
        └────────┬─────────────┘
                 │
                 ↓
        ┌──────────────────────────┐
        │   Storage Layer          │
        │   ├─ Bronze (raw)        │
        │   ├─ Silver (cleaned)    │
        │   └─ Gold (analytics)    │
        └────────┬─────────────────┘
                 │
                 ↓
        ┌──────────────────────────┐
        │   ingestion_logs table   │
        │   ├─ job_id              │
        │   ├─ status              │
        │   ├─ records_read        │
        │   ├─ records_written     │
        │   ├─ error_message       │
        │   └─ timestamps          │
        └────────┬─────────────────┘
                 │
                 ↓
        ┌──────────────────────┐
        │   Return to User     │
        │   Job status & logs  │
        └──────────────────────┘
```

---

## Parser Registry Visualization

```
┌────────────────────────────────────────────────────────────┐
│                   PARSER REGISTRY                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ParserFactory.PARSER_REGISTRY = {                        │
│                                                            │
│    "apk_inform": APKInformParser                          │
│    ├─ Required: parser_type                               │
│    ├─ Optional: regions, upload_to_storage               │
│    └─ Example: {"parser_type": "apk_inform", ...}        │
│                                                            │
│    "investing_com": InvestingComParser                    │
│    ├─ Required: parser_type, instruments                 │
│    ├─ Optional: start_date, end_date                     │
│    └─ Example: {"parser_type": "investing_com", ...}     │
│                                                            │
│    "yfinance": YFinanceParser                            │
│    ├─ Required: parser_type, tickers                     │
│    ├─ Optional: period, interval                         │
│    └─ Example: {"parser_type": "yfinance", ...}          │
│                                                            │
│    "tripoli_land": TripoliLandParser                      │
│    ├─ Required: parser_type                               │
│    ├─ Optional: companies, base_url                      │
│    └─ Example: {"parser_type": "tripoli_land", ...}      │
│                                                            │
│    "currency": CurrencyParser                            │
│    ├─ Required: parser_type                               │
│    ├─ Optional: none                                      │
│    └─ Example: {"parser_type": "currency"}               │
│                                                            │
│    "graintradecomua": GraintradeComuaParser              │
│    ├─ Required: parser_type                               │
│    ├─ Optional: regions                                   │
│    └─ Example: {"parser_type": "graintradecomua", ...}   │
│                                                            │
│  }                                                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Configuration Schema Hierarchy

```
DataSource
└── config (JSON)
    ├── parser_type (string) ◄── REQUIRED, identifies parser
    │
    ├─► apk_inform config
    │   ├── regions (list, optional) → ["Odesa", "Mykolaiv"]
    │   ├── upload_to_storage (bool, optional) → true/false
    │   └── storage_type (string, optional) → "hetzner"
    │
    ├─► investing_com config
    │   ├── instruments (list, required) → [{"symbol": "ZWZ"}, ...]
    │   ├── start_date (string, optional) → "2023-01-01"
    │   ├── end_date (string, optional) → "2024-01-12"
    │   └── retry_attempts (int, optional) → 3
    │
    ├─► yfinance config
    │   ├── tickers (list, required) → ["ZWZ=F", "ZCZ=F"]
    │   ├── period (string, optional) → "2y"
    │   ├── interval (string, optional) → "1d"
    │   └── progress (bool, optional) → false
    │
    ├─► tripoli_land config
    │   ├── companies (list, optional) → ["nibulon", "kernel"]
    │   ├── base_url (string, optional) → "https://tripoli.land"
    │   ├── storage_type (string, optional) → "hetzner"
    │   └── output_format (string, optional) → "csv"
    │
    ├─► currency config
    │   └── (no additional fields required)
    │
    └─► graintradecomua config
        ├── regions (list, optional) → ["Odesa"]
        └── commodities (list, optional) → ["wheat"]
```

---

## Request/Response Flow

```
CLIENT REQUEST
    │
    ├─ POST /data-sources
    │  {
    │    "name": "APK-Inform",
    │    "source_type": "web_scraping",
    │    "config": {
    │      "parser_type": "apk_inform",
    │      "regions": ["Odesa"]
    │    }
    │  }
    │
    ↓
DATABASE STORED
    │
    ├─ data_sources.id = 1
    ├─ data_sources.name = "APK-Inform"
    └─ data_sources.config = {"parser_type": "apk_inform", ...}
    │
    ↓
LATER: CLIENT TRIGGERS
    │
    ├─ POST /ingestion/start
    │  {
    │    "data_source_id": 1,
    │    "layer": "bronze"
    │  }
    │
    ↓
SERVER PROCESSES
    │
    ├─ Fetch DataSource.config
    ├─ Validate config
    ├─ Create parser
    ├─ Execute parse()
    ├─ Store results
    ├─ Log job
    │
    ↓
IMMEDIATE RESPONSE (202 Accepted)
    │
    ├─ {
    │    "job_id": "job_a1b2c3d4e5f6",
    │    "status": "started"
    │  }
    │
    ↓
ASYNC PROCESSING (background)
    │
    ├─ job status: started → running → completed
    │
    ↓
LATER: CLIENT CHECKS
    │
    ├─ GET /ingestion/jobs/job_a1b2c3d4e5f6
    │
    ↓
SERVER RETURNS STATUS
    │
    └─ {
         "job_id": "job_a1b2c3d4e5f6",
         "status": "completed",
         "records_read": 150,
         "records_written": 150,
         "output_path": "/data/delta/bronze/..."
       }
```

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   ROUTER LAYER                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ /data-sources        /ingestion/start  /ingestion/jobs  ││
│  │  (POST, GET, PATCH)  (POST)           (GET)            ││
│  └────────────┬──────────────┬──────────────┬──────────────┘│
└───────────────┼──────────────┼──────────────┼────────────────┘
                │              │              │
                ↓              ↓              ↓
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                       │
│  ┌────────────────────────────────────────────────────────┐│
│  │ ConfigValidator      ParserFactory    IngestionService ││
│  │  • Validate config    • Create parser  • Run jobs      ││
│  │  • Type checking      • Registry       • Log results   ││
│  │  • Error messages     • Instantiate                    ││
│  └────────────┬─────────────┬──────────────┬──────────────┘│
└───────────────┼─────────────┼──────────────┼────────────────┘
                │             │              │
                ↓             ↓              ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                               │
│  ┌────────────────────────────────────────────────────────┐│
│  │ DataSource Table     Parser Instances   IngestionLog  ││
│  │  • config field      • APKInformParser  • Status      ││
│  │  • parser_type       • YFinanceParser   • Records     ││
│  │  • parameters        • etc...           • Timestamps  ││
│  └────────────┬─────────────┬──────────────┬──────────────┘│
└───────────────┼─────────────┼──────────────┼────────────────┘
                │             │              │
                ↓             ↓              ↓
┌─────────────────────────────────────────────────────────────┐
│                 EXTERNAL DATA SOURCES                       │
│  ┌────────────────────────────────────────────────────────┐│
│  │ Websites/APIs   →   Parsers   →   Results            ││
│  │ • APK-Inform        (fetch)       • DataFrames       ││
│  │ • Investing.com     (parse)       • CSVs             ││
│  │ • Yahoo Finance     (transform)   • Parquet files    ││
│  │ • Tripoli Land      (validate)    • Database records ││
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## State Machine: Job Lifecycle

```
┌──────────────┐
│   NEW JOB    │
└──────┬───────┘
       │ POST /ingestion/start
       ↓
┌──────────────┐
│   STARTED    │  ←─── Job created, validation begins
└──────┬───────┘
       │ Validation
       ├─────────────┬─────────────┐
       │             │             │
       ↓ VALID   ✗ INVALID    TIMEOUT
┌──────────────┐  │         (15 min)
│   RUNNING    │  │             │
└──────┬───────┘  │             │
       │          │             ↓
       │ Process  │        ┌──────────────┐
       │          │        │   FAILED     │
       │          │        └──────────────┘
       ↓          │
    COMPLETE      ↓
       │      ┌──────────────┐
       │      │   FAILED     │
       │      └──────────────┘
       │      (Validation or
       │       Execution Error)
       │
       ↓
┌──────────────────┐
│   COMPLETED      │  ←─── Final state, results saved
└──────────────────┘

Transitions:
  STARTED    → RUNNING    (validation passed)
  RUNNING    → COMPLETED  (success)
  RUNNING    → FAILED     (error)
  STARTED    → FAILED     (invalid config)
```

---

## Configuration Decision Tree

```
I want to add a data source
        │
        ↓
┌───────────────────────┐
│ Choose parser type    │
├───────────────────────┤
│                       │
├─ apk_inform?          
│  └─ Need regions?    
│     Yes → ["Odesa", ...]
│     No → []
│  └─ Need S3 upload?
│     Yes → upload_to_storage: true
│     No → {}
│
├─ investing_com?
│  └─ Need instruments
│     Required! → [{"symbol": "ZWZ"}]
│  └─ Need date range?
│     Yes → start_date, end_date
│     No → {}
│
├─ yfinance?
│  └─ Need tickers
│     Required! → ["ZWZ=F", "ZCZ=F"]
│  └─ Need period?
│     Yes → period: "2y"
│     No → use default "2y"
│
├─ tripoli_land?
│  └─ Need companies?
│     Yes → companies: ["nibulon"]
│     No → []
│
├─ currency?
│  └─ No additional params needed
│
└─ graintradecomua?
   └─ Need regions?
      Yes → regions: ["Odesa"]
      No → []
        │
        ↓
Build config object
        │
        ↓
POST /data-sources with config
        │
        ↓
Config validated ✓
        │
        ↓
DataSource created ✓
        │
        ↓
Ready to ingest!
```

---

## Success Criteria Checklist

```
┌─────────────────────────────────────────────────────────────┐
│ PARSER CONFIGURATION SYSTEM SUCCESS CRITERIA                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ✓ Config Stored                                            │
│   └─ Parser parameters saved in DataSource.config         │
│                                                             │
│ ✓ Config Validated                                         │
│   └─ ConfigValidator checks required fields               │
│   └─ Type validation works                                │
│   └─ Clear error messages returned                        │
│                                                             │
│ ✓ Parser Instantiated                                      │
│   └─ ParserFactory reads config                           │
│   └─ Correct parser class created                         │
│   └─ Parameters passed correctly                          │
│                                                             │
│ ✓ Parser Executed                                          │
│   └─ parse() method runs                                  │
│   └─ Data returned as DataFrame                           │
│   └─ Error handling works                                 │
│                                                             │
│ ✓ Results Stored                                           │
│   └─ Data saved to bronze/silver/gold layer               │
│   └─ File paths correct                                   │
│   └─ Format preserved                                     │
│                                                             │
│ ✓ Jobs Tracked                                             │
│   └─ IngestionLog records created                         │
│   └─ Status updates correctly                             │
│   └─ Execution time recorded                              │
│                                                             │
│ ✓ API Functional                                           │
│   └─ POST /data-sources works                             │
│   └─ POST /ingestion/start works                          │
│   └─ GET /ingestion/jobs works                            │
│   └─ GET /ingestion/parsers works                         │
│                                                             │
│ ✓ Error Handling                                           │
│   └─ Invalid config caught                                │
│   └─ Parser errors logged                                 │
│   └─ User gets meaningful errors                          │
│                                                             │
│ ✓ Performance                                              │
│   └─ Jobs run asynchronously                              │
│   └─ No timeout issues                                    │
│   └─ Concurrent jobs supported                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

This visual guide should help you understand:
- System architecture and data flow
- How components interact
- Configuration schema structure
- Request/response patterns
- Job lifecycle
- Configuration options
- Success criteria

Refer back to specific diagrams when implementing or troubleshooting!
