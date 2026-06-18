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
7. Allows users to **bookmark** job cards for later review

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
│  ┌─────────────────────────────┐                           │
│  │       Bookmark BP           │                           │
│  │     /api/bookmarks          │                           │
│  └─────────────────────────────┘                           │
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
│    resumes, reviews, │
│    bookmarks)        │
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
├── app.py
├── config.py
├── requirements.txt
│
├── chat_api/
│   ├── __init__.py
│   ├── extensions.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── message.py
│   │   ├── resume.py
│   │   ├── job.py
│   │   ├── company.py
│   │   ├── job_card.py
│   │   ├── bookmark.py          ← جدید
│   │   └── token_blocklist.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── message.py
│   │   ├── resume.py
│   │   ├── users.py
│   │   ├── admin.py
│   │   ├── landing.py
│   │   └── bookmark.py          ← جدید
│   │
│   ├── service/  ...
│   ├── utils/    ...
│   │
│   └── docs/
│       ├── auth/
│       ├── chat/
│       ├── message/
│       ├── resume/
│       ├── user/
│       ├── admin/
│       ├── landing/
│       └── bookmark/            ← جدید
│           ├── toggle_bookmark.yml
│           ├── list_bookmarks.yml
│           ├── delete_bookmark.yml
│           └── check_bookmark.yml
│
└── tests/
```

---

## Core Features

### Authentication
- JWT-based auth with access + refresh tokens
- Token revocation via `token_blocklist` table
- Bcrypt password hashing

### Chat System
- Per-user isolated chat sessions
- Auto-generated Persian chat title from first message
- Rolling memory summary every 10 messages

### Resume Management
- Full CRUD + `/import` endpoint

### RAG Job Matching Pipeline
1. Intent Classification → ANALYZE / CHAT
2. Embedding via bge-m3
3. Cosine similarity against all job embeddings
4. Top-3 selection
5. Company reviews (exact + fuzzy match)
6. Card building with `match_percent`
7. LLM Persian advisory report
8. SSE streaming

### Bookmark System ← جدید
- کاربر می‌تواند روی دکمه بوک‌مارک کنار هر کارت شغلی کلیک کند
- Toggle endpoint: اگر بوک‌مارک وجود داشته باشد حذف می‌شود، در غیر این صورت اضافه می‌شود
- لیست بوک‌مارک‌ها مخصوص هر کاربر و مرتب بر اساس زمان
- بررسی وضعیت بوک‌مارک یک آدرس خاص (برای وضعیت اولیه دکمه در فرانت)
- Constraint یکتایی: هر کاربر یک `job_url` را فقط یکبار بوک‌مارک می‌کند

### Admin Dashboard
- Role-gated stats endpoint

---

## Database Models

### `users`
| Column | Type | Notes |
|---|---|---|
| `user_id` | Integer PK | |
| `username` | String(255) | unique |
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
| `title` | String(255) | |
| `summary` | Text | rolling LLM memory |
| `last_summarized_message_id` | Integer | |

### `messages`
| Column | Type | Notes |
|---|---|---|
| `message_id` | BigInteger PK | |
| `chat_id` | FK → chats | cascade delete |
| `content` | Text | |
| `role` | String(20) | `user`, `assistant`, `system` |

### `resumes`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → users | ondelete CASCADE |
| `title` | String(120) | |
| `content` | Text | |

### `jobs`
| Column | Type | Notes |
|---|---|---|
| `job_id` | BigInteger PK | |
| `job_url` | Text | unique |
| `embedding` | Vector(1536) | pgvector |
| ... | | |

### `job_cards`
| Column | Type | Notes |
|---|---|---|
| `id` | BigInteger PK | |
| `message_id` | FK → messages | ondelete CASCADE |
| `cards_json` | JSON | لیست کارت‌های شغلی |

### `bookmarks` ← جدید
| Column | Type | Notes |
|---|---|---|
| `id` | BigInteger PK | |
| `user_id` | FK → users | ondelete CASCADE |
| `job_url` | Text | |
| `job_title` | Text | nullable |
| `company_name` | Text | nullable |
| `location` | Text | nullable |
| `paycheck` | Text | nullable |
| `source_site` | Text | nullable |
| `match_percent` | Integer | nullable |
| `requirements` | JSON | nullable |
| `company_reviews` | JSON | nullable |
| `created_at` | DateTime(tz) | |
| **UNIQUE** | `(user_id, job_url)` | هر کاربر یک job_url را فقط یکبار |

### `companies`
| Column | Type | Notes |
|---|---|---|
| `company_id` | BigInteger PK | |
| `company_name` | Text | unique |
| `reviews` | JSON | |

### `token_blocklist`
| Column | Type | Notes |
|---|---|---|
| `id` | BigInteger PK | |
| `jti` | String(36) | unique |
| `token_type` | String(10) | |
| `user_id` | FK → users | nullable |

---

## API Reference

Base URL: `/api`  
Swagger UI: `http://localhost:5000/apidocs`

### Auth — `/api/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login |
| POST | `/auth/refresh` | Refresh token | Rotate access token |
| POST | `/auth/logout` | Access token | Revoke token |

### Chats — `/api/chats`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/chats` | Yes | List user chats |
| POST | `/chats` | Yes | Create chat |
| DELETE | `/chats/:chat_id` | Yes | Delete chat |
| PATCH | `/chats/:chat_id/title` | Yes | Update title |

