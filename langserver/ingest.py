
import uuid
import hashlib
import itertools
import asyncio
from typing import List, Optional, Dict, Any, Iterable

import feedparser
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter

from embeddings import embed_texts
from qdrant_store import QdrantStore
from utils import parse_file_to_text
from schemas import (
    IngestRequest, LogIngestRequest, DBIngestRequest,
    RSSIngestRequest, RSSArticle, SocialIngestRequest,
    IngestItem
)
import defaults as cfg

# -----------------------------
# Default chunking & batching
# -----------------------------
DEFAULT_CHUNK_SIZE = cfg.CHUNK_SIZE
DEFAULT_CHUNK_OVERLAP = cfg.CHUNK_OVERLAP
EMBED_BATCH_SIZE = cfg.EMBED_BATCH_SIZE
LOG_LINES_PER_CHUNK = cfg.LOG_LINES_PER_CHUNK

# -----------------------------
# Deterministic ID generation
# -----------------------------
def deterministic_id(*parts: str) -> str:
    joined = "|".join([p or "" for p in parts])
    hash_bytes = hashlib.sha256(joined.encode("utf-8")).digest()
    return str(uuid.UUID(bytes=hash_bytes[:16]))

# -----------------------------
# Text chunking
# -----------------------------
def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    cs = chunk_size or DEFAULT_CHUNK_SIZE
    co = chunk_overlap or DEFAULT_CHUNK_OVERLAP
    splitter = RecursiveCharacterTextSplitter(chunk_size=cs, chunk_overlap=co)
    return splitter.split_text(text)


def batch_iterable(iterable: Iterable, size: int) -> Iterable[List]:
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, size))
        if not batch:
            break
        yield batch


def _point_exists(store: QdrantStore, collection: str, point_id: str) -> bool:
    try:
        return store.point_exists(collection, point_id)
    except Exception:
        return False

# -----------------------------
# Generic text ingestion
# -----------------------------
async def ingest_texts(request: IngestRequest, store: QdrantStore, batch_size: int = EMBED_BATCH_SIZE):
    collection = request.collection or cfg.DEFAULT_COLLECTION
    texts, metadatas, ids = [], [], []

    for item in request.items:
        if not item.id:
            item.id = str(uuid.uuid4())
        chunks = chunk_text(item.text)
        for i, chunk in enumerate(chunks):
            pt_id = deterministic_id(item.id, str(i))
            texts.append(chunk)
            md = dict(item.metadata or {})
            md.update({
                "source_type": md.get("source_type", "text"),
                "chunk_index": i,
                "snippet": chunk[:1000]
            })
            metadatas.append(md)
            ids.append(pt_id)

    total = 0
    for batch_ids, batch_metadatas, batch_texts in zip(
        batch_iterable(ids, batch_size),
        batch_iterable(metadatas, batch_size),
        batch_iterable(texts, batch_size)
    ):
        vectors = await asyncio.to_thread(embed_texts, batch_texts)
        await asyncio.to_thread(store.upsert, collection, batch_ids, vectors, batch_metadatas)
        total += len(batch_ids)

    return {"ok": True, "collection": collection, "count": total}

