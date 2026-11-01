"""Daily new building permits -> Slack. Env: APIFY_TOKEN, SLACK_WEBHOOK_URL. pip install apify-client requests"""
import os, requests
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("opendatafrontierlab/us-building-permits").call(run_input={
    "jurisdictions": ["austin-tx", "seattle-wa", "los-angeles-ca"],
    "daysBack": 3, "keyword": "solar", "onlyNewSinceLastRun": True,
})
for p in client.dataset(run.default_dataset_id).iterate_items():
    text = f"{p['jurisdiction']}: {p['description'][:120]} | {p['address']} | {p.get('contractorBusinessName') or ''}"
    requests.post(os.environ["SLACK_WEBHOOK_URL"], json={"text": text})
