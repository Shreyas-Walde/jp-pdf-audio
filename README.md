# Japanese PDF Audio Reader

An open-source web-based learning tool that converts Japanese textbook PDFs into a structured reading and listening experience.

## Overview

Japanese PDF Audio Reader allows learners to:
- Read Japanese text chapter by chapter
- Listen to native-quality Japanese audio at both chapter and sentence level
- Study without paying for subscriptions or APIs

The system preprocesses content once and serves it efficiently to many users without repeated computation or cost.

## Architecture

The system is divided into two isolated domains:

### Processing Domain (Python)
Runs offline or as a background job. Handles:
- PDF ingestion
- Text extraction
- Chapter detection
- Sentence segmentation
- Audio generation (via Voicevox)
- Metadata persistence

### Serving Domain (Next.js)
Runs continuously and serves users. Handles:
- Display text
- Stream audio
- Serve metadata

## Project Structure

```
jp-pdf-audio/
├── processor/              # Python processing pipeline
│   ├── __init__.py
│   ├── config.py           # Configuration constants
│   ├── database.py         # SQLite operations
│   ├── pipeline.py         # Main orchestration
│   ├── ingest_pdf.py       # PDF ingestion
│   ├── extract_text.py     # Text extraction
│   ├── normalize_text.py   # Text normalization
│   ├── detect_chapters.py  # Chapter detection
│   ├── segment_sentences.py # Sentence segmentation
│   ├── generate_tts.py     # TTS generation
│   ├── stitch_audio.py     # Audio stitching
│   └── persist_metadata.py # Metadata storage
├── web/                    # Next.js frontend
│   └── src/
│       ├── app/            # App router pages & API
│       └── components/     # React components
├── data/                   # Generated content
│   ├── books/              # Original PDFs
│   └── audio/              # Generated audio files
│       ├── sentences/      # Per-sentence audio
│       └── chapters/       # Per-chapter audio
├── requirements.txt        # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- [Voicevox](https://voicevox.hiroshiba.jp/) - Local TTS engine
- ffmpeg - Audio processing
- Tesseract OCR with Japanese pack (optional, fallback only)

## Quick Start

### 1. Install Python dependencies

```bash
uv sync
```

### 2. Install frontend dependencies

```bash
cd web
npm install
```

### 3. Start Voicevox

Download and run Voicevox from [voicevox.hiroshiba.jp](https://voicevox.hiroshiba.jp/). It runs on port 50021.

### 4. Process a PDF

```bash
uv run python -m processor.pipeline /path/to/book.pdf --title "Book Title"
```

### 5. Start the web server

```bash
cd web
npm run dev
```

Visit `http://localhost:3000` to view the books.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Processing | Python, pdfplumber, spaCy, Voicevox |
| Database | SQLite |
| Audio | Opus codec (.ogg) |
| Frontend | Next.js 14 (App Router) |

## License

Open source. See LICENSE file for details.