### Messages

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/chats/:id/messages` | Yes | Get messages |
| POST | `/chats/:id/messages` | Yes | Send message (SSE) |

### Resumes — `/api/resumes`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/resumes/` | Yes | Create |
| GET | `/resumes/` | Yes | List |
| GET | `/resumes/:id` | Yes | Get single |
| PUT/PATCH | `/resumes/:id` | Yes | Update |
| DELETE | `/resumes/:id` | Yes | Delete |
| GET | `/resumes/:id/import` | Yes | Get content only |

### Users — `/api`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/me` | Yes | Get profile |
| PATCH | `/me` | Yes | Update profile |
| PATCH | `/me/password` | Yes | Change password |
| DELETE | `/me` | Yes | Delete account |

### Bookmarks — `/api/bookmarks` ← جدید

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/bookmarks/toggle` | Yes | Add or remove a bookmark (toggle) |
| GET | `/bookmarks/` | Yes | List all bookmarks of the user |
| DELETE | `/bookmarks/:id` | Yes | Delete bookmark by ID |
| GET | `/bookmarks/check?job_url=...` | Yes | Check if a job_url is bookmarked |

#### نحوه استفاده در فرانت‌اند

```js
// Toggle (add/remove) — کافی است همین یک endpoint را صدا بزنید
POST /api/bookmarks/toggle
Body: {
  "job_url": "https://...",
  "job_title": "Python Developer",
  "company_name": "Acme",
  "location": "Tehran",
  "paycheck": "Negotiable",
  "source_site": "jobinja",
  "match_percent": 86,
  "requirements": ["Python", "Flask"],
  "company_reviews": { "rating": 4.2 }
}

// Response اگر اضافه شد → 201, bookmarked: true
// Response اگر حذف شد → 200, bookmarked: false

// لیست بوک‌مارک‌ها
GET /api/bookmarks/

// بررسی وضعیت
GET /api/bookmarks/check?job_url=https://...
```

### Admin — `/api/admin`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/admin/stats` | Admin | Platform stats |
| GET | `/admin/users` | Admin | List users |
| DELETE | `/admin/users/:id` | Admin | Delete user |
| GET | `/admin/jobs` | Admin | List jobs |
| GET | `/admin/jobs/:id` | Admin | Get job |
| PATCH | `/admin/jobs/:id` | Admin | Update job |
| DELETE | `/admin/jobs/:id` | Admin | Delete job |

### Landing & Debug

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/landing` | No | Landing content + stats |
| GET | `/api/_debug/cors` | No | CORS debug |

---

## SSE Streaming Protocol

Every POST to `/api/chats/:id/messages` returns `Content-Type: text/event-stream`.

```
event: meta
data: {"chat": {...}, "user_message_id": 101, "type": "analyze"|"chat", "title_changed": false}

event: jobs
data: {"items": [{
  "title": "...",
  "company_name": "...",
  "location": "...",
  "paycheck": "...",
  "requirements": ["Python", ...],
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

### نکته برای بوک‌مارک

وقتی فرانت‌اند `jobs` event را دریافت می‌کند، کنار هر کارت یک دکمه ستاره/بوک‌مارک نشان می‌دهد. با کلیک روی آن، اطلاعات کارت را به `POST /api/bookmarks/toggle` ارسال می‌کند.

---

## Static Mock Mode

```python
# Development (default):
STATIC_MODE = True   # در routes/message.py

# Production:
STATIC_MODE = False
```

---

## Configuration

```python
class Config:
    SECRET_KEY
    SQLALCHEMY_DATABASE_URI
    JWT_SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES   # JWT_ACCESS_MINUTES
    JWT_REFRESH_TOKEN_EXPIRES  # JWT_REFRESH_DAYS
    LLM_BASE_URL / LLM_CHAT_ENDPOINT / LLM_API_KEY / LLM_MODEL
    LLM_TEMPERATURE / LLM_MAX_TOKENS / LLM_TIMEOUT
    EMBED_BASE_URL / EMBED_MODEL / EMBED_EXPECTED_DIM / EMBED_TIMEOUT
```

---

## Installation & Setup

```bash
git clone ...
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # مقادیر را پر کنید
```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

```bash
python app.py   # جداول به‌طور خودکار ساخته می‌شوند (db.create_all)
```

---

## Running the Project

```bash
# Development
python app.py

# Production
gunicorn -w 1 -b 0.0.0.0:5000 --timeout 120 "app:app"
```

---

## Running Tests

```bash
python tests/test.py            # LLM connectivity
python tests/test_db_connection.py  # DB connectivity
```

---

## Environment Variables

```env
SECRET_KEY=...
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
JWT_SECRET_KEY=...
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=30
LLM_BASE_URL=https://llm.example.ir
LLM_CHAT_ENDPOINT=/llm/v1/chat/completions
LLM_API_KEY=...
LLM_MODEL=...
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=60
EMBED_BASE_URL=https://embed.example.ir
EMBED_MODEL=bge-m3
EMBED_EXPECTED_DIM=1536
EMBED_TIMEOUT=30
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## Response Format

```json
// Success
{ "status": 200, "message": "ok", "data": { ... } }

// Error
{ "status": 400, "error": "description", "data": null }
```

---

## License

This project is proprietary. All rights reserved.