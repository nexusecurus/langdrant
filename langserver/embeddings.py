"""
embeddings.py

Handles:
- Text embeddings via Ollama API
- Query embeddings for vector search
- LLM prompt generation with n8n-ready output
- Robust retry logic and JSON/JSONL parsing
"""

import time
import json
from typing import List, Dict
import httpx
from schemas import GenerateResponse
import defaults as cfg


# -----------------------------
# Internal Ollama request helper
# -----------------------------
def _ollama_request(endpoint: str, payload: dict, timeout: int = 60) -> dict:
    for attempt in range(cfg.OLLAMA_RETRY_COUNT):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(f"{cfg.OLLAMA_BASE_URL}{endpoint}", json=payload)
                response.raise_for_status()

                text = response.text.strip()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    first_line = text.split("\n")[0]
                    return json.loads(first_line)

        except Exception as e:
            if attempt < cfg.OLLAMA_RETRY_COUNT - 1:
                time.sleep(cfg.OLLAMA_RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"Ollama request failed after {cfg.OLLAMA_RETRY_COUNT} attempts: {e}"
                )


# -----------------------------
# Embeddings
# -----------------------------
def embed_texts(texts: List[str], model: str = None, num_ctx: int = None) -> List[List[float]]:
    model = model or cfg.EMBED_MODEL
    embeddings = []

    for text in texts:
        payload = {
            "model": model,
            "prompt": text,
            "num_ctx": num_ctx or cfg.LLM_CTX
        }
        res = _ollama_request("/api/embeddings", payload)

        try:
            emb = res["embedding"]
            if not emb:
                raise ValueError(f"Empty embedding returned for text: {text}")
        except KeyError:
            raise ValueError(f"Invalid response from Ollama embeddings API: {res}")

        embeddings.append(emb)

    return embeddings


def embed_query(query: str, model: str = None, num_ctx: int = None) -> List[float]:
    return embed_texts([query], model=model, num_ctx=num_ctx)[0]


# -----------------------------
# LLM generation (CHAT Stream)
# -----------------------------
def stream_completion(prompt: str, model: str = None, max_tokens: int = None, num_ctx: int = None):
    model = model or cfg.LLM_MODEL
    max_tokens = max_tokens or cfg.LLM_MAX_TOKENS

    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "num_ctx": num_ctx or cfg.LLM_CTX,
        "stream": True
    }

    buffer = ""

    with httpx.Client(timeout=None) as client:
        with client.stream("POST", f"{cfg.OLLAMA_BASE_URL}/api/generate", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    j = json.loads(line)
                    chunk = j.get("response", "")
                    if not chunk:
                        continue

                    buffer += chunk
                    if buffer.endswith((" ", ".", "?", "!", ",", ";", ":")):
                        yield buffer
                        buffer = ""
                except Exception:
                    continue

    if buffer:
        yield buffer


# -----------------------------
# LLM generation (RAG)
# -----------------------------
def generate_completion(prompt: str, model: str = None, max_tokens: int = None,
                        num_ctx: int = None, n8n_ready: bool = False) -> str:
    model = model or cfg.LLM_MODEL
    max_tokens = max_tokens or cfg.LLM_MAX_TOKENS

    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "num_ctx": num_ctx or cfg.LLM_CTX,
        "stream": False
    }

    res = _ollama_request("/api/generate", payload, timeout=120)

    if "choices" in res and len(res["choices"]) > 0:
        texts = []
        for choice in res["choices"]:
            if "message" in choice and "content" in choice["message"]:
                texts.append(choice["message"]["content"])
            elif "content" in choice:
                texts.append(choice["content"])
        full_text = "\n".join(texts)
    elif "response" in res:
        full_text = str(res["response"])
    elif "output" in res:
        full_text = "\n".join(map(str, res["output"])) if isinstance(res["output"], list) else str(res["output"])
    else:
        full_text = str(res)

    if n8n_ready:
        summary, canonical = "", ""
        try:
            j = json.loads(full_text)
            summary = j.get("summary", "")
            canonical = j.get("canonical_embedding_text", "")
        except json.JSONDecodeError:
            lines = full_text.splitlines()
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if "summary" in line_lower and not summary:
                    if i + 1 < len(lines):
                        summary = lines[i + 1].strip()
                if "canonical" in line_lower and not canonical:
                    if i + 1 < len(lines):
                        canonical = lines[i + 1].strip()

        summary = summary or "No summary generated."
        canonical = canonical or "No canonical_embedding_text generated."
        return GenerateResponse(summary=summary, canonical_embedding_text=canonical).dict()

    return full_text
