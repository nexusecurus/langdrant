# <p align="center"> LangChain-Qdrant Multi-Source API </p>

<p align="center">developed by NexuSecurus&trade;</p> 


<div style="text-align:center">
    <img align="center" src="images/logo.png" alt="Project Logo">
</div>

<br>

<p align="center">
  <table>
    <tr>
      <th>Supported HW</th>
      <th>Target OS</th>
      <th>Code Stats</th>
      <th>Audience</th>
      <th>Type</th>
      <th>Dependencies</th>
      <th>License</th>
    </tr>
    <tr>
      <td><img src="https://img.shields.io/badge/Architecture-x86_64%20%7C%20ARM-blue?"></td>
      <td>
        <img src="https://img.shields.io/badge/Windows-10%2B-lightblue?logo=windows">
        <img src="https://img.shields.io/badge/Linux-Used-yellow?logo=linux">
        <img src="https://img.shields.io/badge/macOS-12%2B-lightgrey?logo=apple">
      </td>
      <td><img src="https://img.shields.io/badge/Python-3.11-green?logo=python"></td>
      <td><img src="https://img.shields.io/badge/AI-Developers-%23197aaa?logo=fastapi&logoColor=white"></td>
      <td><img src="https://img.shields.io/badge/API-Server-brightyellow?logo=fastapi"></td>
      <td><img src="https://img.shields.io/badge/LangChain-Latest-blue?logo=openai"></td>
      <td><img src="https://img.shields.io/badge/License-MIT-blue.svg"></td>
    </tr>
    <tr>
      <td><img src="https://img.shields.io/badge/CrossPlatform-Architecture-blue"></td>
      <td>
        <img src="https://img.shields.io/badge/Shell-Used-yellow?logo=linux">
        <img src="https://img.shields.io/badge/Poweshell-10%2B-lightblue?logo=windows">
      </td>
      <td><img src="https://img.shields.io/badge/FastAPI-Used-yellow?logo=fastapi"></td>
      <td><img src="https://img.shields.io/badge/Qdrant-VectorDB-purple"></td>
      <td><img src="https://img.shields.io/badge/Docker-Compose-blue?logo=docker"></td>
      <td><img src="https://img.shields.io/badge/Ollama-Latest-blue?logo=openai"></td>

    </tr>
  </table>
</p>


<br>

# Table of Contents

