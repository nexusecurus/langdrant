
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, UploadFile, Form
from typing import List, Optional
import asyncio

# -----------------------------
# Import centralized defaults
# -----------------------------
import defaults as cfg

# -----------------------------
# Logging Configuration
# -----------------------------
class ISOFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.utcfromtimestamp(record.created).isoformat() + "Z"


logging.basicConfig(
    level=getattr(logging, cfg.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt=None
)

for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers:
        handler.setFormatter(ISOFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))

# -----------------------------
# Import schemas, utils, and ingestion modules
# -----------------------------
from schemas import (
    IngestRequest, LogIngestRequest, DBIngestRequest,
    RSSIngestRequest, FetchRSSRequest, SocialIngestRequest, QueryRequest,
    DeleteCollectionRequest, GenerateRequest, DebugChunkRequest,
    DebugEmbedRequest, DebugEmbedResponse, HybridQueryRequest,
    MultiQueryRequest, ChatRequest, ChatResponse
)
from ingest import (
    ingest_texts, ingest_file, ingest_logs, ingest_db_rows,
    ingest_rss, ingest_social, fetch_and_ingest_rss_feed,
    chunk_text
)
from qdrant_store import QdrantStore
from embeddings import embed_query, generate_completion, stream_completion, embed_texts
from utils import require_api_key
from sse_starlette.sse import EventSourceResponse

# -----------------------------
# FastAPI initialization
# -----------------------------
app = FastAPI(title="LangChain Multi-Source API")
store = QdrantStore()

# -----------------------------
# Endpoint: LLM Generation
# -----------------------------
@app.post("/generate")
def api_generate(req: GenerateRequest, auth: bool = Depends(require_api_key)):
    response = generate_completion(
        prompt=req.prompt,
        model=req.model or cfg.LLM_MODEL,
        max_tokens=req.max_tokens or cfg.LLM_MAX_TOKENS,
        n8n_ready=True,
        num_ctx=req.num_ctx or cfg.LLM_CTX
    )
    return {"response": response}


# -----------------------------
# Endpoint: CHAT
# -----------------------------
@app.post("/chat")
def api_chat(req: ChatRequest, auth: bool = Depends(require_api_key)):

    conversation = []
    for msg in req.messages:
        prefix = f"{msg.role.capitalize()}: "
        conversation.append(prefix + msg.content.strip())
    prompt = "\n".join(conversation) + "\nAssistant:"

    use_stream = req.stream if req.stream is not None else cfg.LLM_STREAM

    if use_stream:
        async def event_generator():
            for chunk in stream_completion(
                prompt,
                model=req.model or cfg.LLM_MODEL,
                max_tokens=req.max_tokens or cfg.LLM_MAX_TOKENS
            ):
                yield {"data": chunk}

            yield {"data": "[DONE]"}

        return EventSourceResponse(event_generator())

    reply = generate_completion(
        prompt=prompt,
        model=req.model or cfg.LLM_MODEL,
        max_tokens=req.max_tokens or cfg.LLM_MAX_TOKENS
    )
    return ChatResponse(response=reply)

# -----------------------------
# Endpoint: Generic Text Ingestion
# -----------------------------
@app.post("/ingest_texts")
async def api_ingest_texts(request: IngestRequest, auth: bool = Depends(require_api_key)):
    return await ingest_texts(request, store)

# -----------------------------
# Endpoint: File Ingestion
# -----------------------------
@app.post("/ingest_file")
async def api_ingest_file(
    file: UploadFile,
    collection: Optional[str] = Form(None),
    auth: bool = Depends(require_api_key)
):
    return await ingest_file(file, collection or cfg.DEFAULT_COLLECTION, store)

# -----------------------------
# Endpoint: Log Ingestion
# -----------------------------
@app.post("/ingest_logs")
async def api_ingest_logs(request: LogIngestRequest, auth: bool = Depends(require_api_key)):
    return await ingest_logs(request, store)

# -----------------------------
# Endpoint: Database Row Ingestion
# -----------------------------
@app.post("/ingest_db")
async def api_ingest_db(request: DBIngestRequest, auth: bool = Depends(require_api_key)):
    db_config = {
        "host": cfg.DB_HOST,
        "port": cfg.DB_PORT,
        "dbname": cfg.DB_NAME,
        "user": cfg.DB_USER,
        "password": cfg.DB_PASSWORD
    }
    return await ingest_db_rows(request, db_config, store)

# -----------------------------
# Endpoint: RSS Ingestion
# -----------------------------
@app.post("/ingest_rss")
async def api_ingest_rss(request: RSSIngestRequest, auth: bool = Depends(require_api_key)):
    return await ingest_rss(request, store)

# -----------------------------
# Endpoint: Social Media Ingestion
# -----------------------------
@app.post("/ingest_social")
async def api_ingest_social(request: SocialIngestRequest, auth: bool = Depends(require_api_key)):
    return await ingest_social(request, store)

# -----------------------------
# Endpoint: Fetch and ingest RSS feeds
# -----------------------------
@app.post("/fetch_rss_feeds")
async def api_fetch_rss_feeds(
    request: FetchRSSRequest,
    auth: bool = Depends(require_api_key)
):
    return await fetch_and_ingest_rss_feed(request.urls, request.collection, store)


