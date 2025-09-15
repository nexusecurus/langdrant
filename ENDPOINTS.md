# LangChain-Qdrant API — Endpoints Manual

This document describes **all available endpoints** in the LangChain-Qdrant API server, their **parameters**, **default values**, and **example requests**.  
It is meant as a **developer-facing manual** for direct usage or integration (e.g., with `curl`, `Postman`, or automation tools like **N8N**).

---


## Authentication

All endpoints (except `/health` and `/ping`) require an **API key**.  
Include it in the request header:

```bash
-H "x-api-key: $API_KEY"
```

The `$API_KEY` value is configured in your `.env` file:

```env
API_KEY=your_custom_long_api_key
```


## Extra notes

> The following commands assume you are running them locally, if running them remotely change `localhost` to ip of the host running **Langdrant**

> Same with port, if you change the port under `.env`, please update the commands to reflect it.


---


# Endpoints

## 1. `/generate` — LLM Embedding Text Generation for N8N

Generate text completions using the configured Ollama model based on data provided from previous nodes.

⚠️ Important: This endpoint only works reliably if the prompt explicitly instructs the model to output a valid JSON object with the keys:



```makefile
Generate a JSON object with exactly these keys:
{
  "summary": "One concise human-readable sentence about the entity ExampleApp",
  "canonical_embedding_text": "ExampleApp|ACTIVE|3|us-east-1|web|v2"
}

Entity Data:
name: ExampleApp
status: ACTIVE
node_count: 3
region: us-east-1
role: web
version: 2

Respond strictly in JSON with only keys summary and canonical_embedding_text.

```
> Without this instruction, many models will fail or hallucinate responses.

> For this endpoint `**gpt-oss models**` are the recommended ones.

**Method:** `POST`  
**Auth required:** `YES`


### Request Schema
 
| Variable     |  Required\*   | Default             | Override | Type   | Description                                                                   |
| ------------ | ------------  | ------------------- | -------- | ------ | ----------------------------------------------------------------------------- |
| `prompt`     | **YES**       | —                   |    —     | `str`  | Actual prompt to the AI. Must instruct the model to return strict JSON.       |
| `model`      | **Optional**  | `${LLM_MODEL}`      | **YES**  | `str`  | Ollama model to be used (e.g., `gpt-oss:20b`, `llama3:8b`).                   |
| `max_tokens` | **Optional**  | `${LLM_MAX_TOKENS}` | **YES**  | `int`  | Maximum number of tokens in the response.                                     |
| `num_ctx`    | **Optional**  | `${LLM_CTX}`        | **YES**  | `int`  | Context window size (how much text the model can attend to).                  |
| `stream`     | **Optional**  | `False`             | **YES**  | `bool` | Whether to stream responses (SSE). Currently not used in this implementation. |



\* Values can be override by user, if user dont provide them, defaults are used from `.env` file.

### Examples

**Minimal:**  
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "prompt": "Generate a JSON object with the following keys for the cluster data:\n\n{\n  \"summary\": \"One concise human-readable paragraph summarizing the cluster\",\n  \"canonical_embedding_text\": \"cluster_name|status_code|node_count|datacenter_id|cluster_type_id|version\"\n}\n\nCluster Data:\ncluster_name: nexusecurus\nstatus: ACTIVE\nnode_count: 5\ndatacenter_id: 1\ncluster_type_id: 1\nextra_vars: {\"version\":9,\"id\":\"cluster\"}\ntags: entity:cluster, cluster:nexusecurus, status:active, nodes:5, dc:1, ctype:1\nsource: {\"system\":\"postgres\",\"table\":\"brain.inf_cluster_data\",\"primary_key\":{\"cluster_name\":\"nexusecurus\"},\"updated_at\":\"2025-09-13T00:10:10.737Z\"}\nai_summary: Cluster \"nexusecurus\" is active with 5 node(s). Datacenter ID: 1. Cluster Type ID: 1. Extra: version=9, id=cluster\nembedding_text: ...\ncontent_hash: b2ede957\nupdated_at: 2025-09-13T00:10:10.737Z\n\nRespond strictly in JSON with only keys \"summary\" and \"canonical_embedding_text\". No explanations, no extra text."
  }'

