# Japanese PDF Audio Reader - Railway Deployment

## Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

## Services

### 1. Next.js Frontend (`/web`)

Serves the web UI and audio files.

### 2. Python Worker (`/processor`)

Processes PDFs, generates TTS audio.

### 3. PostgreSQL Database

Stores book/chapter/sentence metadata.

## Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-xxx

# Optional
OPENROUTER_MODEL=google/gemini-2.0-flash-001
```

## Volumes

- `/app/data` - Persistent storage for PDFs and audio files

## Adding New PDFs

```bash
# SSH into Railway container
railway run python -m processor.pipeline "/path/to/book.pdf" --title "Book Title"
```
