# TruthScan Comprehensive Project Report

## 1. Project Overview
TruthScan is a digital content verification and forensic analysis platform engineered in Python (Flask). The platform empowers investigators, journalists, and everyday users to detect fake news, uncover manipulated media (deepfakes), analyze file integrity, and cross-reference real-time news across multiple global and national sources using Retrieval-Augmented Generation (RAG) and automated machine learning.

---

## 2. Architecture & Tech Stack
- **Backend Framework**: Python, Flask, Jinja2
- **Database Engine**: SQLite with cryptographic forensic logging (`forensic_records`, `users`)
- **Natural Language Processing & ML**:
  - `scikit-learn`: `TfidfVectorizer` + `LogisticRegression`
  - `spaCy`: Named Entity Recognition (NER) via `en_core_web_sm`
- **Generative AI & RAG**:
  - `google-genai` official Python SDK (Gemini 2.5 Flash with structured JSON output schema)
- **Live Aggregation & Search Microservices**:
  - Google News RSS (`pygooglenews`, `feedparser`)
  - NewsAPI Python Client (`newsapi-python`)
  - Inshorts Unofficial API Services (`kehsihba19`, `cyberboysumanjay`)
  - Open-News API Microservice
  - SerpAPI & BeautifulSoup4 for content parsing
- **Security & Integrity**:
  - `werkzeug.security` (PBKDF2 SHA-256 password hashing)
  - `hashlib` (Cryptographic SHA-256 hashing)
  - `imagehash` (Perceptual pHash for visual similarity)
  - `Pillow` (EXIF metadata extraction)
- **Deployment & Networking**:
  - Cloudflare Tunnel (`cloudflared`) for secure public endpoints
  - Git version control (`Keshav018-miet/TruthScan`)

---

## 3. Core Features & Recent Milestones

### A. Live Multi-Source RAG Verification (`multi_source_verifier.py`, `live_search.py`)
- **Concurrent Retrieval Engine**: Built a multi-threaded aggregation worker using `concurrent.futures.ThreadPoolExecutor` that queries five independent news services concurrently (PyGoogleNews, NewsAPI, Inshorts endpoints, and Open-News).
- **Time-Filtered Context Extraction**: Implemented strict 24-48 hour recency filtering to retrieve verified breaking news updates.
- **Deduplication Engine**: Automatically deduplicates returned articles by normalized title similarity and unique URLs.
- **Structured LLM Fact-Checking**: Connects to the official `google-genai` SDK using Gemini 2.5 Flash to compare input claims against retrieved web context, returning strict JSON payloads with `verification_status` (True / Fake / Unverified), `confidence_score` (0-100), detailed reasoning, and source citations.
- **Graceful Web Search Fallback**: If AI synthesis is disabled or API keys are missing, the system gracefully bypasses the LLM step, analyzes direct live news hits, and returns verified status alongside genuine matching article links and summaries without throwing mock errors.

### B. Intelligent News Verification & False-Positive Elimination (`ml_model.py`)
- **Robust Entity Extraction**: Integrated `spaCy` NER to detect `ORG`, `GPE`, `PERSON`, and `EVENT` tags. Included an automated fallback cleaner (stripping punctuation and stop words) so that live search is never aborted due to low entity counts.
- **Live Search Priority**: When mainstream reputable sources (such as Times of India, Hindustan Times, The Hindu, India Today, NDTV, BBC, Reuters) report matching information within 24-48 hours, the system overrides offline TF-IDF predictions and awards a "Verified / Likely True" or "Verified Breaking Event" verdict with high confidence (85% - 92%).
- **Neutral Channel Handling**: Replaced harsh penalties for unverified or missing channels with a balanced "Unverified / Needs Further Context" verdict when live evidence is inconclusive.
- **Official Channel Authentication**: Integrated `ChannelVerifier` database recognizing registered handles and official government domains (PIB, ISRO, DRDO, Defence Squad).

### C. Digital Media Forensics (`utils.py`)
- **Cryptographic File Integrity**: Bit-by-bit comparison of original and suspect files using SHA-256 hashes to detect alterations or tampering.
- **Image & Video Forensics**: Extraction of EXIF camera metadata, color space, dimension specs, perceptual image hashing, and frame-by-frame video forensics.
- **Forensic Chain of Custody**: Every analysis is recorded with a unique UUID, timestamp, file attributes, perceptual and cryptographic hashes, and structured JSON metadata.

### D. User Authentication & Access Control
- **Database Schema**: Secure SQLite storage for user credentials with PBKDF2 password hashing.
- **Session Security**: Custom `@login_required` decorators guarding all dashboard, analysis, and report endpoints.

### E. Responsive Mobile-First UI/UX Overhaul
- **Design System**: Refined minimalist monochrome foundation (`#F9F9FB` background, `#111111` typography, `#F1F1F4` cards, and `#3B4E68` slate-navy accents).
- **Mobile Responsiveness**:
  - Full viewport scaling via `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
  - Automatic single-column grid transformation on screens smaller than 768px.
  - 16px minimum font size on all input fields to prevent browser auto-zoom.
  - Safe text wrapping (`word-break: break-word`) for hashes and source URLs.
  - Minimum 44px finger-friendly touch targets for buttons and collapsible navigation.

---

## 4. Verification Workflow Summary
```
User Claim / Media Input
   |
   +--> [Text News / Claim]
   |        |
   |        v
   |     spaCy NER & Fallback Cleaner
   |        |
   |        v
   |     Multi-Source Live Query (Concurrent ThreadPool: Google News, NewsAPI, Inshorts, Open-News)
   |        |
   |        +--> Reputable Live Matches Found?
   |        |       +--> Yes: Override Offline ML -> "Verified / Likely True" (>85%)
   |        |       +--> No:  Secondary Fallback -> Offline TF-IDF + Channel Credibility
   |        |
   |        v
   |     Gemini 2.5 Flash RAG Synthesis (or Direct Match Fallback)
   |
   +--> [Image / Video / File]
            |
            v
         SHA-256 Hash + Perceptual Hash + EXIF Forensic Extraction
            |
            v
         SQLite Database Registration (Forensic Chain of Custody)
            |
            v
         Comprehensive Forensic Report Generated
```

---

## 5. Conclusion & Next Steps
TruthScan has evolved into an end-to-end, production-ready digital forensic suite. By marrying real-time multi-source news aggregation, intelligent offline machine learning, generative AI fact-checking, and responsive mobile-first design, TruthScan delivers transparent, auditable verification for digital content.
