# 🤖 AI Job Advisory Chatbot — Backend API

> A production-ready Flask REST API powering an AI-driven career advisory platform. It analyzes resumes using vector embeddings, scores job listings via cosine similarity, and delivers streamed responses through Server-Sent Events (SSE).

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Core Features](#core-features)
- [Database Models](#database-models)
- [API Reference](#api-reference)
- [Services & Modules](#services--modules)
- [SSE Streaming Protocol](#sse-streaming-protocol)
- [Configuration](#configuration)
- [Installation & Setup](#installation--setup)
- [Running the Project](#running-the-project)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)

---

## Overview

This backend serves a smart career advisory application that:

1. Accepts a user's resume as plain text via chat
2. Embeds the resume using a `bge-m3` embedding model
3. Computes cosine similarity against all job listings stored in PostgreSQL with `pgvector`
4. Returns the top 3 matching jobs as structured cards
5. Generates a professional Persian-language advisory report via an LLM
6. Streams the entire response token-by-token using SSE

All chat history is persisted per user, with an automatic summarization mechanism that compresses older messages into a rolling summary stored on the `Chat` model.

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                        Frontend (React)                    │
│              Consumes SSE stream / REST endpoints          │
└───────────────────────┬────────────────────────────────────┘
                        │ HTTP / SSE
┌───────────────────────▼────────────────────────────────────┐
│                    Flask Application                       │
│                                                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Auth BP    │  │   Chat BP    │  │   Message BP     │   │
│  │  /api/auth  │  │   /api/chats │  │ /api/chats/:id/  │   │
│  └─────────────┘  └──────────────┘  │   messages       │   │
│                                     └──────────────────┘   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Resume BP  │  │   Users BP   │  │    Admin BP      │   │
│  │ /api/resumes│  │   /api/me    │  │   /api/admin     │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Service Layer                     │   │
│  │  intent_classifier → resume_report → job_scoring    │   │
│  │  embeddings → qom_llm → memory_summary              │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────┬────────────────────────────┬───────────────────┘
            │                            │
┌───────────▼──────────┐    ┌────────────▼──────────────────┐
│   PostgreSQL +       │    │     External LLM / Embed API  │
│   pgvector           │    │     (Qom University LLM)      │
│   (jobs, users,      │    │     bge-m3 Embedding Model    │
│    chats, messages,  │    └───────────────────────────────┘
│    resumes, reviews) │
└──────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask 3.0.0 |
| ORM | Flask-SQLAlchemy 3.1.1 |
| Database | PostgreSQL + pgvector |
| Auth | Flask-JWT-Extended 4.6.0 |
| Password Hashing | Flask-Bcrypt 1.0.1 |
| CORS | Flask-Cors 4.0.0 |
| API Docs | Flasgger (Swagger UI) |
| Vector Search | pgvector + numpy cosine similarity |
| LLM Integration | OpenAI-compatible REST API (Qom LLM) |
| Embedding Model | bge-m3 (via Qom Embed API) |
| Streaming | Server-Sent Events (SSE) |
| DB Driver | psycopg2 + pg8000 |
| Config | python-dotenv |

---

## Project Structure

```
.
├── app.py                          # Application entry point
├── config.py                       # Centralized configuration (env-based)
├── requirements.txt
├── .gitignore
│
├── chat_api/
│   ├── __init__.py                 # App factory (create_app), CORS, Swagger, JWT setup
│   ├── extensions.py               # Shared Flask extensions (db, bcrypt, jwt)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User model (username, email, phone, role)
│   │   ├── chat.py                 # Chat model (title, summary, last_summarized_message_id)
│   │   ├── message.py              # Message model (role: user/assistant/system)
│   │   ├── resume.py               # Resume model (title, content, user FK)
│   │   ├── job.py                  # Job model (embedding, requirements, raw_text)
│   │   ├── company.py              # Company model (reviews JSON)
│   │   └── token_blocklist.py      # JWT revocation table
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                 # /register, /login, /refresh, /logout
│   │   ├── chat.py                 # GET/POST /chats, DELETE /chats/:id, PATCH title
│   │   ├── message.py              # GET/POST /chats/:id/messages (SSE stream)
│   │   ├── resume.py               # Full CRUD + /import endpoint
│   │   ├── users.py                # /me profile, password change, account delete
│   │   ├── admin.py                # /admin/stats (role-gated)
│   │   └── landing.py              # /landing public stats + content
│   │
│   ├── service/
│   │   ├── qom_llm.py              # LLM chat completion wrapper + chunk_text
│   │   ├── embeddings.py           # bge-m3 embedding + cosine_similarity + clamp_percent
│   │   ├── intent_classifier.py    # LLM-based ANALYZE vs CHAT intent detection
│   │   ├── resume_report.py        # Full RAG pipeline: embed → score → fetch reviews → report
│   │   ├── job_scoring.py          # DB loading, scoring, card building, prompt text builder
│   │   ├── company_reviews.py      # Exact + fuzzy company review fetcher + formatter
│   │   ├── botMessage.py           # Chat mode: history assembly + LLM call + SSE yield
│   │   ├── message_stream.py       # SSE orchestrator: intent → jobs → content → done
│   │   ├── static_mock.py          # Static mock SSE stream for local dev/testing
│   │   ├── memory_summary.py       # Rolling chat summary via LLM (every N messages)
│   │   ├── title_gen.py            # Auto-generate 3-word Persian chat title from first message
│   │   ├── auth_validators.py      # Username, password, email, phone validators (regex)
│   │   └── docs_path.py            # Path helper for YAML doc files
│   │
│   ├── utils/
│   │   ├── response_utils.py       # api_ok(), api_error(), normalize_username()
│   │   ├── message_utils.py        # message_dto(), sse() formatter
│   │   ├── chat_utils.py           # chat_brief(), current_user_id(), get_chat_if_owner()
│   │   └── requirements_utils.py   # normalize_requirements() for job requirement parsing
│   │
│   └── docs/                       # Swagger YAML documentation per endpoint
│       ├── auth/
│       ├── chat/
│       ├── message/
│       ├── resume/
│       ├── user/
│       ├── admin/
│       └── landing/
│
└── tests/
    ├── test.py                     # LLM connectivity test
    ├── test_db_connection.py       # PostgreSQL connectivity test
    └── create_tables.py            # (reserved)
```

---

## Core Features

### Authentication
- JWT-based auth with access + refresh tokens
- Token revocation via `token_blocklist` table
- Bcrypt password hashing
- Username normalization (lowercase, stripped)
- Input validation: username (3–32 chars, alphanumeric + `._-`), password (8–128 chars, must contain letter + digit)

### Chat System
- Per-user isolated chat sessions
- Auto-generated Persian chat title from first message (max 3 words, via LLM)
- Manual title update (PATCH, max 60 chars)
- Chat deletion with cascade to messages
- Rolling memory summary: every 10 messages, older messages are compressed into `chat.summary` via LLM, injected into subsequent prompts as context

### Resume Management
- Full CRUD: create, list, get, update, delete
- `/import` endpoint: returns only `content` field for importing into chat input
- All resumes scoped to authenticated user

### RAG Job Matching Pipeline
The core intelligence of the system:

1. **Intent Classification** — Every user message is classified as `ANALYZE` or `CHAT` using a zero-temperature LLM call with JSON output
2. **Embedding** — Resume text is embedded via `bge-m3` (up to 4000 chars, padded/truncated to `EMBED_EXPECTED_DIM`)
3. **Vector Scoring** — Cosine similarity computed in Python (numpy) against all job embeddings loaded from PostgreSQL
4. **Top-3 Selection** — Jobs sorted by similarity score, top 3 selected
5. **Company Reviews** — Exact-match then ILIKE fuzzy-match against `companies` table
6. **Card Building** — Structured JSON cards with `match_percent`, `requirements`, `company_reviews`
7. **LLM Report** — Full Persian advisory report generated with resume + job texts in prompt
8. **SSE Streaming** — Report chunked at 220 chars and streamed as SSE `content` events

### Admin Dashboard
- Role-gated (`role = "admin"`) stats endpoint
- Returns counts: users, jobs, chats, messages

### Landing Page
- Public endpoint returning platform statistics + full Persian landing content (hero, features, how-it-works, CTAs)

---

## Database Models

### `users`
| Column | Type | Notes |
|---|---|---|
| `user_id` | Integer PK | |
| `username` | String(255) | unique, indexed |
| `email` | String(255) | unique, nullable |
| `phone_number` | String(20) | unique, nullable |
| `password_hash` | String(255) | bcrypt |
| `role` | String(20) | `"user"` or `"admin"` |
| `created_at` / `updated_at` | DateTime(tz) | UTC |

### `chats`
| Column | Type | Notes |
|---|---|---|
| `chat_id` | BigInteger PK | |
| `user_id` | FK → users | |
| `title` | String(255) | default: "گفتگوی جدید" |
| `summary` | Text | rolling LLM memory |
| `last_summarized_message_id` | Integer | tracks summarization cursor |
| `created_at` / `updated_at` | DateTime(tz) | |

### `messages`
| Column | Type | Notes |
|---|---|---|
| `message_id` | BigInteger PK | |
| `chat_id` | FK → chats | cascade delete |
| `content` | Text | |
| `role` | String(20) | `user`, `assistant`, `system` |
| `created_at` | DateTime(tz) | |

### `resumes`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → users | ondelete CASCADE |
| `title` | String(120) | |
| `content` | Text | |
| `created_at` / `updated_at` | DateTime(tz) | |

### `jobs`
| Column | Type | Notes |
|---|---|---|
| `job_id` | BigInteger PK | |
| `job_url` | Text | unique |
| `source_site` | Text | |
| `job_title` | Text | |
| `company_name` | Text | |
| `location` | Text | |
| `paycheck` | Text | |
| `requirements` | JSON | list/dict/str |
| `raw_text` | Text | full ad text |
| `embedding` | Vector(1536) | pgvector |

### `companies`
| Column | Type | Notes |
|---|---|---|
| `company_id` | BigInteger PK | |
| `company_name` | Text | unique |
| `reviews` | JSON | list/dict/str |
| `updated_at` | DateTime | |

### `token_blocklist`
| Column | Type | Notes |
|---|---|---|
| `id` | BigInteger PK | |
| `jti` | String(36) | unique, indexed |
| `token_type` | String(10) | `access` or `refresh` |
| `user_id` | FK → users | nullable |
| `revoked_at` | DateTime | |

---

## API Reference

Base URL: `/api`

Swagger UI available at: `http://localhost:5000/apidocs`

### Auth — `/api/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login, get access + refresh tokens |
| POST | `/auth/refresh` | Refresh token | Rotate access token |
| POST | `/auth/logout` | Access token | Revoke current token |

### Chats — `/api/chats`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/chats` | Yes | List all user chats (ordered by `updated_at desc`) |
| POST | `/chats` | Yes | Create new chat |
| DELETE | `/chats/:chat_id` | Yes | Delete chat + cascade messages |
| PATCH | `/chats/:chat_id/title` | Yes | Update chat title (max 60 chars) |

### Messages — `/api/chats/:chat_id/messages`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/chats/:id/messages` | Yes | Get all messages in a chat |
| POST | `/chats/:id/messages` | Yes | Send message, returns SSE stream |

### Resumes — `/api/resumes`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/resumes/` | Yes | Create resume |
| GET | `/resumes/` | Yes | List all resumes (ordered by `updated_at desc`) |
| GET | `/resumes/:id` | Yes | Get single resume |
| PUT/PATCH | `/resumes/:id` | Yes | Update title or content |
| DELETE | `/resumes/:id` | Yes | Delete resume |
| GET | `/resumes/:id/import` | Yes | Get only content for chat import |

### Users — `/api`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/me` | Yes | Get own profile |
| PATCH | `/me` | Yes | Update username / email / phone |
| PATCH | `/me/password` | Yes | Change password |
| DELETE | `/me` | Yes | Delete account (cascade) |

### Admin — `/api/admin`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/admin/stats` | Admin role | Get platform-wide counts |

### Landing — `/api`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/landing` | No | Get landing page content + live stats |

### Debug

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/_debug/cors` | Returns allowed CORS origins |

---

## Services & Modules

### `qom_llm.py`
Thin wrapper around the Qom LLM's OpenAI-compatible `/v1/chat/completions` endpoint.

```python
qom_chat(messages, temperature=None, max_tokens=None, timeout=None) -> str
chunk_text(text, chunk_size=220) -> Generator[str]
```

Uses `Config.LLM_API_KEY`, `Config.LLM_MODEL`, `Config.LLM_TEMPERATURE`, `Config.LLM_MAX_TOKENS`. `chunk_text` simulates token-by-token streaming since the LLM is called synchronously.

---

### `embeddings.py`
Interfaces with the bge-m3 embedding API.

```python
get_embedding(text, task_type=None) -> np.ndarray   # shape: (EMBED_EXPECTED_DIM,)
cosine_similarity(a, b) -> float                    # range: 0.0 – 1.0
clamp_percent(score) -> int                         # converts to 0–100 integer
```

Input text is truncated to 4000 chars before embedding. Output is padded or truncated to `EMBED_EXPECTED_DIM` (from `.env`).

---

### `intent_classifier.py`
Classifies user input as `ANALYZE` (resume/job matching) or `CHAT` (general advisory).

```python
detect_intent(user_text) -> "ANALYZE" | "CHAT"
```

Uses zero-temperature LLM call with strict JSON output schema. Falls back to heuristic: `len(text) >= 120` → `ANALYZE`. Confidence threshold: if `< 0.55` and text is long → forces `ANALYZE`.

---

### `resume_report.py`
The main RAG pipeline, called when intent is `ANALYZE`.

```python
analyze_resume_stream(user_text) -> Generator
```

Yields in order:
1. `str` — intro message
2. `("jobs", {"items": [...]})` — structured job cards
3. `str` chunks — LLM advisory report in 220-char pieces

---

### `job_scoring.py`

```python
load_jobs_with_embeddings(cursor) -> list       # loads all jobs with non-null embeddings
score_jobs(rows, resume_embedding) -> list      # sorted by cosine similarity desc
build_cards(top_jobs, reviews_map) -> list      # structured card dicts
build_jobs_text_for_prompt(top_jobs, reviews_map) -> str  # formatted text for LLM prompt
open_conn() -> psycopg2.connection              # opens psycopg2 + registers pgvector
```

---

### `company_reviews.py`

```python
fetch_company_reviews(cursor, company_names) -> dict   # exact match then ILIKE fuzzy
format_reviews_for_prompt(reviews, max_items=6) -> str # handles list/dict/str/None
```

---

### `botMessage.py`
Handles the `CHAT` intent path. Assembles system prompt, rolling summary, last 6 messages, and current user message. Yields SSE tuples: `("intent", ...)`, `("content", chunk)`.

---

### `message_stream.py`
SSE orchestrator. Consumes `generate_bot_reply()` generator, emits `meta` event first, routes `jobs` events to SSE, accumulates `content` chunks, saves final `Message` to DB, triggers `maybe_update_chat_summary()`, emits `done` with `bot_message_id`.

---

### `memory_summary.py`
Rolling chat compressor.

```python
maybe_update_chat_summary(chat_id, user_id, every_n_messages=10)
update_chat_summary(chat_id, user_id, chunk_limit=18)
```

Triggers only when `total_messages % every_n_messages == 0`. Reads messages newer than `last_summarized_message_id`. Appends new block to existing summary, re-summarizes via LLM, updates `chat.summary` and `chat.last_summarized_message_id`.

---

### `title_gen.py`
Auto-generates a short (max 3-word) Persian chat title from the first user message.

```python
generate_chat_title(first_user_message) -> str   # max 60 chars, fallback: "چت جدید"
```

---

### `auth_validators.py`

| Function | Rules |
|---|---|
| `validate_username` | 3–32 chars, `^[a-z0-9._-]+$` |
| `validate_password` | 8–128 chars, must contain letter + digit |
| `validate_email` | Standard regex, max 255 chars |
| `validate_phone_number` | Iranian format: `0912...`, `+98912...`, `98912...` |

---

### `requirements_utils.py`
Normalizes the `requirements` field from jobs, which can be `list`, `dict`, `str`, or `None`. Falls back to parsing bullet points (`•`, `-`, `*`, `–`) from `raw_text` if structured data is missing.

---

## SSE Streaming Protocol

Every POST to `/api/chats/:id/messages` returns `Content-Type: text/event-stream`.

### Event Sequence

```
event: meta
data: {"chat": {...}, "user_message_id": 101, "type": "analyze"|"chat", "title_changed": false}

event: jobs
data: {"items": [{
  "title": "...",
  "company_name": "...",
  "location": "...",
  "paycheck": "...",
  "requirements": ["Python", "Flask", ...],
  "match_percent": 86,
  "job_url": "https://...",
  "source_site": "...",
  "company_reviews": {...}
}]}

event: content
data: {"delta": "رزومه شما را بررسی کردیم..."}

event: done
data: {"bot_message_id": 102}

event: error
data: {"message": "..."}
```

The `jobs` event is only emitted when `type == "analyze"`. Multiple `content` events are emitted sequentially. The stream always ends with either `done` or `error`.

### Static Mock Mode
For local development without LLM/DB access, `message.py` uses `stream_static_reply()` from `static_mock.py`. To switch to live mode, replace the call with `stream_bot_reply()` in `chat_api/routes/message.py`:

```python
# Development (default):
stream_static_reply(chat, user_msg, content, user_id, title_changed)

# Production (live LLM + DB):
stream_bot_reply(chat, user_msg, content, user_id, title_changed)
```

---

## Configuration

All configuration is loaded from `.env` via `python-dotenv` in `config.py`.

```python
class Config:
    SECRET_KEY                # Flask secret
    SQLALCHEMY_DATABASE_URI   # PostgreSQL DSN
    JWT_SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES  # from JWT_ACCESS_MINUTES
    JWT_REFRESH_TOKEN_EXPIRES # from JWT_REFRESH_DAYS

    LLM_BASE_URL              # e.g. https://llm.example.ir
    LLM_CHAT_ENDPOINT         # e.g. /llm/v1/chat/completions
    LLM_API_KEY
    LLM_MODEL
    LLM_TEMPERATURE
    LLM_MAX_TOKENS
    LLM_TIMEOUT

    EMBED_BASE_URL
    EMBED_MODEL               # bge-m3
    EMBED_EXPECTED_DIM        # e.g. 1536
    EMBED_TIMEOUT
```

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with `pgvector` extension
- Access to Qom LLM API and Embed API

### 1. Clone the repository

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 5. Enable pgvector on PostgreSQL

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 6. Initialize the database

Tables are created automatically on first run via `db.create_all()` inside the app factory:

```bash
python -c "from chat_api import create_app; app = create_app()"
```

---

## Running the Project

### Development

```bash
python app.py
```

Server starts at `http://0.0.0.0:5000`. Swagger UI at `http://localhost:5000/apidocs`.

### Production

```bash
gunicorn -w 1 -b 0.0.0.0:5000 --timeout 120 "app:app"
```

> Use only 1 worker when relying on SSE/streaming. For scaling, use an async worker like `gevent`.

---

## Running Tests

### Test LLM connectivity

```bash
python tests/test.py
```

Expected output: `متصل شد.`

### Test database connectivity

```bash
python tests/test_db_connection.py
```

Expected output:
```
✅ اتصال موفقیت‌آمیز بود!
📦 نسخه PostgreSQL: PostgreSQL 15.x ...
```

---

## Environment Variables

```env
# Flask
SECRET_KEY=your-flask-secret-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=30

# LLM (Chat)
LLM_BASE_URL=https://llm.example.ir
LLM_CHAT_ENDPOINT=/llm/v1/chat/completions
LLM_API_KEY=your-llm-api-key
LLM_MODEL=your-model-name
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=60

# Embedding
EMBED_BASE_URL=https://embed.example.ir
EMBED_MODEL=bge-m3
EMBED_EXPECTED_DIM=1536
EMBED_TIMEOUT=30

# CORS
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## Response Format

All non-SSE endpoints return a consistent JSON envelope.

**Success:**
```json
{
  "status": 200,
  "message": "ok",
  "data": { ... }
}
```

**Error:**
```json
{
  "status": 400,
  "error": "description of error",
  "data": null
}
```

---

## CORS Configuration

CORS is configured per the `CORS_ORIGINS` environment variable. If not set, defaults to `localhost:5173` variants. Only routes under `/api/*` are CORS-enabled. Authentication is handled via `Authorization: Bearer <token>` header; `supports_credentials` is `false`.

---

## License

This project is proprietary. All rights reserved.