```

**Override model, token limit, context size and streaming:**  
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -H "x-api-key: 173a58eb0d771bf3f28c464c3d7121adca4f377d214062dbeb24065dd97e96c0" \
  -d '{
    "model": "llama3:8b",
    "max_tokens": 2048,
    "num_ctx": 8192,
    "stream": false,
    "prompt": "Generate a JSON object with the following keys for the given Proxmox cluster data:\n\n{\n  \"summary\": \"One concise human-readable paragraph summarizing the cluster\",\n  \"canonical_embedding_text\": \"cluster_name|status_code|node_count|datacenter_id|cluster_type_id|version\"\n}\n\nCluster Data:\ncluster_name: nexusecurus\nstatus: ACTIVE\nnode_count: 5\ndatacenter_id: 1\ncluster_type_id: 1\nextra_vars: {\"version\":9,\"id\":\"cluster\"}\ntags: entity:cluster, cluster:nexusecurus, status:active, nodes:5, dc:1, ctype:1\nsource: {\"system\":\"postgres\",\"table\":\"brain.inf_cluster_data\",\"primary_key\":{\"cluster_name\":\"nexusecurus\"},\"updated_at\":\"2025-09-13T00:10:10.737Z\"}\nai_summary: Cluster \"nexusecurus\" is active with 5 node(s). Datacenter ID: 1. Cluster Type ID: 1. Extra: version=9, id=cluster\nembedding_text: ...\ncontent_hash: b2ede957\nupdated_at: 2025-09-13T00:10:10.737Z\n\nRespond strictly in JSON with only keys \"summary\" and \"canonical_embedding_text\". No explanations, no extra text."
  }'


```

**Expected Output**

```json
{
  "response": {
    "summary": "The Proxmox cluster *nexusecurus* is currently active, consisting of five nodes located in datacenter one. It is classified as cluster type one and runs version nine of the cluster software.",
    "canonical_embedding_text": "nexusecurus|ACTIVE|5|1|1|9"
  }
}
```

---

## 2. `/chat` — Conversational API

Simulates a multi-turn chat. Supports streaming (SSE).

**Method:** `POST`  
**Auth required:** ✅ Yes


### Request Schema

|   Variable  |     Required\*   |       Default       |    Override  |     Type    |                   Description                 |  
|-------------|------------------|---------------------|--------------|-------------|-----------------------------------------------|
|  `messages` |     **YES**      |       `none`        |       —      |    `str`    | Chat history, list of {role, content} objects |
|   `model`   |   **Optional**   |   `${LLM_MODEL}`    |    **YES**   |    `str`    |              Ollama Model to use              |
| `max_tokens`|   **Optional**   | `${LLM_MAX_TOKENS}` |    **YES**   |    `int`    |             Max Tokens for response           |
|  `num_ctx`  |   **Optional**   |    `${LLM_CTX}`     |    **YES**   |    `int`    |          Context Size / CTX Windows Size      |
|   `stream`  |   **Optional**   |   `${LLM_STREAM}`   |    **YES**   |    `bool`   |     Enable Server-Sent Events (streaming)     |


\* Values can be override by user, if user dont provide them, defaults are used from `.env` file.

### Examples

**Non-streaming (default):**  
```bash
curl -X POST http://localhost:8000/chat \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

```

**Override model:**  
```bash
-d '{"messages":[{"role":"user","content":"Tell me a joke"}],"model":"gpt-oss:20b"}'
```

**Override max_tokens:**  
```bash
-d '{"messages":[{"role":"user","content":"Tell me a joke"}],"max_tokens":500}'
```

**Override num_ctx:**  
```bash
-d '{"messages":[{"role":"user","content":"Tell me a joke"}],"num_ctx":8192}'
```

**Streaming Enabled:**  
```bash
-d '{"messages":[{"role":"user","content":"Tell me a joke"}],"stream":true}'
```

**All Flags:**  
```bash
-d '{"messages":[{"role":"user","content":"Tell me a joke"}],"model":"gpt-oss:20b","max_tokens":2000,"num_ctx":8192,"stream":true}'
```

**Expected Outputs**

#### With Streaming/SSE Disabled
```json
{
  "response": "Why did the scarecrow win an award? Because he was outstanding in his field!"
}


```
#### With Streaming/SSE Enabled
```bash
data: Why did the scarecrow win an award?
data: 
data: Because he was outstanding in his field!

data: [DONE]

```

---

## 3. `/ingest_texts` — Direct Text Ingestion

Ingests raw text, automatically **chunks → embeds → stores in Qdrant**.  

👉 You **DO NOT** need to pre-embed manually.

**Method:** `POST`  
**Auth required:** ✅ Yes


### Request Schema

| Variable   |  Required\*  | Default        | Override | Type             | Description                                      |
| ---------- | ------------ | -------------- | -------- | ---------------- | ------------------------------------------------ |
| `id`       | **Optional** | auto-generated | **YES**  | `str`            | Unique ID, generated if not provided             |
| `text`     | **YES**      |       —        |    —     | `str`            | The actual text content to store                 |
| `metadata` | **Optional** |`{}`            | **YES**  | `Dict[str, Any]` | **Optional**tadata dictionary for structured data |

\* Values can be override by user, if user dont provide them, defaults are used from `.env` file.


### Examples

