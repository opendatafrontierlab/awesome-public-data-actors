# Turn government PDFs into RAG-ready chunks with page citations

Most RAG tutorials start with clean text. Real-world documents, especially public-sector ones, are **long PDFs**: 200-page RFP packages, Federal Register rules in three columns, standards full of tables, and scanned attachments with no text layer at all. Naive PDF-to-text extraction breaks reading order, merges headers into body text and loses the page numbers you need for citations.

This tutorial converts PDFs into **heading-aware chunks that carry their section path, page range and a ready-made citation**, loads them into a vector store, and answers questions *with sources*, all in about 40 lines of Python. It uses the [PDF to Markdown & RAG Chunks](https://apify.com/opendatafrontierlab/pdf-to-markdown-rag) Actor for the extraction step.

**Why use an Actor for extraction?** There's nothing to install or maintain: layout analysis, table detection and OCR all run in the cloud, and it scales to thousands of PDFs. It uses **no external LLM**, so there are no token costs and documents aren't sent to an AI provider. Pricing is $0.003 per document + $0.0015 per page, plus $0.004 per scanned page that needs OCR. A 30-page report costs about 5 cents, and Apify's free plan covers plenty of experimentation.

---

## 1. What a good chunk looks like

Here is a real chunk produced from a Federal Register rule (OPM, 5 CFR Part 250, published Oct 29, 2026). The text is shortened:

```json
{
  "url": "https://www.govinfo.gov/content/pkg/FR-2026-10-29/pdf/2026-22093.pdf",
  "text": "## _Administrative Burden of Quarterly Reviews_\n\nComments 0003, 0005, and 0002 raised concerns ...",
  "headingPath": ["Rules and Regulations", "_Administrative Burden of Quarterly Reviews_"],
  "pageStart": 3,
  "pageEnd": 3,
  "chunkIndex": 12,
  "approxTokens": 448,
  "citation": "2026-22093.pdf, p. 3",
  "sha256": "…",
  "markdownUrl": "https://api.apify.com/v2/key-value-stores/…/records/doc-….md"
}
```

Three things make this chunk RAG-friendly:

1. **It follows the document structure.** Chunks break at headings, so a chunk never starts mid-way through one section and ends in another (unless a section is tiny). The `headingPath` tells the model *where* in the document the text lives, which is very useful context to prepend before embedding.
2. **It carries page numbers.** `pageStart`/`pageEnd` and `citation` let your app say *"Source: p. 3"*, and users can verify the answer.
3. **It's clean.** Repeating page headers, footers and page numbers are removed, and tables are rendered as Markdown (or HTML for merged cells).

## 2. Convert your PDFs

Open the [Actor](https://apify.com/opendatafrontierlab/pdf-to-markdown-rag), click **Try for free**, and paste PDF links, or use this input:

```json
{
  "startUrls": [
    { "url": "https://www.govinfo.gov/content/pkg/FR-2026-10-29/pdf/2026-22093.pdf" },
    { "url": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf" }
  ],
  "outputMode": "chunks",
  "chunkSizeChars": 2000,
  "chunkOverlapChars": 200,
  "ocrMode": "auto"
}
```

- `chunkSizeChars: 2000` ≈ 500 tokens, which suits most embedding models. Use 1,000–1,500 for very precise retrieval.
- `ocrMode: "auto"` OCRs only pages with no text layer. Scanned attachments are handled automatically and digital pages aren't slowed down.
- Prefer one item per page? Use `"outputMode": "pages"`. Need the whole document as Markdown? Use `"document"`. The full Markdown is always saved too (`markdownUrl`).

## 3. Load the chunks into a vector store and ask questions

Install the two libraries (Chroma is used here because it runs locally with no setup; the same pattern works for Pinecone, Qdrant, pgvector or Weaviate):

```bash
pip install "apify-client>=3" chromadb
```

```python
import os
import chromadb
from apify_client import ApifyClient

# 1) Convert PDFs into chunks (runs in the cloud)
apify = ApifyClient(os.environ["APIFY_TOKEN"])
run = apify.actor("opendatafrontierlab/pdf-to-markdown-rag").call(run_input={
    "startUrls": [{"url": "https://www.govinfo.gov/content/pkg/FR-2026-10-29/pdf/2026-22093.pdf"}],
    "outputMode": "chunks",
    "chunkSizeChars": 2000,
})
chunks = [c for c in apify.dataset(run.default_dataset_id).iterate_items() if c.get("text")]

# 2) Index them; prepend the heading path so the embedding knows the context
db = chromadb.Client()
col = db.get_or_create_collection("gov-docs")
col.add(
    ids=[f"{c['docId']}-{c['chunkIndex']}" for c in chunks],
    documents=[" > ".join(c["headingPath"]) + "\n\n" + c["text"] for c in chunks],
    metadatas=[{"citation": c["citation"], "url": c["url"],
                "pageStart": c["pageStart"], "pageEnd": c["pageEnd"]} for c in chunks],
)

# 3) Retrieve with citations
question = "What concerns did commenters raise about quarterly reviews?"
res = col.query(query_texts=[question], n_results=3)
for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
    print(f"[{meta['citation']}] {doc[:200]}...\n")
```

Output from a real run (shortened):

```
[2026-22093.pdf, p. 3] Rules and Regulations > _Administrative Burden of Quarterly Reviews_

## _Administrative Burden of Quarterly Reviews_  Comments 0003, 0005, and 0002 raised concerns ...
```

Now pass the retrieved chunks to any LLM with a prompt like *"Answer using only the sources below and cite them as [citation]"*. Your app can then show answers such as:

> Commenters worried that the new quarterly reviews would create administrative burden **[2026-22093.pdf, p. 3]** …

### Using LangChain or LlamaIndex instead
Both frameworks have Apify integrations (`ApifyDatasetLoader` in LangChain, the Apify reader in LlamaIndex). Map `text` to the page content and keep `citation`, `pageStart`, `pageEnd` and `url` as metadata. The rest of your pipeline stays the same.

## 4. Keep the index fresh

Public documents change: RFPs get amendments, guidance gets revised. Every result includes a `sha256` fingerprint of the source file. Re-run the Actor on a schedule (Apify **Tasks + Schedules**) and re-embed only documents whose fingerprint changed.

Combine it with the [Government Bids & RFP Scraper](https://apify.com/opendatafrontierlab/us-public-bids) to build an end-to-end pipeline: *find new RFPs → convert their PDF packages → ask "what are the submission requirements and deadlines?"*

## 5. Let an AI agent do it

Connect the [Apify MCP server](https://mcp.apify.com) to Claude, Cursor or your own agent and add `opendatafrontierlab/pdf-to-markdown-rag`. The agent can then read any PDF link it encounters and answer with page-level citations, without you writing a PDF parser.

## Tips and gotchas

- **Scanned PDFs:** OCR is optimized for English and Latin-script text, and quality depends on the scan. Check `ocrPages` in the output to see how many pages were OCR'd.
- **Huge documents:** use `maxPagesPerDocument` to cap cost while testing. Skipped pages aren't charged.
- **Tables with merged cells:** set `"tableFormat": "html"`. LLMs read HTML tables well.
- **Failed URLs are free:** non-PDF links or download errors return an error item and aren't charged.
- **Open source:** the Actor is AGPL-3.0, built on PyMuPDF / PyMuPDF4LLM. Source: [opendatafrontierlab/pdf-to-markdown-rag](https://github.com/opendatafrontierlab/pdf-to-markdown-rag).

---

*Try it:* [PDF to Markdown & RAG Chunks on Apify](https://apify.com/opendatafrontierlab/pdf-to-markdown-rag). Paste a PDF link and see the chunks in under a minute.