# -----------------------------
# File ingestion (async)
# -----------------------------
async def ingest_file(file: UploadFile, collection: Optional[str], store: QdrantStore,
                      chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
    data = await file.read()
    text = parse_file_to_text(data, file.filename)
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    coll = collection or cfg.DEFAULT_COLLECTION
    ids = [deterministic_id(file.filename, str(i)) for i in range(len(chunks))]
    metadatas = [{"source": file.filename, "chunk_index": i, "source_type": "file", "snippet": chunks[i][:1000]}
                 for i in range(len(chunks))]

    total = 0
    for id_batch, md_batch, txt_batch in zip(
        batch_iterable(ids, EMBED_BATCH_SIZE),
        batch_iterable(metadatas, EMBED_BATCH_SIZE),
        batch_iterable(chunks, EMBED_BATCH_SIZE)
    ):
        vecs = await asyncio.to_thread(embed_texts, txt_batch)
        await asyncio.to_thread(store.upsert, coll, id_batch, vecs, md_batch)
        total += len(id_batch)

    return {"ok": True, "collection": coll, "count": total}

# -----------------------------
# Log ingestion
# -----------------------------
async def ingest_logs(request: LogIngestRequest, store: QdrantStore, batch_size: int = EMBED_BATCH_SIZE):
    collection = request.collection or cfg.DEFAULT_COLLECTION
    texts, metadatas, ids = [], [], []

    for entry in request.logs:
        text = f"[{entry.timestamp}] [{entry.vm_id}] [{entry.log_level}] {entry.message}"
        if not entry.id:
            entry.id = str(uuid.uuid4())
        chunks = chunk_text(text)
        for i, c in enumerate(chunks):
            pt_id = deterministic_id(entry.id, str(i))
            md = dict(entry.metadata or {})
            md.update({
                "source_type": "log",
                "vm_id": entry.vm_id,
                "timestamp": entry.timestamp,
                "log_level": entry.log_level,
                "chunk_index": i,
                "snippet": c[:1000]
            })
            texts.append(c)
            metadatas.append(md)
            ids.append(pt_id)

    total = 0
    for batch_ids, batch_mds, batch_texts in zip(
        batch_iterable(ids, batch_size),
        batch_iterable(metadatas, batch_size),
        batch_iterable(texts, batch_size)
    ):
        vectors = await asyncio.to_thread(embed_texts, batch_texts)
        await asyncio.to_thread(store.upsert, collection, batch_ids, vectors, batch_mds)
        total += len(batch_ids)

    return {"ok": True, "collection": collection, "count": total}

# -----------------------------
# DB ingestion
# -----------------------------
async def ingest_db_rows(request: DBIngestRequest, db_config: Dict[str, Any], store: QdrantStore,
                         batch_size: int = EMBED_BATCH_SIZE, text_columns: Optional[List[str]] = None):
    collection = request.collection or cfg.DEFAULT_COLLECTION
    texts, metadatas, ids = [], [], []

    if not request.rows:
        return {"ok": False, "error": "No rows provided."}

    for row in request.rows:
        if not row.id:
            row.id = str(uuid.uuid4())
        pieces = [str(row.row_data.get(c, "")) for c in (text_columns or row.row_data.keys())]
        text = "\n".join(pieces)
        chunks = chunk_text(text)
        for i, c in enumerate(chunks):
            pt_id = deterministic_id(row.id, str(i))
            md = dict(row.metadata or {})
            md.update({"source_type": "db", "table": row.table, "chunk_index": i, "snippet": c[:1000]})
            texts.append(c)
            metadatas.append(md)
            ids.append(pt_id)

    total = 0
    for id_batch, md_batch, txt_batch in zip(
        batch_iterable(ids, batch_size),
        batch_iterable(metadatas, batch_size),
        batch_iterable(texts, batch_size)
    ):
        vecs = await asyncio.to_thread(embed_texts, txt_batch)
        await asyncio.to_thread(store.upsert, collection, id_batch, vecs, md_batch)
        total += len(id_batch)

    return {"ok": True, "collection": collection, "count": total}

# -----------------------------
# RSS ingestion
# -----------------------------
async def ingest_rss(request: RSSIngestRequest, store: QdrantStore, batch_size: int = EMBED_BATCH_SIZE):
    collection = request.collection or cfg.DEFAULT_COLLECTION
    texts, metadatas, ids = [], [], []

    for article in request.articles:
        if not article.id or article.id.strip() == "":
            article.id = deterministic_id(article.url or "", article.published_at or "")

        text = f"{article.title}\n\n{article.content}"
        chunks = chunk_text(text)
        for i, c in enumerate(chunks):
            pt_id = deterministic_id(article.id, str(i))
            md = dict(article.metadata or {})
            md.update({
                "source_type": "rss",
                "url": article.url,
                "title": article.title,
                "published_at": article.published_at,
                "chunk_index": i,
                "snippet": c[:1000]
            })
            if _point_exists(store, collection, pt_id):
                continue
            texts.append(c)
            metadatas.append(md)
            ids.append(pt_id)

    total = 0
    for id_batch, md_batch, txt_batch in zip(
        batch_iterable(ids, batch_size),
        batch_iterable(metadatas, batch_size),
        batch_iterable(texts, batch_size)
    ):
        vecs = await asyncio.to_thread(embed_texts, txt_batch)
        await asyncio.to_thread(store.upsert, collection, id_batch, vecs, md_batch)
        total += len(id_batch)

    return {"ok": True, "collection": collection, "count": total}

# -----------------------------
# Social media ingestion
# -----------------------------
async def ingest_social(request: SocialIngestRequest, store: QdrantStore, batch_size: int = EMBED_BATCH_SIZE):
    collection = request.collection or cfg.DEFAULT_COLLECTION
    texts, metadatas, ids = [], [], []

    for post in request.posts:
        if not post.id:
            post.id = str(uuid.uuid4())
        chunks = chunk_text(post.content)
        for i, c in enumerate(chunks):
            pt_id = deterministic_id(post.id, str(i))
            md = dict(post.metadata or {})
            md.update({
                "source_type": "social",
                "platform": post.platform,
                "user_id": post.user_id,
                "post_id": post.post_id,
                "timestamp": post.timestamp,
                "chunk_index": i,
                "snippet": c[:1000]
            })
            if _point_exists(store, collection, pt_id):
                continue
            texts.append(c)
            metadatas.append(md)
            ids.append(pt_id)

    total = 0
    for id_batch, md_batch, txt_batch in zip(
        batch_iterable(ids, batch_size),
        batch_iterable(metadatas, batch_size),
        batch_iterable(texts, batch_size)
    ):
        vecs = await asyncio.to_thread(embed_texts, txt_batch)
        await asyncio.to_thread(store.upsert, collection, id_batch, vecs, md_batch)
        total += len(id_batch)

    return {"ok": True, "collection": collection, "count": total}

# -----------------------------
# Fetch and ingest RSS feeds (async)
# -----------------------------
async def fetch_and_ingest_rss_feed(urls: List[str], collection: str, store: QdrantStore):
    async def fetch_feed(url: str) -> List[RSSArticle]:
        feed = await asyncio.to_thread(feedparser.parse, url)
        articles = []
        for entry in feed.entries:
            article_id = deterministic_id(entry.get("link", ""), entry.get("published", ""))
            article = RSSArticle(
                id=article_id,
                title=entry.get("title", ""),
                content=entry.get("summary", ""),
                url=entry.get("link", ""),
                published_at=entry.get("published", ""),
                metadata={}
            )
            articles.append(article)
        return articles

    all_articles_lists = await asyncio.gather(*(fetch_feed(url) for url in urls))
    all_articles = [article for sublist in all_articles_lists for article in sublist]

    request = RSSIngestRequest(collection=collection or cfg.DEFAULT_COLLECTION, articles=all_articles)
    return await ingest_rss(request, store)
