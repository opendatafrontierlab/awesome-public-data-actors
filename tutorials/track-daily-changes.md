# Track daily changes in building permits and public bids (new records, awards, closings)

Most public-data feeds give you a **snapshot**: every permit or bid that exists today. What you usually want is the **delta**: which permits were issued since yesterday, which bids just moved from *forecast* to *open*, which ones were *awarded*, and which deadlines moved. Rebuilding that delta yourself means downloading everything daily, storing yesterday's copy, matching records whose IDs shift, and filtering out noise (whitespace edits, re-geocoded coordinates, publishers who re-key their data overnight).

This tutorial uses the [Permits & Bids Change Feed](https://apify.com/opendatafrontierlab/permits-bids-change-feed) Actor, which does that diffing once a day across **20 official open-data feeds** (12 building-permit portals in the US and Canada, plus 8 public-bid and grant sources such as NYC City Record, LA RAMP, Delaware, E-Rate Form 470 and Grants.gov). Each change comes with its **before and after values**.

**What you'll build:** a daily job that sends only new bids and status changes matching your keywords to Slack or a Google Sheet, and never sends the same change twice.

**Cost:** you pay per change delivered: $0.004 per new record or update, $0.006 per status change, plus $0.001 per run. A keyword-filtered daily feed usually costs cents per day.

> **Archive start: 2026-10-29.** Changes are recorded from that date on. You can't request earlier dates, so the history is short today and grows every day.

---

## 1. What a "change" looks like

Every row has a `changeType`:

| `changeType` | Meaning |
|---|---|
| `new` | The record appeared in the publisher's feed for the first time |
| `status` | The normalized status moved, e.g. `forecast → open`, `open → awarded`, `issued → closed` |
| `updated` | A material field changed: dates, amount, title, description, business name or documents |
| `removed` | The publisher deleted it (confirmed by a direct lookup, after 2 missed collections) |
| `expired` | A bid's deadline passed (free, off by default) |

Example row (shape only; values are illustrative):

```json
{
  "changeId": "2026-11-02:bid:grants-gov:NSF-26-512:status",
  "changeType": "status",
  "changedOn": "2026-11-02",
  "changeSummary": "Status forecast -> open: Facilitating Research at Primarily Undergraduate Institutions (Grants.gov)",
  "changedFields": ["status", "statusNorm"],
  "before": {"status": "forecasted", "statusNorm": "forecast"},
  "after":  {"status": "posted",     "statusNorm": "open"},
  "kind": "bid",
  "sourceKey": "grants-gov",
  "record": {"title": "…", "statusNorm": "open", "dates": {"posted": "2026-11-02", "due": "2027-01-15"},
             "links": {"record": "https://www.grants.gov/search-results-detail/…"},
             "license": "Public domain U.S. Government work"}
}
```

Permits and bids share one record shape (`title`, `description`, `status`, `statusNorm`, `dates`, `money`, `businessName`, `org`, `location`, `links`, `documents`, `license`, `attribution`), so one downstream mapping covers both.

### Why not just diff the raw feeds yourself?
A few things the feed handles that a naive `diff` won't:
- **Stable keys.** Records are matched on the publisher's own permit or notice number, never on row order. Rows a publisher splits per address or line (San Francisco, Cincinnati, E-Rate documents) are merged first.
- **Material fields only.** Changes in letter case, whitespace, number formatting or coordinates are ignored.
- **Status normalization.** "Signed-off", "Finaled" and "Completed" all map to `closed`. A wording change that keeps the same normalized status is an `updated`, not a billed status change.
- **Broken-source guard.** If a portal returns nothing, loses half its rows, changes its schema, or re-keys its data overnight, that day's removals and mass changes are suppressed and flagged in a free `SOURCE_STATUS` record, instead of flooding you with thousands of fake changes.

## 2. Run it once

Open the [Actor page](https://apify.com/opendatafrontierlab/permits-bids-change-feed), click **Try for free**, and use this input:

```json
{
  "changeTypes": ["new", "status"],
  "kinds": ["bid"],
  "keywords": ["roof", "hvac", "network", "cabling"],
  "since": "lastRun",
  "maxItems": 200,
  "cursorName": "bids-slack"
}
```

- `kinds`: `permit`, `bid`, or leave empty for both.
- `sources`: optional list such as `["nyc-city-record", "erate-form-470", "grants-gov"]`.
- `states`: two-letter codes such as `["NY", "CA"]`.
- `minAmount` with `amountCurrency` (`USD` or `CAD`): keep only bigger jobs. Calgary and Edmonton amounts are in CAD and are never converted.

The **first** run returns the last 7 days of changes (or everything since the archive start, if that's shorter).

## 3. Make it a daily feed that never repeats

The key setting is `"since": "lastRun"`. The Actor stores a cursor per filter set plus `cursorName`, so each run starts right after the last change the previous run delivered. If a run stops at `maxItems` or at your maximum charge, the next run picks up from the first undelivered change, and nothing is charged twice.

1. On the Actor page, click **Save as a new task** with the input above.
2. Open **Schedules → Create schedule** and run the task daily at around **12:00 ET**. The daily collection starts at 10:30 ET and usually finishes within about 20 minutes.

Two rules to remember:
- **Keep the input fixed** for a scheduled task. Changing any filter starts a new cursor, which re-delivers (and re-bills) the last 7 days.
- **Use a different `cursorName` per pipeline** (e.g. `bids-slack` and `permits-sheet`), so they don't share a position.

## 4. Send the changes somewhere useful

**Slack via Python:**

```python
import os, requests
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("opendatafrontierlab/permits-bids-change-feed").call(run_input={
    "changeTypes": ["new", "status"],
    "kinds": ["bid"],
    "keywords": ["roof", "hvac", "network", "cabling"],
    "since": "lastRun",
    "cursorName": "bids-slack",
    "maxItems": 200,
})
for ch in client.dataset(run.default_dataset_id).iterate_items():
    link = (ch.get("record") or {}).get("links", {}).get("record", "")
    icon = {"new": "🆕", "status": "🔁", "updated": "✏️", "removed": "🗑️"}.get(ch["changeType"], "•")
    requests.post(os.environ["SLACK_WEBHOOK_URL"], json={"text": f"{icon} {ch['changeSummary']}\n{link}"})
```

**Google Sheets / Make / Zapier / n8n:** trigger on *Apify: Finished task run*, fetch the dataset items, and map `changeType`, `changedOn`, `changeSummary`, `record.title`, `record.dates.due` and `record.links.record` to columns.

**AI agents:** connect the [Apify MCP server](https://mcp.apify.com) and add `opendatafrontierlab/permits-bids-change-feed`. Then ask, for example, *"Which E-Rate Form 470 requests for Wi-Fi or cabling were posted since my last check?"*

## 5. Recipes

| Goal | Input |
|---|---|
| Award watch: which bids were just awarded or cancelled | `{"kinds": ["bid"], "changeTypes": ["status"], "since": "lastRun"}`, then keep rows where `after.statusNorm` is `awarded` or `cancelled` |
| New large permits in one city | `{"kinds": ["permit"], "sources": ["seattle-wa"], "changeTypes": ["new"], "minAmount": 100000}` |
| Grants moving from forecast to open | `{"sources": ["grants-gov"], "changeTypes": ["status"]}` |
| Deadline changes on open bids | `{"kinds": ["bid"], "changeTypes": ["updated"]}`, then keep rows whose `changedFields` include a date |
| Contractor activity | `{"kinds": ["permit"], "changeTypes": ["new"], "keywords": ["<company name>"]}` |

## 6. Snapshot or change feed?

| You need… | Use |
|---|---|
| Everything matching a search right now (backfill, one-off research) | [US Building Permits](https://apify.com/opendatafrontierlab/us-building-permits) or [US Public Bids](https://apify.com/opendatafrontierlab/us-public-bids) |
| Only what's new or changed since yesterday, with before/after values | [Permits & Bids Change Feed](https://apify.com/opendatafrontierlab/permits-bids-change-feed) |
| The RFP documents as text for an LLM | [PDF to Markdown & RAG Chunks](https://apify.com/opendatafrontierlab/pdf-to-markdown-rag) |

A common setup: backfill once with the snapshot tools, then keep it current with the change feed.

## FAQ

**Is SAM.gov included?** No. SAM.gov requires a personal API key. Use the US Public Bids Actor with your own key.

**How do I know a source is healthy?** Every run saves a free `SOURCE_STATUS` record with each source's last healthy day, staleness and license. Set `includeSourceHealth: true` to also get it as dataset rows.

**Is there personal data?** No. Owner, applicant and contact names, emails and phones are excluded, and emails or phone numbers inside free text are redacted. Business names are kept.

**Is it affiliated with any agency?** No. Data is republished under each publisher's license, and each record carries its license and attribution. Always confirm deadlines on the official record link.

---

*Try it:* [Permits & Bids Change Feed on Apify](https://apify.com/opendatafrontierlab/permits-bids-change-feed).
