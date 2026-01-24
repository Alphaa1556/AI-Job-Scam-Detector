# AI-Job-Scam-Detector

AI-powered system to detect fake job and internship offers using document analysis, OCR, and multi-signal scam detection logic.

---

## Problem Statement

Students are increasingly targeted by fake job and internship scams involving fraudulent offer letters, fake companies, and pay-to-work schemes. These scams often appear highly professional and cause financial loss and data theft.

---

## Solution

We propose an AI-powered web application that analyzes job or internship offer letters (PDFs and images) and detects scam indicators using OCR, rule-based analysis, and online presence verification.  
The system generates a **risk score** along with a **clear verdict and reasons** to help users make informed decisions.

---

## Features

- Scam keyword & pattern detection  
- Risk score generation (Safe / Suspicious / High Risk)  
- Offer letter analysis using OCR (PDF & Image support)  
- Company website presence checking  
- LinkedIn presence verification  
- Logo authenticity check (logo present but no verifiable online presence)  
- Contact risk detection (email / phone / messaging patterns)  
- Detailed scam reasons with final verdict  

---

## Google Technologies Used

- Google technologies explored during design & planning phase  
- (Current implementation uses open-source OCR and verification logic due to billing constraints)

---

## Tech Stack

- **Frontend:** HTML, CSS (UI designed using Figma / Canva)  
- **Backend:** Python (Flask)  
- **OCR:** Tesseract OCR, PyPDF2  
- **Image Processing:** OpenCV, Pillow, NumPy  
- **AI Logic:** Rule-based scam detection & multi-signal risk scoring  

---

## Team Contributions

- **Member 1:**  
  PPT preparation, documentation, and presentation

- **Member 2:**  
  Frontend development (UI design & layout)

- **Member 3:**  
  Frontend development (integration & user interaction)

- **Member 4:**  
  Backend development  
  - File handling & OCR  
  - Scam detection logic  
  - Website & LinkedIn verification  
  - Logo authenticity analysis  
  - Risk scoring & verdict generation

---

## Project Status

This project is completed as part of a **hackathon submission**.  
Core backend logic and frontend integration are fully functional, with scope for future AI and cloud-based enhancements.

---

⚠️ *This project is intended for educational and hackathon demonstration purposes only.*