**Minimal request (single item, default collection):**
```bash
curl -X POST http://localhost:8000/ingest_texts \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "items": [
          {"text": "This is a sample text to ingest."}
        ]
      }'
```

**Full request with collection and metadata:**

```bash
curl -X POST http://localhost:8000/ingest_texts \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "collection": "my_custom_collection",
        "items": [
          {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "text": "This is a test with metadata.",
            "metadata": {"source": "n8n workflow", "tags": ["test", "sample"]}
          }
        ]
      }'

```
**Expected Outputs**


**Successful ingestion:**

```json
{
  "ok": true,
  "collection": "my_custom_collection",
  "count": 1
}
```

---

## 4. `/ingest_file` — File Ingestion

Uploads and ingests a document (PDF, DOCX, TXT, etc.).  
It will be **chunked, embedded, and stored**.

**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema

| Variable        | Required\*  | Default                 | Override | Type   | Description                                                  |
| --------------- | ----------  | ----------------------- | -------- | ------ | ------------------------------------------------------------ |
| `file`          | **YES**     | —                       | —        | `file` | The file to ingest (text, CSV, PDF, etc.).                   |
| `collection`    | **Optional**| `${DEFAULT_COLLECTION}` | **YES**  | `str`  | Target Qdrant collection for the ingested chunks.            |
| `chunk_size`    | **Optional**| `${CHUNK_SIZE}`         | **YES**  | `int`  | Number of characters per chunk.                              |
| `chunk_overlap` | **Optional**| `${CHUNK_OVERLAP}`      | **YES**  | `int`  | Number of overlapping characters between consecutive chunks. |


### Examples

**Minimal curl (default chunking, default collection):**

```bash
curl -X POST http://localhost:8000/ingest_file \
  -H "x-api-key: YOUR_API_KEY" \
  -F "file=@/path/to/my_file.txt"

```

**With custom collection and chunking:**

```bash
curl -X POST http://localhost:8000/ingest_file \
  -H "x-api-key: YOUR_API_KEY" \
  -F "file=@/path/to/my_file.txt" \
  -F "collection=my_custom_collection" \
  -F "chunk_size=500" \
  -F "chunk_overlap=50"

```

**Expected Outputs:**

```json
{
  "ok": true,
  "collection": "my_custom_collection",
  "count": 1
}

```
---

## 5. `/ingest_logs` — Log File Ingestion

Optimized for structured/unstructured logs.  

**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema

| Variable     | Required\*  | Default                 | Override | Type   | Description                                         |
| ------------ | ----------- | ----------------------- | -------- | ------ | --------------------------------------------------- |
| `collection` | **Optional**| `${DEFAULT_COLLECTION}` | **YES**  | `str`  | Target Qdrant collection for the ingested logs.     |
| `logs`       | **YES**     | —                       | —        | `list` | List of log entries to ingest (`LogEntry` objects). |


### `LogEntry` Object

| Variable    | Required\*  | Default       |   Type   | Description                                         |
| ----------- | ----------- | ------------- | -------- | --------------------------------------------------- |
| `id`        | **Optional**| autogenerated |   `str`  | Unique log entry ID; auto-generated if missing.     |
| `timestamp` | **YES**     | autogenerated |   `str`  | ISO8601 timestamp of the log entry.                 |
| `vm_id`     | **YES**     | —             |   `str`  | Identifier for the VM or system generating the log. |
| `log_level` | **Optional**| `"INFO"`      |   `str`  | Log level (INFO, WARN, ERROR, etc.).                |
| `message`   | **YES**     | —             |   `str`  | Actual log message text.                            |
| `metadata`  | **Optional**| `{}`          |  `dict`  | Additional metadata associated with the log entry.  |


### Examples

**Minimal curl (default collection):**

```bash
curl -X POST http://localhost:8000/ingest_logs \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      {
        "vm_id": "vm01",
        "message": "System started successfully.",
        "timestamp": "2025-09-15T12:00:00Z"
      }
    ]
  }'

```

**With custom collection and extra metadata:**

```bash
curl -X POST http://localhost:8000/ingest_logs \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "vm_logs",
    "logs": [
      {
        "id": "log-123",
        "vm_id": "vm01",
        "log_level": "ERROR",
        "message": "Disk space critically low.",
        "timestamp": "2025-09-15T12:05:00Z",
        "metadata": {"datacenter": "dc1", "environment": "prod"}
      }
    ]
  }'

```

**Expected Outputs:**

```json
{
  "ok": true,
  "collection": "vm_logs",
  "count": 1
}

```

---

## 6. `/ingest_db` — Database Row Ingestion

Pulls rows from PostgreSQL, embeds and stores them.


**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema

