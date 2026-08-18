"""
lambda_handler.py

Single entry point for running the full ingest -> transform -> load
pipeline as a scheduled AWS Lambda function. Attach an EventBridge
rule (e.g. rate(15 minutes)) to trigger `handler` automatically.
"""

import ingest
import load
import transform


def handler(event, context):
    ingest.main()
    transform.main()
    load.main()
    return {"statusCode": 200, "body": "Pipeline run complete"}


if __name__ == "__main__":
    handler(None, None)
