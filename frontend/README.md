# Data Analysis Agent Frontend

Frontend for the Data Analysis Agent platform, built with:

- React + TypeScript (Vite)
- Tailwind CSS
- Redux Toolkit + React Redux (state management)
- React Router (separate URLs for pages)

## Features

- Top navigation with two pages:
  - `/chat`
  - `/data-ingestion`
- Chat workspace:
  - Select datasource
  - Start new conversations
  - Send chat prompts to backend `/chat` API
- Data ingestion workspace:
  - Drag-and-drop CSV upload
  - Database connection form
  - Mutually exclusive ingestion modes (CSV or DB)
  - Live datasource refresh after successful ingestion

## Project Structure

```text
src/
  app/
    AppRoutes.tsx
    hooks.ts
    store.ts
  components/
    common/
    layout/
    navigation/
  features/
    chat/
    datasources/
    ingestion/
  pages/
    ChatPage.tsx
    DataIngestionPage.tsx
  services/
    apiClient.ts
    chatApi.ts
    datasourceApi.ts
    ingestionApi.ts
  types/
```

## Prerequisites

- Node.js 20+
- npm 10+
- Backend API running (FastAPI)

## Local Setup

1. Install dependencies:

```bash
npm install
```

2. Configure environment:

```bash
cp .env.example .env
```

Default value:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

3. Start development server:

```bash
npm run dev
```

4. Open browser:

- http://localhost:5173/chat
- http://localhost:5173/data-ingestion

## Available Scripts

- `npm run dev` - Start Vite dev server
- `npm run build` - Type-check and build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Backend API Expectations

This frontend uses these backend endpoints:

- `GET /ingest/datasources`
- `GET /ingest/datasources/{id}`
- `POST /ingest/file` (multipart form-data with `name` and `file`)
- `POST /ingest/database`
- `POST /chat`

## Notes for Scaling

- Feature-based Redux slices are separated by domain.
- API calls are isolated in `services/`.
- Shared UI is in `components/`.
- Route pages are under `pages/` and can be expanded without changing core app wiring.