| Variable     |  Required\* | Default                 | Override | Type   | Description                                        |
| ------------ | ----------- | ----------------------- | -------- | ------ | -------------------------------------------------- |
| `collection` | **Optional**| `${DEFAULT_COLLECTION}` | **YES**  | `str`  | Target Qdrant collection for the ingested rows.    |
| `rows`       | **YES**     | —                       | —        | `list` | List of database rows to ingest (`DBRow` objects). |

### DBRow Object

| Field      |  Required\* | Default       | Type   | Description                                                |
| ---------- | ----------- | ------------- | ------ | ---------------------------------------------------------- |
| `id`       | **Optional**| autogenerated | `str`  | Unique ID for the row; auto-generated if missing.          |
| `table`    | **YES**     | —             | `str`  | Name of the database table.                                |
| `row_data` | **YES**     | —             | `dict` | Dictionary containing column names and values for the row. |
| `metadata` | **Optional**| `{}`          | `dict` | Extra metadata to associate with this row.                 |



### Examples

**Minimal curl (default collection):**

```bash
curl -X POST http://localhost:8000/ingest_db \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "rows": [
      {
        "table": "users",
        "row_data": {"id": 1, "name": "Alice", "email": "alice@example.com"}
      }
    ]
  }'

```

**With custom collection and metadata:**

```bash
curl -X POST http://localhost:8000/ingest_db \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "db_users",
    "rows": [
      {
        "id": "row-001",
        "table": "users",
        "row_data": {"id": 1, "name": "Alice", "email": "alice@example.com"},
        "metadata": {"environment": "prod", "region": "us-east-1"}
      }
    ]
  }'

```

**Expected Outputs:**

```json
{
  "ok": true,
  "collection": "db_users",
  "count": 1
}

```

---

## 7. `/ingest_rss` — RSS Feed Ingestion

Ingests RSS or news articles into Qdrant for semantic search. Supports chunking of article content for embeddings.

**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema

| Variable     |  Required\* | Default                 | Override | Type   | Description                                            |
| ------------ | ----------- | ----------------------- | -------- | ------ | ------------------------------------------------------ |
| `collection` | **Optional**| `${DEFAULT_COLLECTION}` | **YES**  | `str`  | Target Qdrant collection for the ingested articles.    |
| `articles`   | **YES**     | —                       | —        | `list` | List of RSS articles to ingest (`RSSArticle` objects). |


### RSSArticle Object

| Variable       |  Required\* | Default                                                |  Type  | Description                                    |
| -------------- | ----------- | ------------------------------------------------------ | ------ | ---------------------------------------------- |
| `id`           | **Optional**| autogenerated (deterministic from URL + published\_at) | `str`  | Unique ID for the article.                     |
| `url`          | **YES**     | —                                                      | `str`  | URL of the article.                            |
| `title`        | **YES**     | —                                                      | `str`  | Article title.                                 |
| `content`      | **YES**     | —                                                      | `str`  | Full text content of the article.              |
| `published_at` | **Optional**| current timestamp                                      | `str`  | Publication timestamp of the article.          |
| `metadata`     | **Optional**| `{}`                                                   | `dict` | Extra metadata to associate with this article. |


### Examples

**Minimal curl (default collection):**

```bash
curl -X POST http://localhost:8000/ingest_rss \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "url": "https://example.com/news/123",
        "title": "New Product Launch",
        "content": "Our company has launched a new product today..."
      }
    ]
  }'

```

**With custom collection and metadata:**

```bash
curl -X POST http://localhost:8000/ingest_rss \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "rss_news",
    "articles": [
      {
        "id": "article-001",
        "url": "https://example.com/news/123",
        "title": "New Product Launch",
        "content": "Our company has launched a new product today...",
        "published_at": "2025-09-15T00:00:00Z",
        "metadata": {"category": "product", "region": "us-east-1"}
      }
    ]
  }'

```

**Expected Output:**

```json
{
  "ok": true,
  "collection": "rss_news",
  "count": 1
}

```


---

## 8. `/ingest_social` — Social Media Ingestion

For ingesting social media posts (schema defined in `schemas.py`).

**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema

| Variable     |  Required\* | Default                 | Override | Type   | Description                                                  |
| ------------ | ----------- | ----------------------- | -------- | ------ | ------------------------------------------------------------ |
| `collection` | **Optional**| `${DEFAULT_COLLECTION}` | **YES**  | `str`  | Target Qdrant collection for the ingested posts.             |
| `posts`      | **YES**     | —                       | —        | `list` | List of social media posts to ingest (`SocialPost` objects). |


### SocialPost Object

