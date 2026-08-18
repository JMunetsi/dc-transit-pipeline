"""
transform.py

Reads the most recent raw bus-position JSON from S3, flattens it into
a tabular DataFrame, cleans it (drops incomplete records, standardizes
timestamps, dedupes by vehicle ID), and writes the cleaned table back
to S3 as CSV/Parquet for loading.
"""

import io
import json
import os

import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
S3_RAW_PREFIX = os.environ.get("S3_RAW_PREFIX", "raw/bus-positions/")
S3_CLEAN_PREFIX = os.environ.get("S3_CLEAN_PREFIX", "clean/bus-positions/")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

REQUIRED_FIELDS = ["VehicleID", "Lat", "Lon", "DateTime", "RouteID"]


def get_latest_raw_key(s3) -> str:
    """Find the most recently written raw object under the raw prefix."""
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_RAW_PREFIX)
    objects = response.get("Contents", [])
    if not objects:
        raise FileNotFoundError(f"No raw objects found under {S3_RAW_PREFIX}")
    latest = max(objects, key=lambda obj: obj["LastModified"])
    return latest["Key"]


def load_raw_json(s3, key: str) -> dict:
    obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)
    return json.loads(obj["Body"].read())


def clean_bus_positions(payload: dict) -> pd.DataFrame:
    """Flatten and clean the raw WMATA payload into a tidy DataFrame."""
    records = payload.get("BusPositions", [])
    df = pd.DataFrame(records)

    # Drop records missing any required field
    df = df.dropna(subset=[f for f in REQUIRED_FIELDS if f in df.columns])

    # Standardize timestamp
    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
        df = df.dropna(subset=["DateTime"])

    # Dedupe on vehicle ID, keep latest observation
    if "VehicleID" in df.columns:
        df = df.sort_values("DateTime").drop_duplicates(subset="VehicleID", keep="last")

    return df.reset_index(drop=True)


def upload_clean_to_s3(s3, df: pd.DataFrame, source_key: str) -> str:
    """Write the cleaned DataFrame back to S3 as CSV, mirroring the raw key's timestamp."""
    filename = source_key.split("/")[-1].replace(".json", ".csv")
    key = f"{S3_CLEAN_PREFIX}{filename}"

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=buffer.getvalue())
    return key


def main():
    s3 = boto3.client("s3", region_name=AWS_REGION)
    raw_key = get_latest_raw_key(s3)
    payload = load_raw_json(s3, raw_key)
    df = clean_bus_positions(payload)
    clean_key = upload_clean_to_s3(s3, df, raw_key)
    print(f"Cleaned {len(df)} records -> s3://{S3_BUCKET_NAME}/{clean_key}")


if __name__ == "__main__":
    main()
