"""
load.py

Loads the most recently cleaned bus-position CSV from S3 into a
warehouse table (SQLite by default — swap for BigQuery in production
by replacing the `load_to_sqlite` call with a `pandas_gbq.to_gbq` call).
"""

import io
import os
import sqlite3

import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
S3_CLEAN_PREFIX = os.environ.get("S3_CLEAN_PREFIX", "clean/bus-positions/")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DB_PATH = os.environ.get("DB_PATH", "data/transit.db")

TABLE_NAME = "bus_positions"


def get_latest_clean_key(s3) -> str:
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_CLEAN_PREFIX)
    objects = response.get("Contents", [])
    if not objects:
        raise FileNotFoundError(f"No clean objects found under {S3_CLEAN_PREFIX}")
    latest = max(objects, key=lambda obj: obj["LastModified"])
    return latest["Key"]


def load_clean_csv(s3, key: str) -> pd.DataFrame:
    obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)
    return pd.read_csv(io.BytesIO(obj["Body"].read()))


def load_to_sqlite(df: pd.DataFrame, db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
    conn.close()


def main():
    s3 = boto3.client("s3", region_name=AWS_REGION)
    clean_key = get_latest_clean_key(s3)
    df = load_clean_csv(s3, clean_key)
    load_to_sqlite(df, DB_PATH)
    print(f"Loaded {len(df)} records into {DB_PATH} ({TABLE_NAME})")


if __name__ == "__main__":
    main()
