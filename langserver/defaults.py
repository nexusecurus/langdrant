
import os
import json
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# -----------------------------
# Helper functions
# -----------------------------
def _get_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _get_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _get_json(name: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    v = os.getenv(name)
    if not v:
        return default or {}
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return default or {}

# -----------------------------
# API & Logging
# -----------------------------
API_KEY: str = os.getenv("API_KEY", "")
API_PORT: int = _get_int("API_PORT", 8000)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# -----------------------------
# Vector Database (Qdrant)
# -----------------------------
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
VECTOR_SIZE: int = _get_int("VECTOR_SIZE", 1536)
COLLECTION_CACHE_TTL: int = _get_int("COLLECTION_CACHE_TTL", 10)
DEFAULT_COLLECTION: str = os.getenv("DEFAULT_COLLECTION", "knowledge")
QUERY_TOP_K: int = _get_int("QUERY_TOP_K", 5)

# -----------------------------
# LLM / Embeddings (Ollama)
# -----------------------------
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3:8b")

LLM_CTX: int = _get_int("LLM_CTX", 4096)

LLM_MAX_TOKENS: int = _get_int("LLM_MAX_TOKENS", 300)
LLM_STREAM: bool = _get_bool("LLM_STREAM", False)

OLLAMA_RETRY_COUNT: int = _get_int("OLLAMA_RETRY_COUNT", 3)
OLLAMA_RETRY_DELAY: float = _get_float("OLLAMA_RETRY_DELAY", 2.0)

# -----------------------------
# Database Ingest
# -----------------------------
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = _get_int("DB_PORT", 5432)
DB_NAME: str = os.getenv("DB_NAME", "rag_db")
DB_USER: str = os.getenv("DB_USER", "ragadmin")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

# -----------------------------
# Ingestion Settings
# -----------------------------
CHUNK_SIZE: int = _get_int("CHUNK_SIZE", 800)
CHUNK_OVERLAP: int = _get_int("CHUNK_OVERLAP", 120)
EMBED_BATCH_SIZE: int = _get_int("EMBED_BATCH_SIZE", 64)
LOG_LINES_PER_CHUNK: int = _get_int("LOG_LINES_PER_CHUNK", 80)

# -----------------------------
# Safety checks
# -----------------------------
if not API_KEY:
    raise RuntimeError("❌ Missing API_KEY in .env file")

if not QDRANT_URL:
    raise RuntimeError("❌ Missing QDRANT_URL in .env file")

if not OLLAMA_BASE_URL:
    raise RuntimeError("❌ Missing OLLAMA_BASE_URL in .env file")
