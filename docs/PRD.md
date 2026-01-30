# Japanese PDF Audio Reader
## Product Requirements Document (PRD)

---

## 1. Product Overview

Japanese PDF Audio Reader is an open source web based learning tool that converts Japanese textbook PDFs into a structured reading and listening experience.

The product allows learners to read Japanese text chapter by chapter and listen to native quality Japanese audio at both chapter and sentence level.

The system is designed to preprocess content once and serve it efficiently to many users without repeated computation or cost.

---

## 2. Problem Statement

Japanese learners often study from PDF textbooks that do not include native quality audio or only provide limited listening material.

Existing solutions have one or more of the following problems:

- Flat audio for entire documents without structure
- Robotic or non native speech
- Paid APIs and recurring costs
- No sentence level playback
- Poor support for Japanese text structure

This makes it difficult for learners to practice listening comprehension, pronunciation, and natural conversational rhythm.

---

## 3. Target Users

### Primary Users

- Japanese language learners
- JLPT N5 to N3 level
- Users comfortable with hiragana and katakana
- Users with basic kanji vocabulary knowledge
- Self learners studying from textbooks

### Secondary Users

- Language study groups
- Educators sharing learning material
- Open source contributors

---

## 4. User Goals

Users want to:

- Upload or access a Japanese textbook PDF
- Read structured chapters
- Listen to native sounding Japanese audio
- Replay individual sentences
- Learn natural pronunciation and rhythm
- Study without paying for subscriptions or APIs

---

## 5. Use Cases

### Core Use Case

A learner uploads a Japanese textbook PDF.  
The system processes it once and makes it available as a structured book with text and audio.  
The learner opens chapters, reads text, and plays sentence or chapter audio.

### Secondary Use Case

Multiple users access the same processed book and consume the content without triggering new processing or costs.

---

## 6. MVP Scope

### In Scope

- Upload a Japanese PDF
- Extract text from text based PDFs
- Ignore images
- Preserve Japanese characters and furigana if present
- Detect chapters
- Segment text into sentences
- Generate native sounding Japanese audio
- Store audio permanently
- Display text and audio in a web interface
- Sentence level and chapter level audio playback

---

## 7. Out of Scope for MVP

- User accounts and authentication
- Text editing or corrections
- Translations
- Grammar explanations
- Vocabulary annotations
- Real time text to speech
- Mobile applications
- Multi language support
- AI chat or tutoring features

---

## 8. Functional Requirements

### Content Ingestion

- The system shall allow an admin to upload a PDF
- Each PDF shall be treated as a single book
- PDFs shall be immutable after processing

### Text Processing

- The system shall extract Japanese text from the PDF
- OCR shall only be used as a fallback
- Text shall be normalized and cleaned
- Chapters shall be detected using heuristics
- Sentences shall be segmented accurately

### Audio Generation

- The system shall generate Japanese audio using open source TTS
- Audio shall sound native and conversational
- Audio shall be generated once per sentence
- Audio shall be reused for all users

### Content Serving

- Users shall be able to view a list of books
- Users shall be able to view chapters within a book
- Users shall be able to read text per chapter
- Users shall be able to play sentence level audio
- Users shall be able to play chapter level audio

---

## 9. Non Functional Requirements

- Fully open source
- No paid APIs or services
- Deterministic processing
- Low hosting cost
- Fast page load times
- Audio playback without lag
- System must work with static or near static hosting

---

## 10. Assumptions

- PDFs are mostly text based
- Content does not change after processing
- Admin controls which books are added
- Users consume content only
- Processing can take several minutes per book

---

## 11. Constraints

- No real time AI inference
- Limited compute budget
- Open source only tools
- Hosting should be free or near free
- Audio storage must scale efficiently

---

## 12. Success Metrics

The MVP is considered successful if:

- A full Japanese textbook can be processed end to end
- Chapters and sentences are correctly displayed
- Sentence level audio plays correctly
- Chapter level audio plays correctly
- Multiple users can access the same book without recomputation
- The system runs without paid services

---

## 13. Risks and Mitigations

### Risk: Poor OCR accuracy
Mitigation: Prefer text extraction and only fallback to OCR.

### Risk: Unnatural TTS output
Mitigation: Use high quality open source Japanese TTS models and test with learners.

### Risk: Large audio storage size
Mitigation: Use compressed formats for serving and reuse audio.

### Risk: Copyright issues
Mitigation: Content responsibility lies with the operator, not the software.

---

## 14. Future Enhancements

These are explicitly not part of MVP:

- Sentence highlighting during playback
- Playback speed control
- Multiple voice options
- Furigana toggling
- Offline downloads
- User progress tracking
- Grammar and vocabulary tools

---

## 15. Product Philosophy

This product prioritizes:

- Learning effectiveness over feature count
- Determinism over experimentation
- Preprocessing over real time computation
- Open access over monetization

---

## 16. Readiness for Technical Implementation

This PRD is written to align directly with:

- Technical specification documents
- Agentic IDE workflows
- Open source development practices

It defines a clear MVP boundary and execution path.