| Field       |  Required\* | Default            | Type   | Description                                  |
| ----------- | ----------- | ------------------ | ------ | -------------------------------------------- |
| `id`        | **Optional**| autogenerated UUID | `str`  | Unique ID for the post.                      |
| `platform`  | **YES**     | —                  | `str`  | Platform name (e.g., "twitter", "mastodon"). |
| `user_id`   | **YES**     | —                  | `str`  | User ID of the post author.                  |
| `post_id`   | **YES**     | —                  | `str`  | Platform-specific post ID.                   |
| `content`   | **YES**     | —                  | `str`  | Full text content of the post.               |
| `timestamp` | **Optional**| current timestamp  | `str`  | Time when the post was published.            |
| `metadata`  | **Optional**| `{}`               | `dict` | Extra metadata to associate with this post.  |


### Examples

**Minimal curl (default collection):**

```bash
curl -X POST http://localhost:8000/ingest_social \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [
      {
        "platform": "twitter",
        "user_id": "user123",
        "post_id": "tweet456",
        "content": "Hello world! This is my first tweet."
      }
    ]
  }'

```

**With custom collection and metadata:**

```bash
curl -X POST http://localhost:8000/ingest_social \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "social_posts",
    "posts": [
      {
        "id": "post-001",
        "platform": "mastodon",
        "user_id": "user456",
        "post_id": "masto789",
        "content": "Launching our new feature today!",
        "timestamp": "2025-09-15T12:00:00Z",
        "metadata": {"category": "announcement", "region": "eu-west-1"}
      }
    ]
  }'

```

**Expected Output:**

```json
{
  "ok": true,
  "collection": "social_posts",
  "count": 1
}

```

---

## 9. `/fetch_rss_feeds` — Background Fetch & Ingest

Fetches RSS/Atom feeds from provided URLs, parses the entries into articles, and ingests them into a Qdrant collection.

**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema
| Variable     |  Required\* | Default                 | Override | Type   | Description                                         |
| ------------ | ----------- | ----------------------- | -------- | ------ | --------------------------------------------------- |
| `urls`       | **YES**     | —                       | —        | `list` | List of RSS feed URLs to fetch and ingest.          |
| `collection` | **Optional**| `${DEFAULT_COLLECTION}` | **YES**  | `str`  | Target Qdrant collection for the ingested articles. |


### Examples

**Minimal curl (default collection):**

```bash
curl -X POST http://localhost:8000/fetch_rss_feeds \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/rss",
      "https://another-site.com/feed"
    ]
  }'
```

**With custom collection:**

```bash
curl -X POST http://localhost:8000/fetch_rss_feeds \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://technews.com/rss"],
    "collection": "rss_articles"
  }'

```

**Expected Output:**

```json
{
  "ok": true,
  "collection": "rss_articles",
  "count": 12
}
```


---

## 10. `/query` — Semantic Search

Performs a vector-based semantic search against the Qdrant store. **Optional**generates an LLM answer from the retrieved context.

**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema

| Variable      |  Required\* | Default                 | Override | Type   | Description                                             |
| ------------- | ----------- | ----------------------- | -------- | ------ | ------------------------------------------------------- |
| `query`       | **YES**     | —                       | —        | `str`  | Text query to search.                                   |
| `top_k`       | **Optional**| `5`                     | **YES**  | `int`  | Number of top results to return.                        |
| `collection`  | **Optional**| `${DEFAULT_COLLECTION}` | **YES**  | `str`  | Qdrant collection to search in.                         |
| `llm_model`   | **Optional**| `${LLM_MODEL}`          | **YES**  | `str`  | LLM model to generate an answer from retrieved results. |
| `embed_model` | **Optional**| `${EMBED_MODEL}`        | **YES**  | `str`  | Embedding model to convert query into a vector.         |
| `filters`     | **Optional**| `{}`                    | **YES**  | `dict` | Qdrant payload filters for narrowing search.            |
| `return_raw`  | **Optional**| `False`                 | **YES**  | `bool` | Whether to return raw vectors or formatted metadata.    |


### Example

**Minimal Example:**

```bash
curl -X POST http://localhost:8000/query \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"Find information about cluster nexusecurus"}'
```

**Full Example with All Flags:**

```bash
curl -X POST http://localhost:8000/query \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find information about cluster nexusecurus",
    "top_k": 10,
    "collection": "clusters",
    "llm_model": "gpt-oss:20b",
    "embed_model": "nomic-embed-text",
    "return_raw": true
  }'

```

**Expected Outputs:**

`Without llm_model`

```json
{
  "results": [
    {
      "id": "10fe9044-77d4-8b44-d0e7-bd30c8142a1d",
      "score": 0.82532704,
      "payload": {
        "source_type": "text",
        "chunk_index": 0,
        "snippet": "NexuSecurus cluster is online with 5 nodes."
      }
    },
    ...
  ]
}

```
`With llm_model`