# -----------------------------
# Endpoint: Semantic Query
# -----------------------------
@app.post("/query")
def api_query(req: QueryRequest, auth: bool = Depends(require_api_key)):
    vec = embed_query(req.query, req.embed_model or cfg.EMBED_MODEL)
    
    results = store.search_by_vector(
        vec,
        req.collection or cfg.DEFAULT_COLLECTION,
        top_k=req.top_k or cfg.QUERY_TOP_K,
        filter=req.filters
    )

    if req.llm_model and results:
        context_snippets = [r["payload"].get("snippet", "") for r in results if r["payload"].get("snippet")]
        context_text = "\n\n".join(context_snippets)

        enriched = generate_completion(
            f"Here are some factual snippets from the knowledge base:\n\n{context_text}\n\n"
            "Please provide a concise summary or highlight key points without adding new information.",
            model=req.llm_model
        )
        return {"enriched": enriched, "results": results}

    return {"results": results}



# -----------------------------
# Endpoint: Semantic Query-Hybrid
# -----------------------------
@app.post("/query_hybrid")
def api_query_hybrid(req: HybridQueryRequest, auth: bool = Depends(require_api_key)):
    collections = req.collections or [cfg.DEFAULT_COLLECTION]
    vec = embed_query(req.query, req.embed_model or cfg.EMBED_MODEL)

    all_results = []
    for coll in collections:
        results = store.search_by_vector(
            vec,
            collection=coll,
            top_k=req.top_k or cfg.QUERY_TOP_K,
            filter=None
        )

        if req.keyword_filters:
            filtered = []
            for r in results:
                payload = r.get("payload", {})
                match = True
                for key, val in req.keyword_filters.items():
                    if key not in payload or val.lower() not in str(payload[key]).lower():
                        match = False
                        break
                if match:
                    filtered.append(r)
            results = filtered

        if req.boost_recent_days:
            cutoff = datetime.utcnow() - timedelta(days=req.boost_recent_days)

            def recent_score(r):
                ts = r.get("payload", {}).get("published_at")
                if not ts:
                    return 0
                try:
                    dt = datetime.fromisoformat(ts)
                    return 1 if dt > cutoff else 0
                except Exception:
                    return 0

            results.sort(key=recent_score, reverse=True)

        all_results.extend(results)

    all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)[: req.top_k or cfg.QUERY_TOP_K]

    enriched = None
    if req.llm_model and all_results:
        context_snippets = [r["payload"].get("snippet", "") for r in all_results]
        context_text = "\n\n".join(context_snippets)

        enriched = generate_completion(
            f"Here are some factual snippets from the knowledge base:\n\n{context_text}\n\n"
            "Please provide a concise summary or highlight key points without adding new information.",
            model=req.llm_model
        )

    return {
        "query": req.query,
        "collections": collections,
        "results": all_results if req.return_raw else [r["payload"] for r in all_results],
        "enriched": enriched
    }

# -----------------------------
# Endpoint: Semantic Query-Multi-Collections
# -----------------------------
@app.post("/query_multi")
def api_query_multi(req: MultiQueryRequest, auth: bool = Depends(require_api_key)):
    vec = embed_query(req.query, req.embed_model or cfg.EMBED_MODEL)
    all_results = []

    for collection in req.collections or [cfg.DEFAULT_COLLECTION]:
        results = store.search_by_vector(
            vec,
            collection,
            top_k=req.top_k or cfg.QUERY_TOP_K,
            filter=req.filters
        )
        for r in results:
            r["collection"] = collection
        all_results.extend(results)

    all_results.sort(key=lambda x: x["score"], reverse=True)
    all_results = all_results[: req.top_k or cfg.QUERY_TOP_K]

    answer = None
    if req.llm_model and all_results:
        context_snippets = [r["payload"].get("snippet", "") for r in all_results]
        context_text = "\n\n".join(context_snippets)

        answer = generate_completion(
            f"Here are some factual snippets from the knowledge base:\n\n{context_text}\n\n"
            "Please provide a concise summary or highlight key points without adding new information.",
            model=req.llm_model
        )

    return {
        "results": all_results if req.return_raw else [r["payload"] for r in all_results],
        "answer": answer
    }


# -----------------------------
# Endpoint: List Collections
# -----------------------------
@app.get("/collections")
def api_list_collections(auth: bool = Depends(require_api_key)):
    return {"collections": store.list_collections()}

# -----------------------------
# Endpoint: Delete Collection
# -----------------------------
@app.post("/collections/delete")
def api_delete_collection(req: DeleteCollectionRequest, auth: bool = Depends(require_api_key)):
    store.delete_collection(req.collection)
    return {"ok": True, "deleted": req.collection}

# -----------------------------
# Health Check Endpoint
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------------
# Ping Endpoint
# -----------------------------
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}

# -----------------------------
# Debug: Chunking
# -----------------------------
@app.post("/debug/chunk")
def debug_chunk(req: DebugChunkRequest):
    
    chunks = chunk_text(
        req.text,
        chunk_size=req.chunk_size or cfg.CHUNK_SIZE,
        chunk_overlap=req.chunk_overlap or cfg.CHUNK_OVERLAP
    )
    return {
        "total_chunks": len(chunks),
        "chunks": chunks,
        "preview": [c[:200] for c in chunks]  # first 200 chars only
    }

# -----------------------------
# Debug: Embeddings
# -----------------------------
@app.post("/debug/embeds", response_model=DebugEmbedResponse)
async def api_debug_embeds(req: DebugEmbedRequest, auth: bool = Depends(require_api_key)):
    try:
        vectors = await asyncio.to_thread(embed_texts, req.texts, model=req.model or cfg.EMBED_MODEL)
        dims = len(vectors[0]) if vectors else None

        return DebugEmbedResponse(
            count=len(vectors),
            dims=dims,
            vectors=vectors if req.return_vectors else None
        )
    except Exception as e:
        return {"error": str(e)}
