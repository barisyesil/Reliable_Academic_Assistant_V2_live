# Backend — ESTÜ Akademik Asistan API

> 🚧 **Under active development.** Endpoints and configuration may change. See [Known Issues](#known-issues--todo).

This is the FastAPI service behind the Reliable Academic Assistant. It handles authentication and user data (courses, events, conversations), and runs a **LangGraph ReAct agent** that answers questions using **RAG over official ESTÜ documents** and the student's own academic data.

For the full project overview, see the [main README](../README.md).

---

## Stack

- **FastAPI**, with Uvicorn locally and Gunicorn + Uvicorn workers in production
- **SQLAlchemy 2 (async)**: PostgreSQL through `asyncpg` (Supabase pooler) in production, SQLite by default for local development
- **Auth**: JWT access and refresh tokens (`python-jose`), with passwords hashed by `passlib[bcrypt]`
- **LLM**: Groq `qwen/qwen3-32b` (temperature 0, parallel tool calls turned off), with a LangChain SQLite response cache
- **Agent**: LangGraph `create_react_agent` with 4 tools for each user
- **Retrieval**: Pinecone index `estu-index`, with `BAAI/bge-m3` embeddings from the Hugging Face Inference API
- **PDF parsing**: PyMuPDF (`fitz`) for transcripts and document ingestion

## Directory Structure

```
backend/
├── main.py                    # FastAPI app, lifespan (DB → RAG → LLM), CORS, error handler, routers
├── ingest.py                  # Offline PDF ingestion: clean → chunk → embed → store
├── test_rag.py                # Manual smoke test for vector search
├── megatest.py                # Supabase connectivity diagnostics (DNS / TCP / asyncpg)
├── requirements.txt
├── data/                      # Source PDFs; the subfolder name becomes the "category" metadata
│   ├── estüceng/              # Department guides (internship guide, project-based internship…)
│   ├── usul ve esaslar/       # Procedures & principles
│   ├── yönergeler/            # Directives
│   └── yönetmelik/            # Regulations
├── db/                        # Local Chroma store + processed_files.json (ingestion hash cache)
└── app/
    ├── agents/
    │   ├── academic_agent.py  # SYSTEM_PROMPT, build_agent(), build_messages()
    │   └── tools.py           # make_agent_tools(): per-request tool set + source collector
    ├── api/
    │   ├── auth.py            # /api/auth
    │   ├── chat.py            # /api/chat
    │   ├── user.py            # /api/user
    │   └── documents.py       # /api/document, /api/parse-transcript
    ├── core/
    │   ├── config.py          # Pydantic Settings (.env)
    │   ├── database.py        # Async engine / session, init_db()
    │   └── security.py        # Password hashing, JWT create/verify, get_current_user_id
    ├── models/models.py       # User, Conversation, Message, Course, Event
    ├── schemas/schemas.py     # Pydantic request/response models
    ├── services/
    │   ├── rag_service.py     # init_rag() / get_vector_store() (Pinecone)
    │   └── db_service.py      # get_user_academic_summary() (GPA, courses, 30-day events)
    └── transcript_parser.py   # ESTÜ transcript PDF → semesters / courses / grades
```

## Getting Started

### 1. Install

```bash
cd backend
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install langgraph aiosqlite     # not yet in requirements.txt
```

### 2. Configure `.env`

Create `backend/.env`:

```env
# Database (defaults to local SQLite if omitted)
DATABASE_URL=sqlite+aiosqlite:///./estu.db
# DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:6543/postgres   # Supabase pooler

# Auth
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI services
GROQ_API_KEY=...
HF_TOKEN=...
PINECONE_API_KEY=...

# CORS (JSON list or single origin)
CORS_ORIGINS=["http://localhost:5173"]
```

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | – | SQLAlchemy async URL. When it is not SQLite, SSL and PgBouncer-safe settings are used. |
| `SECRET_KEY` | ✅ (prod) | JWT signing key. Always override the default. |
| `GROQ_API_KEY` | ✅ | The Groq LLM API key |
| `HF_TOKEN` | ✅ | Hugging Face token for `BAAI/bge-m3` embeddings |
| `PINECONE_API_KEY` | ✅ | The Pinecone key. The index `estu-index` must already exist and be populated. |
| `CORS_ORIGINS` | – | Allowed origins. **Note:** `main.py` currently allows `*`. |

### 3. Run

```bash
uvicorn main:app --reload --port 8000
```

- API docs (Swagger): http://localhost:8000/docs
- Health check: `GET /health` → `{"status": "ok", "version": "2.0.0"}`

On startup, the app creates the database tables, connects to Pinecone, and sets up the Groq LLM. Startup fails if `HF_TOKEN` or `PINECONE_API_KEY` is missing.

**Production (Render):**

```bash
gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

## API Reference

All `/api/user/*` and `/api/chat/*` routes, and `POST /api/parse-transcript`, need `Authorization: Bearer <access_token>`.

### Auth — `/api/auth`
| Method | Path | Description |
|---|---|---|
| POST | `/register` | Create an account and return access and refresh tokens |
| POST | `/login` | Log in with email and password and return tokens |
| POST | `/refresh` | Exchange a refresh token for a new pair of tokens |

### Chat — `/api/chat`
| Method | Path | Description |
|---|---|---|
| POST | `` | Send `{ query, conversation_id? }` and get `{ answer, sources[], conversation_id }` |
| GET | `/conversations` | The latest 30 conversations |
| GET | `/conversations/{id}/messages` | The full message history, with sources |
| DELETE | `/conversations/{id}` | Delete a conversation |

### User — `/api/user`
| Method | Path | Description |
|---|---|---|
| GET / PATCH | `/me` | Read or update the profile (name, student ID, department, year) |
| GET / POST | `/courses` | List or add courses |
| DELETE | `/courses/{id}` | Remove a course |
| POST | `/courses/upload-transcript` | Upload a transcript PDF |
| POST | `/courses/parse-and-save` | Parse a transcript and save its courses |
| GET / POST | `/events` | List or add calendar events |
| DELETE | `/events/{id}` | Remove an event |

### Documents — `/api`
| Method | Path | Description |
|---|---|---|
| GET | `/document/{category}/{filename}` | Serve a source PDF from `data/`, used for citation links |
| POST | `/parse-transcript` | Parse a transcript PDF (multipart `file`) and save the courses. The frontend uses this one. |

## The Agent

`app/agents/academic_agent.py` defines a strict system prompt (in Turkish) that makes the model:

1. Use `search_regulations` for **every** question about rules or procedures, and never answer from general knowledge.
2. Fetch personal data only when it is needed.
3. Say *"I couldn't find this in ESTÜ regulations"* when retrieval returns nothing.
4. Cite document names in its answers, and never show internal tool steps to the user.

**Tools** (`app/agents/tools.py`). The tools are built for each request, and the user's data is loaded before the agent runs:

| Tool | What it does |
|---|---|
| `search_regulations(query)` | Runs an MMR search on Pinecone (`k=4, fetch_k=20, λ=0.7`) and records the sources (document, page, category, snippet) |
| `get_user_grades(query)` | Returns the GPA and course summary from the database |
| `get_calendar_events(timeframe)` | Returns the user's events for the next 30 days |
| `calculate_academic_status("2.85,2.50")` | Compares the current GPA with a required minimum and says whether the student is eligible |

The agent sees the **last 2 turns** of the conversation.

## Document Ingestion

`ingest.py` builds the knowledge base from `data/**/*.pdf`:

1. **Change detection.** It stores an MD5 hash of each file in `db/processed_files.json`, so only new or changed PDFs are processed.
2. **Structural cleaning.** It joins words broken by hyphens and turns `MADDE n` and `BÖLÜM n` into Markdown headings, so chunks follow article boundaries.
3. **Metadata.** It stores `category` (the subfolder) and `document_name`, and adds a `KATEGORİ | BELGE | SAYFA` header to each page.
4. **Chunking.** It uses `RecursiveCharacterTextSplitter` (size 1500, overlap 300) with heading-aware separators.
5. **Embedding.** It embeds the chunks with `BAAI/bge-m3`, normalized, on CPU.

```bash
python ingest.py
```

> ⚠️ `ingest.py` currently writes to a **local Chroma** store (`./db`), but the API reads from **Pinecone**. Porting the ingestion to Pinecone (`PineconeVectorStore.add_documents`) is on the roadmap.

## Data Model

```
User 1─* Conversation 1─* Message(role, content, sources JSON)
User 1─* Course(course_code, course_name, credits, grade, semester, source: transcript|manual)
User 1─* Event(title, event_date, event_time, color_category)
```

The tables are created automatically on startup (`init_db()`). There are no migrations yet.

