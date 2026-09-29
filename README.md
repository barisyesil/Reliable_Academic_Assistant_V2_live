# Reliable Academic Assistant (ESTÜ Akademik Asistan) — V2

> 🚧 **This project is under active development.** Features, APIs and the deployment setup can still change, and some parts are unfinished. See [Status & Roadmap](#status--roadmap).

An AI assistant for students at **Eskişehir Technical University (ESTÜ)**. It answers questions about university regulations, directives and procedures from the official documents, and cites them. It also uses the student's own data (courses, GPA, calendar), so it can answer personal questions like *"Is my GPA high enough to apply for the internship?"*

This is my undergraduate graduation project (Computer Engineering, ESTÜ).

---

## Why "reliable"?

General-purpose chatbots often make up university rules. This assistant is built to avoid that:

- **Retrieval first:** the agent must call a regulation-search tool before it answers any procedural question. It does not rely on the model's general knowledge.
- **Grounded citations:** each answer returns the source documents and page numbers it used. The UI links to the original PDF.
- **Explicit refusal:** if the documents do not cover a question, the agent says so. It does not guess.
- **Personal context through tools:** the student's GPA, courses and events come from the database through dedicated tools, not from the chat history.

## Features

| | |
|---|---|
| 💬 **AI chat** | A LangGraph ReAct agent with multi-turn conversations, saved chat history and source citations |
| 📚 **Regulation search (RAG)** | Semantic search (MMR) over ~30 official ESTÜ PDFs (regulations, directives, internship guides) |
| 🎓 **Transcript import** | Upload your ESTÜ transcript PDF; your courses and grades are parsed automatically |
| 📊 **GPA calculator** | Manage your courses and calculate GPA and credits (AKTS) |
| 📅 **Calendar** | Personal events (exams, deadlines) that the agent can read |
| 👤 **Accounts** | JWT authentication (access and refresh tokens) and a profile page |
| 🌗 **UI** | Responsive React + Tailwind interface with dark and light themes |

## Architecture

```
┌──────────────────────┐        HTTPS / JSON (JWT)       ┌───────────────────────────────┐
│  Frontend (Vercel)   │ ─────────────────────────────▶  │  Backend – FastAPI (Render)   │
│  React 18 + Vite     │                                 │                               │
│  Tailwind v4, Router │ ◀─────────────────────────────  │  /api/auth  /api/user         │
└──────────────────────┘     answer + sources[]          │  /api/chat  /api/document     │
                                                         └──────┬───────────┬────────────┘
                                                                │           │
                                   ┌────────────────────────────┘           │
                                   ▼                                        ▼
                    ┌───────────────────────────┐          ┌──────────────────────────────┐
                    │ LangGraph ReAct Agent     │          │ PostgreSQL (Supabase)        │
                    │ LLM: Groq · qwen3-32b     │          │ users, conversations,        │
                    │ Tools:                    │          │ messages, courses, events    │
                    │  • search_regulations ────┼──┐       └──────────────────────────────┘
                    │  • get_user_grades        │  │
                    │  • get_calendar_events    │  │       ┌──────────────────────────────┐
                    │  • calculate_academic_... │  └─────▶ │ Pinecone (index: estu-index) │
                    └───────────────────────────┘          │ Embeddings: BAAI/bge-m3      │
                                                           │ (Hugging Face Inference API) │
                                                           └──────────────────────────────┘
```

**How a chat request is handled** (`POST /api/chat`):

1. Load or create the conversation and read the last 3 turns.
2. Load the user's academic summary (GPA, courses, upcoming events) from the database.
3. Build a set of tools for this user and a ReAct agent.
4. The agent decides which tools to call: search regulations, then get grades, then compare.
5. Save the answer and its sources, remove duplicate sources, and return them to the client.

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, Vite 6, Tailwind CSS 4, React Router 6, Axios, react-markdown + remark-gfm, lucide-react |
| Backend | FastAPI, SQLAlchemy 2 (async), asyncpg, Pydantic Settings, python-jose (JWT), passlib/bcrypt, slowapi |
| AI / RAG | LangChain, LangGraph (`create_react_agent`), Groq (`qwen/qwen3-32b`), `BAAI/bge-m3` embeddings, Pinecone, PyMuPDF |
| Infrastructure | Vercel (frontend), Render (backend), Supabase Postgres, Pinecone Cloud, Hugging Face Inference |

## Repository Layout

```
.
├── backend/                 # FastAPI service, agent, RAG, ingestion → see backend/README.md
│   ├── app/
│   │   ├── agents/          # ReAct agent + system prompt, per-user tools
│   │   ├── api/             # auth, chat, user, documents routers
│   │   ├── core/            # settings, async DB engine, JWT/security
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # RAG (Pinecone) + DB helper services
│   │   └── transcript_parser.py
│   ├── data/                # Source PDFs (regulations, directives, guides)
│   ├── ingest.py            # PDF → chunks → embeddings pipeline
│   └── main.py              # App entry point + lifespan (DB, RAG, LLM init)
├── frontend/                # React SPA → see frontend/README.md
│   ├── src/
│   │   ├── pages/           # Chat, GPA, Calendar, Profile, Login, Register
│   │   ├── layout/          # AppLayout + Sidebar
│   │   ├── context/         # AuthContext (JWT session)
│   │   ├── router/          # Protected/Public routes
│   │   └── services/api.js  # Axios client with token refresh
│   └── testquestions.json   # 100-question RAG benchmark set
└── README.md
```

## Quick Start

You need **Python 3.11+**, **Node.js 20+**, and API keys for **Groq**, **Hugging Face** and **Pinecone**.

```bash
git clone https://github.com/barisyesil/Reliable_Academic_Assistant_V2_live.git
cd Reliable_Academic_Assistant_V2_live
```

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install langgraph aiosqlite   # currently missing from requirements.txt
# create backend/.env (see backend/README.md)
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

> ⚠️ The frontend API URL is currently hardcoded to the deployed Render backend. To use your local backend, change `BASE_URL` in `frontend/src/services/api.js` to `http://localhost:8000`. See [frontend/README.md](frontend/README.md).

For more detail, see the **[Backend README](backend/README.md)** and the **[Frontend README](frontend/README.md)**.

## Evaluation

[`frontend/testquestions.json`](frontend/testquestions.json) has **100 benchmark questions** built from the ESTÜ regulations. They cover factual, reasoning, multi-hop, edge-case and comparison questions, and are used to measure retrieval and answer quality.

## Status & Roadmap

The project is **still in development**. The main flows work: sign up and log in, chat with the RAG agent, import a transcript, calculate GPA, and use the calendar. These items are known and planned:


## Author

**Barış Yeşil** — Computer Engineering, Eskişehir Technical University
GitHub: [@barisyesil](https://github.com/barisyesil)

## Disclaimer

This is an independent student project. It is **not** an official ESTÜ service. Answers can be wrong or out of date, so always check important decisions against the official university sources and your academic advisor.
