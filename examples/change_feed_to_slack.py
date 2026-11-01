"""Daily new bids + status changes (e.g. open -> awarded) -> Slack, never repeating. Env: APIFY_TOKEN, SLACK_WEBHOOK_URL."""
import os, requests
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("opendatafrontierlab/permits-bids-change-feed").call(run_input={
    "changeTypes": ["new", "status"],
    "kinds": ["bid"],
    "keywords": ["roof", "hvac", "network", "cabling"],
    "since": "lastRun",          # continue after the last change the previous run delivered
    "cursorName": "bids-slack",  # one cursor per pipeline; keep the input fixed between runs
    "maxItems": 200,
})
icons = {"new": "🆕", "status": "🔁", "updated": "✏️", "removed": "🗑️"}
for ch in client.dataset(run.default_dataset_id).iterate_items():
    link = (ch.get("record") or {}).get("links", {}).get("record", "")
    requests.post(os.environ["SLACK_WEBHOOK_URL"],
                  json={"text": f"{icons.get(ch['changeType'], '•')} {ch['changeSummary']}\n{link}"})
