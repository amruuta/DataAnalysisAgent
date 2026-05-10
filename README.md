# 📊 DataAnalysisAgent

An intelligent, full-stack data analysis agent that lets users ingest datasets, chat with an AI analyst, and generate visualizations and reports.

## 🖼️ UI Preview

![Login](Screenshots/1-login.png)
![Chat](Screenshots/2-chat.png)
![CSV Ingestion](Screenshots/3-data-ingestion-csv.png)
![Database Ingestion](Screenshots/4-data-ingestion-db.png)
![Charts + PPTX](Screenshots/5-chat-max-ppt-graph.png)

## ✨ Key Features

- 🤖 **AI chat for analysis** with tool-backed SQL queries and reasoning.
- 📈 **Plotly charts** generated on-demand from query results.
- 📥 **CSV/Excel ingestion** and database connection ingestion.
- 🗂️ **Session persistence** with Redis caching and Postgres snapshots.
- 📤 **Exports** to CSV and PPTX for reports and stakeholder sharing.
- 🔐 **Secure auth** with HttpOnly JWT cookies and hashed passwords.

## 🧱 Architecture Overview

- **Frontend**: React + Vite + TypeScript, Redux Toolkit, Tailwind CSS.
- **Backend**: FastAPI, SQLAlchemy, Alembic migrations.
- **AI/Agents**: LangChain + DeepAgents + LangGraph (Redis checkpointer).
- **Storage**: PostgreSQL for users/data sources/sessions, Redis for cache/checkpoints.
- **Files**: Uploaded datasets in `uploads/`, exports in `exports/`.

## 🌐 API Overview

### Auth (`/auth`)

- `POST /auth/register` - Create a user account.
- `POST /auth/login` - Login and receive an HttpOnly JWT cookie.
- `POST /auth/logout` - Clear the auth cookie.
- `GET /auth/me` - Return the authenticated user profile.

### Chat (`/chat`)

- `GET /chat/sessions` - List chat sessions for the current user.
- `GET /chat/sessions/{thread_id}` - Fetch a session and restore Redis state if needed.
- `POST /chat/sessions/{thread_id}/save` - Persist cached history/checkpoints to Postgres.
- `POST /chat` - Send a chat prompt; returns response, thread ID, and chart payloads.

### Ingestion (`/ingest`)

- `POST /ingest/file` - Upload CSV/XLS/XLSX and register as a data source.
- `POST /ingest/database` - Register an external database connection.
- `GET /ingest/datasources` - List data sources (optional `source_type=file|database`).
- `GET /ingest/datasources/{data_source_id}` - Fetch a single data source.

### Health & Exports

- `GET /health` - Checks Postgres, Redis, and LangGraph checkpointer status.
- `GET /exports/*` - Static access to CSV/PPTX exports.

## 🔐 Authentication & Security

- **JWT cookie auth**: Auth tokens are stored in an HttpOnly cookie (`AUTH_COOKIE_NAME`).
- **Cookie hardening**: `SameSite=Lax` and `Secure` is configurable via `COOKIE_SECURE`.
- **Password hashing**: Bcrypt via `passlib` with PBKDF2 fallback.
- **Token validation**: JWT decoded on every request; inactive users are blocked.
- **Secret storage**: External DB URLs are encrypted using Fernet (derived from `JWT_SECRET_KEY`).
- **CORS**: Controlled by `CORS_ORIGINS`; frontend sends cookies with `credentials: include`.

## 🗄️ Data & Storage Model

- **Postgres tables**:
  - `users` - login identity and password hash.
  - `data_sources` - file/database sources per user.
  - `chat_sessions` - session metadata, history, and checkpoint snapshots.
- **File ingestion**:
  - CSV/XLS/XLSX stored per user in `uploads/`.
  - Ingested files are written to Postgres as user-scoped tables.
- **Database ingestion**:
  - External DB URLs validated with a `SELECT 1` probe.
  - Optional `table_name` controls scoping; default is `all_tables`.
- **Redis**:
  - Chat histories, session metadata, dirty session tracking.
  - LangGraph checkpointer state per thread.

## 🧠 Agentic Workflow

- **SQL analysis** through LangChain SQL toolkit.
- **Plotly generation** tool returns chart JSON to the frontend.
- **CSV export** tool writes to `exports/` with unique filenames.
- **PPTX generator** builds a themed slide deck (4-7 slides typical).
- **Chart capture** collects Plotly payloads per agent invocation.

## 🚀 Project Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for Postgres + Redis)

### 1) Infrastructure (Postgres + Redis)

```bash
# PostgreSQL
docker run --name data-agent-pg \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin \
  -e POSTGRES_DB=agent_db \
  -p 5432:5432 -d postgres

# Redis
docker run --name data-agent-redis -p 6379:6379 -d redis
```

### 2) Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### Backend Environment Variables (`backend/.env`)

```env
DATABASE_URL=postgresql://admin:admin@localhost:5432/agent_db
REDIS_URL=redis://localhost:6379
AI_API_KEY=
AI_MODEL=
JWT_SECRET_KEY=change-this-secret-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
AUTH_COOKIE_NAME=daa_access_token
COOKIE_SECURE=false
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PUBLIC_BASE_URL=http://127.0.0.1:8000
UPLOAD_DIR=uploads
EXPORT_DIR=exports
SESSION_TTL_SECONDS=3600
SCHEDULER_INTERVAL_SECONDS=300
```

#### Database Migrations (Alembic)

```bash
# Generate a migration (only when models change)
alembic revision --autogenerate -m "create data_sources table"

# Apply migrations
alembic upgrade head
```

#### Run the Backend

```bash
uvicorn app.main:app --reload
```

OpenAPI docs: `http://127.0.0.1:8000/docs`

### 3) Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

#### Frontend Environment Variables (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Frontend Scripts

```bash
npm run dev      # start dev server
npm run build    # production build
npm run preview  # preview built app
npm run lint     # lint source
```

## 🩺 Health Checks

- `GET /health` verifies Postgres, Redis, and the LangGraph checkpointer.

## 🧰 Utilities

- **CSV ➜ SQLite converter**: [sqlite/csv_sqlite_converter.py](sqlite/csv_sqlite_converter.py)
  - Example:
    ```bash
    python sqlite/csv_sqlite_converter.py sqlite/bestsellers\ with\ categories.csv
    ```

## ✅ What’s Included

- 🔑 Auth + protected routes (frontend + backend)
- 📁 File upload + data source registry
- 💬 Chat sessions with caching + autosave
- 📈 Plotly visualizations
- 📤 CSV/PPTX export pipelines

## 📝 Notes

- `COOKIE_SECURE=true` is recommended in production (HTTPS only).
- Ensure Docker services are running before starting the backend.
- Exports are served under `/exports` (e.g., `http://127.0.0.1:8000/exports/...`).
