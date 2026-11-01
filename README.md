# Awesome Public Data Actors

Tutorials, runnable examples and source lists for turning **official public data** (building permits, government bids and grants, public PDFs) into clean feeds for spreadsheets, CRMs, RAG pipelines and AI agents.

Maintained by [OpenDataFrontierLab](https://apify.com/opendatafrontierlab). The tools below are paid, pay-per-use Apify Actors (Apify's free plan includes monthly credit for testing). The tutorials also show the free DIY route where one exists.

## Tutorials
| Tutorial | You'll build |
|---|---|
| [Daily building-permit leads for your city](tutorials/building-permit-leads.md) | New solar / roofing / HVAC / pool permits in a Google Sheet or Slack every morning |
| [Government PDFs to RAG-ready chunks with page citations](tutorials/pdf-rag-chunks.md) | Heading-aware chunks with page numbers in a vector DB, answers with sources |
| [Track daily changes in building permits and public bids](tutorials/track-daily-changes.md) | A daily feed of only new records and status changes (open → awarded), never repeated |

## Runnable examples
- [`examples/permits_to_slack.py`](examples/permits_to_slack.py): new permits matching a keyword, posted to Slack
- [`examples/pdf_chunks_to_chroma.py`](examples/pdf_chunks_to_chroma.py): PDF to chunks to Chroma, query with citations
- [`examples/change_feed_to_slack.py`](examples/change_feed_to_slack.py): new bids and status changes to Slack

All need `pip install apify-client requests` (plus `chromadb` for the RAG example) and an `APIFY_TOKEN` environment variable.

## Actors
| Actor | Use it for |
|---|---|
| [US & Canada Building Permits](https://apify.com/opendatafrontierlab/us-building-permits) | Permit search across 12 city/county portals: Chicago, NYC (DOB NOW), Los Angeles, San Francisco, Seattle, Austin, Cincinnati, Mesa AZ, Marin County CA, Montgomery County MD, Calgary, Edmonton |
| [US Public Bids, RFPs & Grants](https://apify.com/opendatafrontierlab/us-public-bids) | NYC City Record, LA RAMP, Delaware, Montgomery County MD, Illinois CDB, Baton Rouge, E-Rate Form 470, Grants.gov, and SAM.gov with your own key |
| [Permits & Bids Change Feed](https://apify.com/opendatafrontierlab/permits-bids-change-feed) | Daily deltas across those 20 feeds, with before/after values (archive since 2026-10-29) |
| [PDF to Markdown & RAG Chunks](https://apify.com/opendatafrontierlab/pdf-to-markdown-rag) | Long PDFs to Markdown chunks with page citations and OCR. [Open source, AGPL-3.0](https://github.com/opendatafrontierlab/pdf-to-markdown-rag) |

## Free official sources (DIY route)
- City and county open-data portals, most on Socrata (SODA API) or ArcGIS Hub. Search "*&lt;city&gt; open data building permits*".
- [Grants.gov API](https://www.grants.gov/api): federal grant opportunities
- [USAC Open Data](https://opendata.usac.org/): E-Rate Form 470 requests from schools and libraries
- [SAM.gov Get Opportunities API](https://open.gsa.gov/api/get-opportunities-public-api/): federal contract opportunities (free API key)
- [govinfo](https://www.govinfo.gov/) and the [Federal Register](https://www.federalregister.gov/): rules and notices as PDF and XML

## Contributing
Know an official permit or bid dataset that should be covered? [Open an issue](../../issues) with the portal link and the dataset ID.

## License
Text: [CC BY 4.0](LICENSE). Code in `examples/`: MIT, free to copy into your own projects. Data stays under each publisher's license. Not affiliated with any government agency.
