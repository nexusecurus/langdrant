
import time
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from qdrant_client.models import Filter, FieldCondition, MatchValue
import defaults as cfg  # centralized configuration

# -----------------------------
# Configuration from defaults.py
# -----------------------------
QDRANT_URL = cfg.QDRANT_URL
QDRANT_API_KEY = cfg.QDRANT_API_KEY
DEFAULT_VECTOR_SIZE = cfg.VECTOR_SIZE
COLLECTION_CACHE_TTL = cfg.COLLECTION_CACHE_TTL


class QdrantStore:

    def __init__(self, default_collection: str = None):
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self.default_collection = default_collection or cfg.DEFAULT_COLLECTION

        self._collections_cache: Optional[List[Dict[str, Any]]] = None
        self._collections_cache_ts: float = 0

        self._vectors_count_cache: Dict[str, Dict[str, Any]] = {} 

    # -----------------------------
    # Internal cache management
    # -----------------------------
    def _refresh_collections_cache(self) -> None:
        now = time.time()
        if self._collections_cache and now - self._collections_cache_ts < COLLECTION_CACHE_TTL:
            return 

        try:
            collections_info = self.client.get_collections().collections
        except Exception:
            collections_info = []

        result = []
        for c in collections_info:
            name = getattr(c, "name", "unknown")
            count_data = self._vectors_count_cache.get(name, {})
            count = count_data.get("count")
            result.append({"name": name, "vectors_count": count})

        self._collections_cache = result
        self._collections_cache_ts = now

    def _update_vectors_count_cache(self, collection: str) -> None:
        try:
            count = self.client.count(collection_name=collection).count
        except Exception:
            count = None
        self._vectors_count_cache[collection] = {"count": count, "ts": time.time()}

    # -----------------------------
    # Collection operations
    # -----------------------------
    def create_collection_if_missing(self, name: str, vector_size: int = None) -> None:
        self._refresh_collections_cache()
        vector_size = vector_size or DEFAULT_VECTOR_SIZE
        existing_names = [c["name"] for c in (self._collections_cache or [])]
        if name not in existing_names:
            try:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
                )
            except Exception as e:
                raise RuntimeError(f"Failed to create collection '{name}': {e}")

            # Invalidate caches
            self._collections_cache = None
            self._vectors_count_cache[name] = {"count": 0, "ts": time.time()}

    def delete_collection(self, name: str) -> None:
        self._refresh_collections_cache()
        existing_names = [c["name"] for c in (self._collections_cache or [])]
        if name in existing_names:
            try:
                self.client.delete_collection(collection_name=name)
            except Exception as e:
                raise RuntimeError(f"Failed to delete collection '{name}': {e}")
            self._collections_cache = None
            self._vectors_count_cache.pop(name, None)

    def list_collections(self) -> List[Dict[str, Any]]:
        self._refresh_collections_cache()
        now = time.time()
        for c in self._collections_cache or []:
            name = c["name"]
            cached = self._vectors_count_cache.get(name, {})
            if not cached or now - cached.get("ts", 0) > COLLECTION_CACHE_TTL:
                self._update_vectors_count_cache(name)
                c["vectors_count"] = self._vectors_count_cache[name]["count"]
        return self._collections_cache or []

    # -----------------------------
    # Vector operations
    # -----------------------------
    def upsert(self, collection: str, ids: List[str], vectors: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        if not ids or not vectors or len(ids) != len(vectors):
            raise ValueError("IDs and vectors must be non-empty and of equal length.")
        if len(metadatas) != len(ids):
            raise ValueError("Metadatas length must match IDs length.")

        self.create_collection_if_missing(collection, vector_size=len(vectors[0]))

        points = [
            qm.PointStruct(id=str(i), vector=v, payload=m)
            for i, v, m in zip(ids, vectors, metadatas)
        ]
        self.client.upsert(collection_name=collection, points=points)

        self._update_vectors_count_cache(collection)
        self._collections_cache = None

    def search_by_vector(
        self,
        vector: List[float],
        collection: Optional[str] = None,
        top_k: int = 5,
        filter: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        coll = collection or self.default_collection
        self.create_collection_if_missing(coll, vector_size=len(vector))

        filter_obj = None
        if filter:
            if isinstance(filter, dict):
                must_conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter.items()
                ]
                filter_obj = Filter(must=must_conditions)
            elif isinstance(filter, Filter):
                filter_obj = filter
            else:
                raise ValueError(f"Invalid filter type: {type(filter)}. Must be dict or qdrant_client.models.Filter.")

        results = self.client.search(
            collection_name=coll,
            query_vector=vector,
            limit=top_k,
            query_filter=filter_obj
        )

        return [{"id": h.id, "score": h.score, "payload": h.payload} for h in results]
    
    def point_exists(self, collection: str, point_id: str) -> bool:
        try:
            pt = self.client.get_point(collection_name=collection, id=str(point_id))
            return pt is not None
        except Exception:
            return False
