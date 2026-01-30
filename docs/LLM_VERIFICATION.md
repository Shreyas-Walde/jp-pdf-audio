LLM verification design document (.md)

Below is a single Markdown file, written exactly so:

You can save it as LLM_VERIFICATION.md

Agentic IDEs can read it

Future contributors understand the intent

No ambiguity about architecture

Everything is inside one code block, as requested.

# LLM Verification Layer for PDF-Faithful Japanese Reader

## Purpose

This document describes how an LLM is used to verify and clean text extracted from Japanese textbook PDFs.

The LLM is NOT used to generate content.
The LLM is used ONLY as a verifier and cleaner.

The goal is to:
- Preserve PDF layout exactly
- Produce linguistically correct Japanese sentences
- Generate high-quality sentence-level audio
- Avoid garbage, merged sentences, and layout artifacts

---

## Core Principles

1. Page is the atomic unit
2. Layout is the source of visual truth
3. Sentences are the source of audio truth
4. LLM never modifies layout
5. LLM never paraphrases or invents text
6. TTS is generated only after verification

---

## High-Level Pipeline

PDF
→ Page-level layout extraction (pdfplumber)
→ Raw page JSON (untrusted)
→ LLM verification (page-scoped)
→ Verified page JSON (trusted)
→ Sentence-level TTS
→ UI renders page layout faithfully

---

## Page-Level Data Model

Each PDF page is stored as a separate JSON file.

Example: data/raw_pages/page_001.json

```json
{
  "book_id": "nihongo_shoho",
  "page_number": 1,
  "lines": [
    { "line_id": "l1", "text": "I." },
    { "line_id": "l2", "text": "わたしは にほんじんです O" },
    { "line_id": "l3", "text": "わたしは はやしです" }
  ]
}


This file is considered UNTRUSTED input.

Role of the LLM

The LLM operates on ONE page at a time.

The LLM:

Detects correct Japanese sentence boundaries

Removes noise characters and layout artifacts

Restores obvious sentence-ending punctuation

Ignores page headers and non-content markers

Outputs clean, linguistically valid sentences

The LLM must NOT:

Reorder content

Change layout

Paraphrase text

Add new information

Translate text

LLM Output Contract

The LLM must return valid JSON ONLY.

{
  "sentences": [
    {
      "clean_text": "わたしは にほんじんです。",
      "confidence": 0.97
    }
  ]
}


If text is too corrupted to recover, it must be discarded.

Verified Page JSON

After mapping sentences back to layout lines, the verified page JSON becomes:

{
  "book_id": "nihongo_shoho",
  "page_number": 1,
  "verified": true,
  "lines": [
    {
      "line_id": "l2",
      "text": "わたしは にほんじんです。",
      "sentence_id": "s1"
    }
  ],
  "sentences": [
    {
      "sentence_id": "s1",
      "clean_text": "わたしは にほんじんです。",
      "audio_path": "/audio/page_001_s1.mp3",
      "confidence": 0.97
    }
  ]
}

TTS Gating Rules

A sentence is eligible for TTS ONLY if:

It came from LLM verification

Confidence ≥ configured threshold (example: 0.9)

It belongs to exactly one page

Invalid or low-confidence sentences:

Do not generate audio

Are logged for review

Model Choice

Recommended LLMs:

GPT-4o-mini

Claude 3 Haiku

Gemini 2.0 Flash (via OpenRouter)

Gemini 2.0 Flash is acceptable if:

Temperature is set very low

Output is schema-validated

Retries are implemented for malformed JSON

Safety and Cost Controls

One LLM call per page

Cache verified pages

Never re-verify unchanged pages

Enforce strict JSON schema validation

Fail loudly on malformed output

What This System Guarantees

UI matches PDF line-for-line

Sentence audio matches what the learner sees

Garbage text never reaches TTS

Pages can be audited independently

The system is deterministic and reproducible

Non-Goals

Translation

Grammar explanation

Summarization

Chat or tutoring

Real-time inference

This layer exists purely to ensure text correctness and audio quality.