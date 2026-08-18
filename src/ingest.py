"""
ingest.py

Pulls live bus position data from the WMATA API and lands it
unmodified (raw) in S3, keyed by timestamp. This is the "extract"
and first-half of "load" in the pipeline — raw data is never
transformed here, only captured as-is for reproducibility.
"""

import json
import os
from datetime import datetime, timezone

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

WMATA_API_KEY = os.environ["WMATA_API_KEY"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
S3_RAW_PREFIX = os.environ.get("S3_RAW_PREFIX", "raw/bus-positions/")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

WMATA_BUS_POSITIONS_URL = "https://api.wmata.com/Bus.svc/json/jBusPositions"


def fetch_bus_positions() -> dict:
    """Call the WMATA API and return the raw JSON response."""
    headers = {"api_key": WMATA_API_KEY}
    response = requests.get(WMATA_BUS_POSITIONS_URL, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def upload_raw_to_s3(payload: dict) -> str:
    """Upload the raw payload to S3 with a timestamped key. Returns the S3 key."""
    s3 = boto3.client("s3", region_name=AWS_REGION)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    key = f"{S3_RAW_PREFIX}{timestamp}.json"

    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=json.dumps(payload),
        ContentType="application/json",
    )
    return key


def main():
    payload = fetch_bus_positions()
    key = upload_raw_to_s3(payload)
    n_records = len(payload.get("BusPositions", []))
    print(f"Ingested {n_records} bus position records -> s3://{S3_BUCKET_NAME}/{key}")


if __name__ == "__main__":
    main()
