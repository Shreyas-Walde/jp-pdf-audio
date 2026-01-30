# Japanese PDF Audio Reader
## Technical Specification and Data Schemas

---

## 1. Purpose of This Document

This document defines:

- System architecture
- Processing pipeline
- Data models and schemas
- File structure
- API contracts
- Execution flow

It is designed to be:

- Deterministic
- Open source
- Offline friendly
- Cheap to host
- Easy for AI coding agents to execute

---

## 2. System Overview

The system converts a Japanese textbook PDF into a structured, audio enabled reading experience.

Core principles:

- Heavy processing happens once
- Audio is generated once and reused
- Serving is fast and lightweight
- No real time AI usage

---

## 3. High Level Architecture

### Two isolated domains

### A. Processing Domain
Runs offline or as a background job.

Responsibilities:

- PDF ingestion
- Text extraction
- Chapter detection
- Sentence segmentation
- Audio generation
- Metadata persistence

### B. Serving Domain
Runs continuously and serves users.

Responsibilities:

- Display text
- Stream audio
- Serve metadata

---

## 4. Processing Pipeline Specification

### 4.1 Pipeline Entry Point

File  
processor/pipeline.py

Input:

- PDF file path
- Book metadata

Output:

- Structured metadata in database
- Audio files in storage
- Book status set to READY

---

### 4.2 Step 1: PDF Ingestion

File  
processor/ingest_pdf.py

Responsibilities:

- Accept PDF
- Generate unique book_id
- Store original PDF

Output:

- Stored PDF path
- book_id

---

### 4.3 Step 2: Text Extraction

File  
processor/extract_text.py

Primary method:

- pdfplumber

Fallback:

- Tesseract OCR with Japanese language pack (jpn)

Decision rule:

If extracted text length is below threshold, use OCR.

Output:

- Raw extracted Japanese text

---

### 4.4 Step 3: Text Normalization

File  
processor/normalize_text.py

Responsibilities:

- Normalize Unicode
- Remove layout artifacts
- Preserve hiragana, katakana, kanji, and furigana if present

Output:

- Clean normalized text

---

### 4.5 Step 4: Chapter Detection

File  
processor/detect_chapters.py

Method:

- Regex based heuristics

Examples:

- 第1課
- 第三章
- Lesson 2

Output structure:

- chapter_id
- title
- chapter text

---

### 4.6 Step 5: Sentence Segmentation

File  
processor/segment_sentences.py

Primary tool:

- spaCy ja_core_news_sm

Fallback:

- SudachiPy

Sentence is the smallest atomic unit.

Output structure:

- sentence_id
- sentence text

---

### 4.7 Step 6: Text to Speech Generation

File  
processor/generate_tts.py

Engine:

- Coqui TTS Japanese model

Rules:

- Generate audio once
- One file per sentence
- Deterministic output

Output path:

- audio/sentences/{sentence_id}.wav

---

### 4.8 Step 7: Chapter Audio Stitching

File  
processor/stitch_audio.py

Method:

- Concatenate sentence audio files in order

Output path:

- audio/chapters/{chapter_id}.mp3

---

### 4.9 Step 8: Metadata Persistence

File  
processor/persist_metadata.py

Stores:

- Book metadata
- Chapter metadata
- Sentence metadata
- Audio file paths

---

## 5. Data Storage Specification

### 5.1 Database Choice

- SQLite for MVP
- PostgreSQL optional for future scaling

---

### 5.2 Database Schema

### Table: books

Fields:

- id (TEXT, primary key)
- title (TEXT)
- language (TEXT)
- pdf_path (TEXT)
- status (TEXT)
- created_at (TIMESTAMP)

---

### Table: chapters

Fields:

- id (TEXT, primary key)
- book_id (TEXT, foreign key)
- title (TEXT)
- order_index (INTEGER)
- audio_path (TEXT)

---

### Table: sentences

Fields:

- id (TEXT, primary key)
- chapter_id (TEXT, foreign key)
- order_index (INTEGER)
- text (TEXT)
- audio_path (TEXT)

---

## 6. File Storage Structure

data/
books/
- {book_id}.pdf

audio/
sentences/
- {sentence_id}.wav

chapters/
- {chapter_id}.mp3

metadata.db

---

## 7. Serving Layer Specification

### 7.1 Frontend

Framework:

- Next.js

Responsibilities:

- Book list
- Chapter list
- Text rendering
- Audio playback

Rendering strategy:

- Static generation or incremental static regeneration
- Client side audio playback

---

### 7.2 Backend API

Read only API.

Endpoints:

GET /api/books  
Returns list of available books.

GET /api/books/{book_id}/chapters  
Returns chapters for a book with chapter audio paths.

GET /api/chapters/{chapter_id}  
Returns sentences with sentence level audio paths.

---

## 8. Execution Model

### Processing

- Manual or CLI triggered
- One book processed at a time
- Can run locally or on a cheap VM

### Serving

- Static hosting
- Cheap object storage
- Near zero compute cost

---

## 9. Error Handling Strategy

- Fail fast during processing
- Log every pipeline step
- Book marked FAILED if any step fails
- No partial serving of incomplete books

---

## 10. Security and Legal Notes

- Admin only ingestion
- Public read access
- Copyright responsibility lies with the operator
- Open source code, not copyrighted content

---

## 11. Non Goals

- No chatbots
- No translation
- No grammar AI
- No user edits
- No real time inference

---

## 12. Ready for Agentic Execution

This document is:

- Deterministic
- Step ordered
- File oriented
- Schema defined

Suitable for agentic IDEs such as Cursor, Antigravity, Claude Code, and Copilot Workspace.