```json
{
  "enriched": "**Key Points**\n\n- NexuSecurus Cluster: 5 nodes  \n- Location: Datacenter 1  \n- Software: Proxmox 9  ",
  "results": [
    {
      "id": "2607c0ae-7be1-59c7-41c7-f30292df9316",
      "score": 0.78636694,
      "payload": {
        "source": "n8n workflow",
        "tags": [
          "test",
          "sample"
        ],
        "source_type": "text",
        "chunk_index": 0,
        "snippet": "NexuSecurus Cluster has 5 nodes in datacenter 1, and uses proxmox version 9."
      }
    }
  ]
}

```

---

## 11. `/query_hybrid` — Hybrid Search

Hybrid vector + keyword search endpoint with **optional**M enrichment.


### Request Schema

| Variable            |  Required  | Default                | Override   | Type            | Description                                                                                                           |
| ------------------- | ---------- | ---------------------- | ---------- |  -------------- | --------------------------------------------------------------------------------------------------------------------- |
| `query`             |   **YES**  | —                      | —          | `str`           | The text query to embed and search against your Qdrant collections.                                                   |
| `top_k`             |**Optional**| 5                      | **YES**    | `int`           | Maximum number of results to return (after filtering and scoring).                                                    |
| `collections`       |**Optional**| `${DEFAULT_COLLECTION}`| **YES**    | `List[str]`     | Names of Qdrant collections to search. If omitted, defaults to the global default collection.                         |
| `llm_model`         |**Optional**| `${LLM_MODEL}`         | **YES**    | `str`           | LLM model to summarize or enrich the retrieved results. If omitted, no LLM processing is applied.                     |
| `embed_model`       |**Optional**| `${EMBED_MODEL}`       | **YES**    | `str`           | Embedding model to use for vectorization. Defaults to your configured embed model if omitted.                         |
| `keyword_filters`   |**Optional**| `{}`                   | **YES**    | `Dict[str,str]` | Filters applied to the `payload` of each Qdrant point. Values are matched case-insensitively.                         |
| `boost_recent_days` |**Optional**| `None`                 | **YES**    | `int`           | Number of days for recency boost. Entries with `published_at` timestamps within this window are prioritized.          |
| `return_raw`        |**Optional**| `False`                | **YES**    | `bool`          | If `True`, returns full Qdrant points (`id`, `score`, `payload`). If `False`, returns only the `payload`.             |


### Examples

**Minimal Request (just the query):**

```bash
curl -X POST http://localhost:8000/query_hybrid \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "query": "Find information about cluster nexusecurus"
      }'

```
  - Uses default top_k (5) and default collection.
  - No LLM enrichment, no keyword filters, no recency boost.


**Full Request with All Flags:**

```bash
curl -X POST http://localhost:8000/query_hybrid \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "query": "Find information about cluster nexusecurus",
        "top_k": 10,
        "collections": ["datacenter", "knowledge"],
        "llm_model": "gpt-oss:20b",
        "embed_model": "nomic-embed-text",
        "keyword_filters": {"source_type": "text"},
        "boost_recent_days": 30,
        "return_raw": true
      }'

```
  - top_k: limit the number of results after merging all collections.
  - collections: search multiple Qdrant collections.
  - llm_model: generate a concise summary of the retrieved results without hallucinating.
  - embed_model: override the default embedding model.
  - keyword_filters: filter payload fields for exact/case-insensitive substring matches.
  - boost_recent_days: favor points published within the last 30 days.
  - return_raw: include full Qdrant point data (id, score, payload) instead of just payloads.



**Expected Outputs:**

`Without llm:`

```json
{
  "query": "Find information about cluster nexusecurus",
  "collections": [
    "knowledge"
  ],
  "results": [
    {
      "source_type": "text",
      "chunk_index": 0,
      "snippet": "NexuSecurus cluster is online with 5 nodes."
    },
  ...
```

`With llm:`

```json
{
  "query": "Find information about cluster nexusecurus",
  "collections": ["datacenter", "knowledge"],
  "results": [
    {
      "id": "2607c0ae-7be1-59c7-41c7-f30292df9316",
      "score": 0.7863,
      "payload": {
        "source": "n8n workflow",
        "tags": ["test","sample"],
        "source_type": "text",
        "chunk_index": 0,
        "snippet": "NexuSecurus Cluster has 5 nodes in datacenter 1, and uses proxmox version 9."
      }
    }
  ],
  "answer": "**Key Points**\n\n- NexuSecurus Cluster: 5 nodes  \n- Location: Datacenter 1  \n- Software: Proxmox 9"
}

```

---

## 12. `/query_multi` — Multi-Collection Search

Search a single query across multiple Qdrant collections, **optional**summarize results via LLM.

**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema

