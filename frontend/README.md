# SynapseFlow 2026 — Studio (React + TypeScript)

Landing UI for **Studio**: visualize any process from a topic (System Design Roadmap) or your own detailed input.

## Setup

```bash
npm install
```

## Dev

```bash
npm run dev
```

Open **http://localhost:5173**. Ensure the FastAPI backend is running on **http://127.0.0.1:8000** (e.g. `./start.sh` from the project root). Vite proxies `/api`, `/studio`, `/media`, `/dashboard`, etc. to the backend.

## Build

```bash
npm run build
```

Output is in `dist/`. The backend serves this at `/` when present (see root README).

## Features

- **Landing = Studio** — Start by selecting a topic from [systemdr.substack.com](https://systemdr.substack.com) or typing/pasting your own concept.
- **Topic list** — Fetched from `GET /api/topics` (System Design Interview Roadmap topics).
- **Detailed input** — Optional description or full article; combined with selected topic when both are set.
- **Generate** — Calls `POST /studio/generate`; shows SVG preview, steps, and script.
- **Narrate** — TTS via `POST /studio/narrate` (Gemini).
- **Dashboard** — Link to `/dashboard` for the classic dashboard (videos, jobs, quick generate).
