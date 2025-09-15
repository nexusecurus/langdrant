
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import defaults as cfg

# -----------------------------
# Helper functions
# -----------------------------
def gen_uuid() -> str:
    return str(uuid4())

def gen_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

# -----------------------------
# LLM generation
# -----------------------------
class GenerateRequest(BaseModel):

    model: Optional[str] = None
    prompt: str
    max_tokens: Optional[int] = 300
    stream: Optional[bool] = False
    num_ctx: Optional[int] = None

class GenerateResponse(BaseModel):

    summary: str
    canonical_embedding_text: str

# -----------------------------
# LLM CHAT
# -----------------------------
class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    max_tokens: Optional[int] = 300
    stream: Optional[bool] = False
    num_ctx: Optional[int] = None

class ChatResponse(BaseModel):
    response: str

# -----------------------------
# Generic text ingestion
# -----------------------------
class IngestItem(BaseModel):

    id: str = Field(default_factory=gen_uuid)
    text: str
    metadata: Optional[Dict[str, Any]] = {}

class IngestRequest(BaseModel):

    collection: Optional[str] = cfg.DEFAULT_COLLECTION
    items: List[IngestItem]

# -----------------------------
# Log ingestion
# -----------------------------
class LogEntry(BaseModel):

    id: str = Field(default_factory=gen_uuid)
    timestamp: str = Field(default_factory=gen_timestamp)
    vm_id: str
    log_level: Optional[str] = "INFO"
    message: str
    metadata: Optional[Dict[str, Any]] = {}

class LogIngestRequest(BaseModel):

    collection: Optional[str] = cfg.DEFAULT_COLLECTION
    logs: List[LogEntry]

# -----------------------------
# Database row ingestion
# -----------------------------
class DBRow(BaseModel):

    id: str = Field(default_factory=gen_uuid)
    table: str
    row_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}

class DBIngestRequest(BaseModel):

    collection: Optional[str] = cfg.DEFAULT_COLLECTION
    rows: List[DBRow]

# -----------------------------
# RSS / News ingestion
# -----------------------------
class RSSArticle(BaseModel):

    id: str = Field(default_factory=gen_uuid)
    url: str
    title: str
    content: str
    published_at: str = Field(default_factory=gen_timestamp)
    metadata: Optional[Dict[str, Any]] = {}

class RSSIngestRequest(BaseModel):

    collection: Optional[str] = cfg.DEFAULT_COLLECTION
    articles: List[RSSArticle]

# -----------------------------
# RSS Fetch Request
# -----------------------------
class FetchRSSRequest(BaseModel):
    urls: List[str]
    collection: Optional[str] = cfg.DEFAULT_COLLECTION


# -----------------------------
# Social media ingestion
# -----------------------------
class SocialPost(BaseModel):

    id: str = Field(default_factory=gen_uuid)
    platform: str  # e.g., "twitter", "mastodon"
    user_id: str
    post_id: str
    content: str
    timestamp: str = Field(default_factory=gen_timestamp)
    metadata: Optional[Dict[str, Any]] = {}

class SocialIngestRequest(BaseModel):

    collection: Optional[str] = cfg.DEFAULT_COLLECTION
    posts: List[SocialPost]

# -----------------------------
# Semantic query
# -----------------------------
class QueryRequest(BaseModel):

    query: str
    top_k: int = 5
    collection: Optional[str] = None
    llm_model: Optional[str] = None
    embed_model: Optional[str] = None
    filters: Optional[Dict[str, Any]] = {}
    return_raw: Optional[bool] = False

# -----------------------------
# Semantic query-hybrid
# -----------------------------
class HybridQueryRequest(BaseModel):

    query: str
    top_k: int = 5
    collections: Optional[List[str]] = None
    llm_model: Optional[str] = None
    embed_model: Optional[str] = None
    keyword_filters: Optional[Dict[str, str]] = {}
    boost_recent_days: Optional[int] = None
    return_raw: Optional[bool] = False

# -----------------------------
# Semantic query-multi-collections
# -----------------------------
class MultiQueryRequest(BaseModel):
    query: str
    collections: List[str]
    top_k: int = 5
    llm_model: Optional[str] = None
    embed_model: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    hybrid_keywords: Optional[List[str]] = None
    return_raw: Optional[bool] = False

# -----------------------------
# Collection management
# -----------------------------
class CollectionResponse(BaseModel):
    name: str
    vectors_count: int

class DeleteCollectionRequest(BaseModel):
    collection: str

# -----------------------------
# DEBUG: Endpoints
# -----------------------------
class DebugChunkRequest(BaseModel):
    text: str
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None

class DebugEmbedRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = None
    return_vectors: Optional[bool] = True

class DebugEmbedResponse(BaseModel):
    count: int
    dims: Optional[int] = None
    vectors: Optional[List[List[float]]] = None