| Variable            |  Required  | Default                | Override   | Type            | Description                                                                                                           |
| ------------------- | ---------- | ---------------------- | ---------- |  -------------- | --------------------------------------------------------------------------------------------------------------------- |
| `query`             |   **YES**  | —                      | —          | `str`           | The text query to embed and search against your Qdrant collections.                                                   |
| `top_k`             |**Optional**| 5                      | **YES**    | `int`           | Maximum number of results to return (after filtering and scoring).                                                    |
| `collections`       |**Optional**| `${DEFAULT_COLLECTION}`| **YES**    | `List[str]`     | Names of Qdrant collections to search. If omitted, defaults to the global default collection.                         |
| `llm_model`         |**Optional**| `${LLM_MODEL}`         | **YES**    | `str`           | LLM model to summarize or enrich the retrieved results. If omitted, no LLM processing is applied.                     |
| `embed_model`       |**Optional**| `${EMBED_MODEL}`       | **YES**    | `str`           | Embedding model to use for vectorization. Defaults to your configured embed model if omitted.                         |
| `keyword_filters`   |**Optional**| `{}`                   | **YES**    | `Dict[str,str]` | Filters applied to the `payload` of each Qdrant point. Values are matched case-insensitively.                         |
| `boost_recent_days` |**Optional**| `None`                 | **YES**    | `int`           | Number of days for recency boost. Entries with `published_at` timestamps within this window are prioritized.          |
| `return_raw`        |**Optional**| `False`                | **YES**    | `bool`          | If `True`, returns full Qdrant points (`id`, `score`, `payload`). If `False`, returns only the `payload`.             |



### Examples

**Minimal Request Example:**


```bash
curl -X POST http://localhost:8000/query_multi \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "query": "Find information about cluster nexusecurus",
        "collections": ["datacenter", "knowledge"]
      }'

```

**Full Request Example with Flags:**

```bash
curl -X POST http://localhost:8000/query_multi \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "query": "Find information about cluster nexusecurus",
        "collections": ["datacenter", "knowledge"],
        "top_k": 10,
        "llm_model": "gpt-oss:20b",
        "embed_model": "nomic-embed-text",
        "return_raw": true
      }'

```

**Expected Outputs:**

**Minimal Request Example:**

```json
{
  "results": [
    {
      "id": "10fe9044-77d4-8b44-d0e7-bd30c8142a1d",
      "score": 0.82532704,
      "payload": {
        "source_type": "text",
        "chunk_index": 0,
        "snippet": "NexuSecurus cluster is online with 5 nodes."
      },
      "collection": "knowledge"
    },
    {
      "id": "2607c0ae-7be1-59c7-41c7-f30292df9316",
      "score": 0.78636694,
      "payload": {
        "source": "n8n workflow",
        "tags": [
          "test",
          "sample"
        ],
        "source_type": "text",
        "chunk_index": 0,
        "snippet": "NexuSecurus Cluster has 5 nodes in datacenter 1, and uses proxmox version 9."
      },
      "collection": "datacenter"
    },
  ...
```

**Extra Flags Request Example:**

```json
{
  "results": [
    {
      "id": "10fe9044-77d4-8b44-d0e7-bd30c8142a1d",
      "score": 0.82532704,
      "payload": {
        "source_type": "text",
        "chunk_index": 0,
        "snippet": "NexuSecurus cluster is online with 5 nodes."
      },
      "collection": "knowledge"
    },
    {
      "id": "2607c0ae-7be1-59c7-41c7-f30292df9316",
      "score": 0.78636694,
      "payload": {
        "source": "n8n workflow",
        "tags": [
          "test",
          "sample"
        ],
        "source_type": "text",
        "chunk_index": 0,
        "snippet": "NexuSecurus Cluster has 5 nodes in datacenter 1, and uses proxmox version 9."
      },
      "collection": "datacenter"
    },
  ...
  "answer": "**Key Points from the Knowledge Base**\n\n- **NexuSecurus Cluster**\n  - Online with 5 nodes.\n  - All nodes are located in datacenter 1.\n  - Running Proxmox 9.\n  - System log entry: `[2025‑09‑15T12:00:00Z] ...
```

---

## 13. `/collections` — List Collections

Lists all collections stored in Qdrant database.

**Method:** `GET`  
**Auth required:** ✅ Yes

### Examples

```bash
curl -X GET http://localhost:8000/collections \
  -H "x-api-key: <API_KEY>"
