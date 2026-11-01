"""Government PDFs -> heading-aware chunks with citations -> Chroma. Env: APIFY_TOKEN. pip install "apify-client>=3" chromadb"""
import os
import chromadb
from apify_client import ApifyClient

apify = ApifyClient(os.environ["APIFY_TOKEN"])
run = apify.actor("opendatafrontierlab/pdf-to-markdown-rag").call(run_input={
    "startUrls": [{"url": "https://www.govinfo.gov/content/pkg/FR-2026-10-29/pdf/2026-22093.pdf"}],
    "outputMode": "chunks",
    "chunkSizeChars": 2000,
})
chunks = [c for c in apify.dataset(run.default_dataset_id).iterate_items() if c.get("text")]

col = chromadb.Client().get_or_create_collection("gov-docs")
col.add(
    ids=[f"{c['docId']}-{c['chunkIndex']}" for c in chunks],
    documents=[" > ".join(c["headingPath"]) + "\n\n" + c["text"] for c in chunks],
    metadatas=[{"citation": c["citation"], "url": c["url"],
                "pageStart": c["pageStart"], "pageEnd": c["pageEnd"]} for c in chunks],
)
res = col.query(query_texts=["What concerns did commenters raise about quarterly reviews?"], n_results=3)
for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
    print(f"[{meta['citation']}] {doc[:200]}...\n")