- [ LangChain-Qdrant Multi-Source API ](#-langchain-qdrant-multi-source-api-)
- [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Features](#features)
  - [Program Requirements / Prerequisites](#program-requirements--prerequisites)
    - [Hardware](#hardware)
    - [Software](#software)
  - [Installation](#installation)
    - [Clone the repository](#clone-the-repository)
    - [Environment configuration](#environment-configuration)
    - [Docker Compose (RECOMMENDED)](#docker-compose-recommended)
    - [Python (Run Locally)](#python-run-locally)
  - [API Endpoints](#api-endpoints)
    - [\> For a full detailed description of all API endpoints, request/response examples, default values, and n8n integration examples, please check ENDPOINTS.md.](#-for-a-full-detailed-description-of-all-api-endpoints-requestresponse-examples-default-values-and-n8n-integration-examples-please-check-endpointsmd)
    - [LLM Generation](#llm-generation)
    - [Ingestion Endpoints](#ingestion-endpoints)
    - [Semantic Search](#semantic-search)
    - [Collections](#collections)
    - [Debug Endpoints](#debug-endpoints)
    - [Health](#health)
  - [Contributing](#contributing)
  - [License](#license)
  - [References](#references)


## <p align="center">Description</p>

<p align="center"> Langdrant is an open-source API backend for semantic document search, powered by Qdrant and modern embedding models. Easily ingest, embed, and search your documents with a simple REST API. Perfect for building AI-powered search, knowledge bases, and more. A <strong>high-performance FastAPI</strong> server for multi-source data ingestion, semantic search, and LLM-powered query generation. It integrates <strong>Qdrant</strong> as the vector database and <strong>Ollama</strong> for embeddings and LLM completions.</p> 
<p align="center">Supports asynchronous ingestion, streaming responses, and structured <strong>n8n-ready</strong> outputs.</p>


## Features

- **Multi-source ingestion**
  - Generic text
  - Files: PDF, DOCX, HTML, TXT
  - Logs
  - Database rows (PostgreSQL)
  - RSS feeds
  - Social media posts
- **Vector search**
  - Semantic search with optional LLM-based context
  - Hybrid queries (vector similarity + keyword filters)
  - Multi-collection search
- **LLM generation**
  - Context-aware completions
  - n8n-ready structured responses (`summary` and `canonical_embedding_text`)
  - Streaming responses via SSE for conversational endpoints
- **Collection management**
  - List collections with vector counts
  - Delete collections safely
- **Debug endpoints**
  - Text chunk preview
  - Embedding inspection
- **Security**
  - API key enforcement for all endpoints
- **Deployment-ready**
  - Dockerized with FastAPI & Uvicorn
  - Configurable via `.env`
  - Multi-worker async ingestion

---

## Program Requirements / Prerequisites

### Hardware
- CPU: x86_64 or ARM architecture
- RAM: Minimum 4GB (8GB recommended for optimal performance)
- Disk: Minimum 10GB free space
- Internet connection: Required for fetching dependencies, accessing APIs, and pulling container images
- Ollama Instance with available models (Local or Remote)

### Software
- **Git**: Required to clone the repository and manage version control  
  ```bash
  sudo apt install git  # Linux
  brew install git      # macOS
  ```
- **Python 3.11+**: Required for running locally or for building Docker images
  ```bash
  python3 --version
  ```
- **pip**: Python package manager to install dependencies
- **Docker**: Required for containerized deployment
  ```bash
  docker --version
  ```
- **Docker Compose**: For multi-container orchestration
  ```bash
  docker compose version
  ```
- **PostgreSQL** client libraries: Required if you intend to use database ingestion endpoints (psycopg2-binary included in Python dependencies)
- Optional system packages for file ingestion (PDF/DOCX/HTML parsing, OCR):
    - poppler-utils (PDF text extraction)
    - libreoffice (DOCX conversion, optional)
    - tesseract-ocr (OCR for scanned documents)

- **cURL or HTTP** client for testing API endpoints
- **jq** (optional) make json output prettier and more readable.
- **n8n** (optional) for automation workflows and connecting ingestion + query endpoints

---

## Installation

### Clone the repository

```bash
git clone https://github.com/nexusecurus/langdrant.git
cd langdrant
```

### Environment configuration


Copy the `.env.example` to `.env` and configure your environment:

```bash
cp .env.example .env
```

Auto Generate API Key (Optional):

```bash
python3 langserver/api-generator.py
```
> This will generate an API_KEY and update it under `.env` file automatically.


Customize variables to your preference:


```bash
nano .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API key for FastAPI endpoints | `""` |
| `API_PORT` | FastAPI port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `QDRANT_URL` | Qdrant server URL | `http://127.0.0.1:6333` |
| `QDRANT_API_KEY` | Optional Qdrant API key | `""` |
| `VECTOR_SIZE` | Embedding vector size | `1536` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://127.0.0.1:11434` |
| `EMBED_MODEL` | Ollama embedding model | `nomic-embed-text` |
| `LLM_MODEL` | Ollama LLM model | `llama3:8b` |
| `LLM_CTX` | LLM context window | `4096` |
| `LLM_MAX_TOKENS` | Max tokens per generation | `300` |
| `DB_HOST/PORT/NAME/USER/PASSWORD` | PostgreSQL connection | - |
| `CHUNK_SIZE` | Text chunk size | `800` |
| `CHUNK_OVERLAP` | Overlap per chunk | `120` |
| `EMBED_BATCH_SIZE` | Batch size for embedding | `64` |

### Docker Compose (RECOMMENDED)

```bash
docker compose build --no-cache
docker compose pull
docker compose up -d
```

### Python (Run Locally)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd langserver
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## API Endpoints

### > For a full detailed description of all API endpoints, request/response examples, default values, and n8n integration examples, please check [ENDPOINTS.md](ENDPOINTS.md).

### LLM Generation

```http
POST /generate
POST /chat
```

- Generate text using an LLM model. Returns structured n8n-ready data (summary and canonical_embedding_text). Use model, max_tokens, and num_ctx to override defau
- Conversational endpoint. Accepts a list of messages. Supports streaming mode via SSE. Returns assistant response. Flags: model, max_tokens, num_ctx, stream.


### Ingestion Endpoints

**Async ingestion of multiple data sources:**

```http
POST /ingest_texts       # Generic text
POST /ingest_file        # File upload
POST /ingest_logs        # Logs
POST /ingest_db          # Database rows
POST /ingest_rss         # RSS feeds
POST /ingest_social      # Social posts
POST /fetch_rss_feeds    # Fetch and ingest RSS feeds
```

- Supports **deterministic ID generation** for deduplication
- Text is **chunked** with configurable size and overlap
- **Batch embedding and upsert** into Qdrant
- Preserves **full metadata** (source, timestamp, platform, etc.)


### Semantic Search

```http
POST /query              # Single collection
POST /query_hybrid       # Hybrid semantic + keyword filters
POST /query_multi        # Multi-collection search
```

- Returns top-K nearest vectors
- Optional LLM answer generation from retrieved context
- Keyword filters, recency boosts, and hybrid queries supported


### Collections

```http
GET /collections
POST /collections/delete
```

- List collections with vector counts
- Delete collection safely


### Debug Endpoints

```http
POST /debug/chunk
POST /debug/embeds
```

- Preview how text is chunked
- Inspect embeddings before insertion


### Health

```http
GET /health
GET /ping
```

- Returns server status.

---

## Contributing

1. Fork the repository
2. Create your feature branch
3. Submit pull requests with clear descriptions
4. Ensure all new endpoints have tests and documentation

---

## License

[MIT License](LICENSE)

---

## References

- [FastAPI](https://fastapi.tiangolo.com/)
- [Qdrant](https://qdrant.tech/)
- [LangChain](https://www.langchain.com/)
- [Ollama API](https://ollama.com/)
