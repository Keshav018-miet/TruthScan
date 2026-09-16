# TruthScan - Digital Content Verification & Forensic Analysis System

TruthScan is a student-level cybersecurity and digital forensics web application. It is designed to analyze suspicious news, images, and videos to verify their authenticity and integrity.

## Features
- **News Analysis:** Uses TF-IDF and Logistic Regression to analyze text for misinformation.
- **Image Analysis:** Extracts EXIF metadata, generates SHA-256 and Perceptual Hashes, and simulates deepfake detection.
- **Video Analysis:** Extracts frames, calculates hashes, and simulates video manipulation detection.
- **File Integrity Check:** Cryptographically compares two files using SHA-256 to ensure exact matches.
- **Forensic History & Reporting:** Stores all analysis logs in a local SQLite database and generates detailed forensic reports establishing a chain of custody.

## Tech Stack
- **Backend:** Python + Flask
- **Database:** SQLite
- **Machine Learning / NLP:** scikit-learn
- **Hashing & Processing:** hashlib, imagehash, Pillow, opencv-python, ExifRead
- **Frontend:** HTML, CSS, JavaScript (Vanilla)

## Installation & Setup

1. **Prerequisites:** Make sure you have Python 3.8+ installed.
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Application:**
   ```bash
   python app.py
   ```
4. **Access the App:** Open your web browser and navigate to `http://127.0.0.1:5000`.

## Architecture Note
The Machine Learning models for Images and Videos are currently configured as a plug-and-play architecture for future integration of heavy AI models (e.g., PyTorch). Currently, they use simulated heuristics for demonstration purposes, while text analysis uses a real local scikit-learn model trained in-memory.
