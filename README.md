# Memory Bank Dashboard

Read-only web dashboard for viewing [Memory Bank](https://github.com/andriispivakelectrodosg/ai-infra) project state -- core files, tasks, lessons learned, ADRs, and features.

## Quick Start

### Docker (recommended)

```bash
cd memory-bank-dashboard
docker compose up
# Open http://localhost:5000
```

Requires the parent repo structure:

```
ai-infra/
├── memory-bank/          # mounted as /memory-bank
├── docs/lessons-learned/ # mounted as /lessons-learned (optional)
├── docs/adrs/            # mounted as /adrs (optional)
├── features/             # mounted as /features (optional)
└── memory-bank-dashboard/
```

### Without Docker

```bash
cd memory-bank-dashboard
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
# Open http://127.0.0.1:5000
```

## Configuration

All settings via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_BANK_DIR` | `../memory-bank` | Path to memory-bank directory |
| `LESSONS_DIR` | `../docs/lessons-learned` | Path to lessons-learned directory |
| `ADRS_DIR` | `../docs/adrs` | Path to ADRs directory |
| `FEATURES_DIR` | `../features` | Path to features directory |
| `HOST` | `127.0.0.1` | Bind address (`0.0.0.0` in Docker) |
| `PORT` | `5000` | Listen port |
| `FLASK_DEBUG` | `1` | Debug mode (`0` in Docker) |

## Features

- **Collapsible sidebar sections** -- click headings to expand/collapse, state saved in localStorage
- **Sidebar navigation** -- Core Files, Tasks, Lessons Learned, ADRs, Features
- **Item counts** -- badge on each section heading showing number of files
- **Markdown rendering** -- tables, code blocks, checkboxes (via marked.js)
- **Dark/light theme** -- toggle in header, saved in localStorage
- **Task drill-down** -- clickable `[TASK001]` references in task index
- **Lesson drill-down** -- clickable `LL-001` references in lesson index
- **Breadcrumb navigation** -- on task, lesson, and ADR detail pages
- **Auto-refresh** -- polls every 30 seconds for file changes
- **Path traversal protection** -- all file API endpoints are guarded

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard SPA |
| `GET /api/files` | List core memory-bank files |
| `GET /api/file/<path>` | Read a memory-bank file |
| `GET /api/tasks` | List task files |
| `GET /api/lessons` | List lesson-learned files |
| `GET /api/lesson/<path>` | Read a lesson-learned file |
| `GET /api/adrs` | List ADR files |
| `GET /api/adr/<path>` | Read an ADR file |
| `GET /api/features` | List feature files |
| `GET /api/feature/<path>` | Read a feature file |

## Architecture

```
memory-bank-dashboard/
├── app.py              # Flask backend (10 routes)
├── Dockerfile          # python:3.12-slim
├── docker-compose.yml  # Single-command startup
├── requirements.txt    # flask>=3.0
└── templates/
    └── index.html      # SPA (inlined CSS + JS)
```
