# DC Transit Data Pipeline

An automated ETL pipeline that ingests real-time WMATA (DC Metro/Bus) data, lands it in S3, transforms it, and loads it into a queryable warehouse — scheduled to run on its own via AWS Lambda.

## Why this project

My earlier projects (DC Scenicness Prediction, Neighborhood Walkability Index) focused on analysis over static datasets. This one is different: it's a **pipeline**, not a notebook — it pulls live data on a schedule, moves it through raw → clean → queryable stages, and runs unattended in the cloud.

## Architecture

```
WMATA API  →  ingest.py  →  S3 (raw)  →  transform.py  →  S3/local (clean)  →  load.py  →  Warehouse
                                                                                              (SQLite / BigQuery)
     ▲
     │
 Lambda + EventBridge (scheduled trigger, e.g. every 15 min)
```

1. **Ingest** (`src/ingest.py`) — pulls live bus/rail position data from the WMATA API, writes raw JSON to S3 with a timestamped key
2. **Transform** (`src/transform.py`) — reads raw JSON from S3, flattens and cleans it into a tabular format with Pandas (handles missing fields, standardizes timestamps, dedupes)
3. **Load** (`src/load.py`) — loads the cleaned data into a warehouse table (SQLite locally, or BigQuery in the cloud)
4. **Schedule** (`src/lambda_handler.py`) — wraps the ingest→transform→load flow as a single Lambda entry point, triggered on a schedule by EventBridge

## Tech Stack

Python · Pandas · AWS (S3, Lambda, EventBridge) · SQLite / BigQuery · WMATA API

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your WMATA API key and AWS config
python src/ingest.py       # pull latest data → S3
python src/transform.py    # clean → tabular
python src/load.py         # load into warehouse
```

To get a free WMATA API key: https://developer.wmata.com

## Deploying the schedule

Package `src/lambda_handler.py` and dependencies into a Lambda function, then attach an EventBridge rule (e.g. `rate(15 minutes)`) to trigger it automatically. See `sql/schema.sql` for the target table schema.

## Status

🚧 In progress — ingest and transform stages are functional locally; Lambda scheduling is the current focus.
