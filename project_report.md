# TruthScan Project Report

## Project Overview
TruthScan is a comprehensive web-based platform designed for digital content verification and forensic analysis. The core objective of the project is to provide a robust suite of tools for detecting fake news, manipulated media (deepfakes), and file tampering, helping investigators and everyday users verify the authenticity of digital content.

## Features & Implementation Progress

### 1. Backend Architecture (Flask & SQLite)
- **Framework**: Built a robust web application using Python and the Flask framework.
- **Database (`database.py`)**: Designed an SQLite database to store user credentials (`users` table) and forensic analysis reports (`forensic_records` table) securely.
- **Routing**: Implemented structured routing for dashboards, history viewing, and individual forensic reports.

### 2. User Authentication System
- **Security**: Integrated `werkzeug.security` for cryptographic password hashing (pbkdf2:sha256).
- **Session Management**: Implemented secure session tracking to keep users logged in.
- **Access Control**: Built a custom `@login_required` decorator to restrict access to sensitive analysis tools and history logs, automatically redirecting unauthorized users to the login screen.

### 3. Machine Learning & Natural Language Processing
- **Fake News Detection (`ml_model.py`)**: Developed an NLP pipeline utilizing `TfidfVectorizer` and `LogisticRegression` to classify text as "Potentially Fake" or "Potentially Real".
- **Source/Channel Verification Engine**: Built a `ChannelVerifier` module that checks source links (e.g., YouTube, Telegram, Twitter) against a pre-registered database of official channels (such as Defence Squad and government domains). The ML model adjusts its final confidence score based on the credibility of the source channel.

### 4. Forensic Analysis Modules (`utils.py`)
- **Image Analysis**: Calculates SHA-256 and Perceptual hashes to detect exact or visual duplicates, and extracts hidden EXIF metadata.
- **Video Analysis**: Processes video frames for deepfake detection signatures and metadata extraction.
- **File Integrity Checker**: Allows users to upload two files to perform a bit-by-bit cryptographic comparison (SHA-256) to verify if a file has been altered or tampered with.

### 5. Frontend & UI Redesign
- **Aesthetic Upgrade**: Transitioned to a mature, high-end minimalist light theme using a monochrome foundation (clean white `#F9F9FB`, deep charcoal `#111111`, and soft light-gray cards `#F1F1F4`).
- **Accent Details**: Applied an elegant slate-navy (`#3B4E68`) for interactive elements and buttons.
- **Dynamic Views**: Built Jinja2 templates (`base.html`, `login.html`, `register.html`, `report.html`) that dynamically update based on the user's session state and display verification badges (e.g., [Verified Official Channel]) seamlessly.

### 6. Deployment & Collaboration
- **Public Tunneling**: Configured `cloudflared` to expose the local Flask server to the public internet securely, generating live URLs (e.g., trycloudflare.com) for external access and testing.
- **Version Control**: Initialized a Git repository (`Keshav018-miet/TruthScan`), committed all features, and pushed them to GitHub, establishing a standard branching and pull-request workflow for multi-user collaboration.

## Conclusion
To date, TruthScan has evolved from a basic concept into a full-featured prototype with a secure authentication system, an intelligent ML-driven text analysis engine backed by source verification, cryptographic file integrity checking, and a polished, professional user interface ready for team collaboration.