```

**Expected Output:**

```json
{
  "collections": [
    {
      "name": "social_posts",
      "vectors_count": 1
    },
    {
      "name": "my_custom_collection",
      "vectors_count": 1
    },
    {
      "name": "datacenter",
      "vectors_count": 1
    },
    {
      "name": "db_users",
      "vectors_count": 1
    },
    {
      "name": "knowledge",
      "vectors_count": 17
    },
```


---

## 14. `/collections/delete` — Delete Collection

Deletes an entire collection from Qdrant database.

**Method:** `POST`  
**Auth required:** ✅ Yes

### Example

```bash
curl -X POST http://localhost:8000/collections/delete \
  -H "x-api-key: <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"collection": "knowledge"}'

```

**Expected Output:**

```json
{
  "ok": true,
  "deleted": "knowledge"
}
```

---

## 15. `/debug/chunk` — Chunk Preview

Debug endpoint for chunking text.

**Method:** `POST`  
**Auth required:** ❌ No

### Request Schema

| Variable        |  Required\* | Default             | Override | Type | Description                                                  |
| --------------- | ----------- | ------------------- | -------- | ---- | ------------------------------------------------------------ |
| `text`          | **YES**     | —                   | —        | str  | The full text string to split into chunks.                   |
| `chunk_size`    | **Optional**| `${CHUNK_SIZE}`     | **YES**  | int  | Maximum number of characters per chunk.                      |
| `chunk_overlap` | **Optional**| `${CHUNK_OVERLAP}`  | **YES**  | int  | Number of overlapping characters between consecutive chunks. |




### Examples


**Minimal curl (default chunk size/overlap):**

```bash
curl -X POST http://localhost:8000/debug/chunk \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a long text that needs to be split into chunks for processing..."}'

```

**With custom chunk size and overlap:**

```bash
curl -X POST http://localhost:8000/debug/chunk \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a long text that needs splitting into chunks...",
    "chunk_size": 10,
    "chunk_overlap": 5
  }'

```

**Expected Output:**

```json
{
  "total_chunks": 8,
  "chunks": [
    "This is a",
    "is a long",
    "long text",
    "text that",
    "needs",
    "splitting",
    "into",
    "chunks..."
  ],
  "preview": [
    "This is a",
    "is a long",
    "long text",
    "text that",
    "needs",
    "splitting",
    "into",
    "chunks..."
  ]
}

```

---

## 16. `/debug/embeds` — Embedding Debugger

Generate embeddings for a list of text inputs. Useful for testing embedding models or verifying vectorization output.

**Method:** `POST`  
**Auth required:** ✅ Yes

### Request Schema

| Variable         |  Required\* | Default           | Override | Type       | Description                                                                                       |
| ---------------- | ----------- | ----------------- | -------- | ---------- | ------------------------------------------------------------------------------------------------- |
| `texts`          | **YES**     | —                 | —        | list\[str] | List of text strings to embed.                                                                    |
| `model`          | **Optional**| `${EMBED_MODEL}`  | **YES**  | str        | Embedding model to use (e.g., `"nomic-embed-text"`).                                              |
| `return_vectors` | **Optional**| `true`            | **YES**  | bool       | Whether to return the full embedding vectors. If `false`, only metadata (count/dims) is returned. |


### Examples

**Minimal curl (default model, return vectors):**

```bash
curl -X POST http://localhost:8000/debug/embeds \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Hello world!",
      "This is a test sentence for embeddings."
    ]
  }'
```

**With custom model and no vectors:**

```bash
curl -X POST http://localhost:8000/debug/embeds \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Hello world!",
      "This is a test sentence for embeddings."
    ],
    "model": "nomic-embed-text",
    "return_vectors": false
  }'

```

**Expected Outputs:**

`**If return_vectors: true:**`

```json
{
  "count": 2,
  "dims": 768,
  "vectors": [
    [
      0.11532804369926453,
      -0.06501749902963638,
      -3.9886960983276367,
      -0.2478005290031433,
    ]
  ]
}

```

`**If return_vectors: false:**`

```json
{
  "count": 2,
  "dims": 768,
  "vectors": null
}


```

---

## 17. `/health` — Health Check

Check application health status
No authentication required.

```bash
curl -X GET http://localhost:8000/health
```

**Expected Output:**

```json
{
  "status": "ok"
}

```

---

## 18. `/ping` — Simple Ping

Test endpoints connectivity.
No authentication required.

```bash
curl -X GET http://localhost:8000/ping
```

**Expected Output:**

```json
{
  "status": "ok",
  "message": "pong"
}

```

---

# 🔧 Automation with n8n

Each endpoint can be integrated into **n8n** using the **HTTP Request node**.  
- Add header: `x-api-key: {{$json.API_KEY}}`  
- Use JSON payload matching examples above.  
- Map results into workflows for automation.

Examples:
- Auto-ingest new RSS items daily.  
- Run semantic search on Slack messages.  
- Summarize log files and send alerts.

---

# ✅ Notes
- **All ingestion endpoints automatically embed and store vectors.**  
  No separate embedding step is required.  
- Collections are created automatically if they don’t exist.  
- Default values are taken from `.env` (`.env.example` shows defaults).