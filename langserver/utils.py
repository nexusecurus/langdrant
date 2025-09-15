
import os
import io
from fastapi import Header, HTTPException
from dotenv import load_dotenv
import docx
from bs4 import BeautifulSoup
from pypdf import PdfReader
import re

load_dotenv()

# -------------------------
# API Key Enforcement
# -------------------------
def require_api_key(x_api_key: str = Header(None)):

    env_key = os.getenv("API_KEY")
    if env_key and x_api_key != env_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

# -------------------------
# File Parsing
# -------------------------
def parse_file_to_text(content: bytes, filename: str) -> str:

    name = filename.lower()

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        return "\n\n".join([page.extract_text() or "" for page in reader.pages])

    if name.endswith(".docx"):
        doc = docx.Document(io.BytesIO(content))
        return "\n\n".join([p.text for p in doc.paragraphs])

    if name.endswith(".html") or name.endswith(".htm"):
        soup = BeautifulSoup(content, "html.parser")
        return soup.get_text(separator="\n")

    # Default fallback: decode as UTF-8
    return content.decode("utf-8", errors="ignore")

# -------------------------
# Text Helpers
# -------------------------
def clean_text(text: str) -> str:

    text = text.strip()
    text = re.sub(r'\n+', '\n', text)
    return text


def split_lines_to_chunks(lines: list, chunk_size: int = 100) -> list:

    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk = "\n".join(lines[i:i + chunk_size])
        chunks.append(chunk)
    return chunks
