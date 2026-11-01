# How to get daily building permit leads for your city (no scraping, no login)

Every time a homeowner replaces a roof, adds solar panels, digs a pool or builds an ADU, the city issues a **building permit**, and in many cities that permit appears in a public open-data portal within a day or two. For contractors, suppliers and home-service businesses, that is one of the best lead signals there is: the job is real, the address is known, and the timing is right now.

The problem is that every city publishes permits differently: different portals, field names, date formats and quirks. This tutorial shows how to turn 12 official city and county permit datasets into **one clean daily lead feed** in about 10 minutes, using the [Building Permits Scraper](https://apify.com/opendatafrontierlab/us-building-permits) Actor on Apify.

**What you'll build:** every morning at 7:00, new permits matching your trade (say, `solar` in Austin, Seattle and Los Angeles) land in a Google Sheet and a Slack channel. Each permit arrives once, never twice.

**Cost:** $0.003 per permit returned. A typical daily trade-filtered feed across 3 cities returns 20–200 permits, which costs **$0.06–$0.60 per day**. Apify's free plan includes monthly credit, so you can try all of this for free.

---

## 1. Why official open data beats scraping permit websites

Permit "lookup" websites are built for one-off searches, not data pulls. Scraping them is slow and fragile, and often against their terms. Many cities, though, publish the *same* data through documented open-data APIs (Socrata/SODA, ArcGIS) under open licenses that explicitly allow reuse.

The Actor uses only those official APIs. Each record includes a `source` block with the dataset URL and license, so you always know where a lead came from. It also **never collects owner or applicant names, phone numbers or emails**. You get the address, the work description, the project value and, where the city publishes it, the **contractor's business name**.

Covered today: Chicago, New York City (DOB NOW), Los Angeles, San Francisco, Seattle, Austin, Cincinnati, Mesa AZ, Marin County CA, Montgomery County MD (commercial), Calgary and Edmonton.

## 2. Run your first pull

1. Open the [Actor page](https://apify.com/opendatafrontierlab/us-building-permits) and click **Try for free** (you'll need a free Apify account).
2. Fill in the input:
   - **Jurisdictions:** `austin-tx`, `seattle-wa`, `los-angeles-ca`
   - **Days back:** `7`
   - **Keyword:** `solar`
3. Click **Start**.

Or paste this JSON into the input's JSON tab:

```json
{
  "jurisdictions": ["austin-tx", "seattle-wa", "los-angeles-ca"],
  "daysBack": 7,
  "keyword": "solar",
  "maxItems": 500
}
```

The run usually finishes in under 30 seconds. Here's a real record from a test run (Austin):

```json
{
  "jurisdiction": "Austin, TX",
  "permitNumber": "2026-132017 EP",
  "permitType": "Electrical Permit",
  "workType": "Auxiliary Power",
  "description": "Install new 5.7 kW rooftop solar system to existing residential ...",
  "status": "Active",
  "appliedDate": "2026-10-07",
  "issuedDate": "2026-10-28",
  "address": "(street address)",
  "zip": "78759",
  "contractorBusinessName": "Power Home Remodeling",
  "source": {
    "portal": "datahub.austintexas.gov",
    "datasetUrl": "https://datahub.austintexas.gov/d/3syk-w9eu",
    "license": "Public Domain U.S. Government"
  }
}
```
*(Street address and coordinates omitted here; they are included in the real output.)*

Every city comes back in the same schema (`permitNumber`, `permitType`, `workType`, `description`, `status`, `issuedDate`, `address`, `zip`, `valuationUsd`, `contractorBusinessName`, `latitude`, `longitude`, `url`), so one spreadsheet or CRM mapping works for all of them.

### Keyword ideas by trade

| Trade | Keywords that work well |
|---|---|
| Solar | `solar`, `photovoltaic`, `PV` |
| Roofing | `roof`, `re-roof`, `reroof` |
| HVAC | `HVAC`, `furnace`, `heat pump`, `AC` |
| Pools | `pool`, `spa` |
| ADUs / additions | `ADU`, `accessory dwelling`, `addition` |
| Demolition / new build | `demolition`, `new construction` |
| Commercial fit-outs | `tenant improvement`, `TI` |

For bigger jobs, add `"minValuation": 100000`. That filters out minor repairs. (Some cities record a placeholder value of `1` on over-the-counter permits, which this filter also removes.)

## 3. Turn it into a daily feed

1. On the Actor page, click **Save as a new task** with your input, and add:
   ```json
   { "daysBack": 3, "onlyNewSinceLastRun": true }
   ```
   `onlyNewSinceLastRun` remembers which permits you've already received, so each one is delivered exactly once. Combined with a small overlap window (`daysBack: 3`), you won't miss permits that portals publish late. Los Angeles often lags 2–5 days.
2. In the task, open **Schedules → Create schedule**, and pick *every day at 07:00* in your time zone.

That's it: one automated run per day, and you pay only for new permits.

## 4. Send the leads where you work

**Google Sheets:** in the task's **Integrations** tab, add the *Google Sheets* integration (or use Make/Zapier with the Apify app). Map the dataset to a sheet and new rows get appended after each run.

**Slack / email:** in Zapier or Make, use the trigger *"Apify: Finished task run"*, then the action *"Apify: Fetch dataset items"*, then *"Slack: Send message"* with a template like:

```
🏗️ {{jurisdiction}} — {{permitType}}
{{description}}
📍 {{address}}  💲{{valuationUsd}}  👷 {{contractorBusinessName}}
```

**Your CRM or app:** call the API directly. This Python snippet fetches the latest leads and posts them to a Slack webhook:

```python
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
```

**AI agents:** connect the [Apify MCP server](https://mcp.apify.com) to Claude, Cursor or your own agent and add `opendatafrontierlab/us-building-permits`. Then you can simply ask, *"Which pool permits were issued in Austin this week, and which contractors pulled them?"*

## 5. What to do with the leads (responsibly)

- **Subcontractors and suppliers:** the `contractorBusinessName` field tells you which general contractors are active in your area. They are your real customers.
- **Direct-to-homeowner trades:** use the address for compliant outreach such as direct mail or door hangers. Follow your local marketing laws; this data deliberately contains no personal contact details.
- **Market intelligence:** count permits per ZIP per month to see where renovation and new construction are growing.

## FAQ

**Is this legal?** Yes. It uses official open-data APIs published for public reuse, and each record cites its license. It collects no personal data.

**My city isn't listed.** Request it on the Actor's *Issues* tab. Most cities with a Socrata or ArcGIS permits dataset can be added quickly.

**How do I keep costs under control?** Set `maxItems`. You're charged only for permits returned, and a narrow keyword plus `onlyNewSinceLastRun` keeps daily runs small.

---

*Next step:* [open the Building Permits Scraper](https://apify.com/opendatafrontierlab/us-building-permits) and run the example above. Want only what changed since yesterday, including status changes? See [Track daily changes in building permits and public bids](track-daily-changes.md). Want government RFPs too? See the [Government Bids & RFP Scraper](https://apify.com/opendatafrontierlab/us-public-bids).
