# Pak-MedTriage: AI-Powered Multimodal Clinical Decision Support System

> **CSS AI Bootcamp 2026 Capstone Project**  
> **Author:** Artificial Intelligence Student, University of Peshawar  
> **Target Deployment Environment:** Basic Health Units (BHUs) & Rural Health Clinics in Khyber Pakhtunkhwa (KP), Pakistan  

---

## 📋 Executive Summary
In rural healthcare settings across Khyber Pakhtunkhwa, Basic Health Units (BHUs) face severe resource constraints, high patient loads, and delayed specialist referrals. Local healthcare workers often operate under time pressure across regional linguistic barriers (Pashto and Urdu). 

**Pak-MedTriage** is an agentic, multimodal clinical decision support system designed to streamline emergency triage at the point of care. By combining speech-to-text translation, vision-based wound analysis, fast-path inference orchestration, and clinical safety guardrails, Pak-MedTriage transforms unstructured clinical inputs (spoken local history and wound images) into standardized triage classifications (**RED**, **YELLOW**, **GREEN**) accompanied by protocol-compliant stabilization guidance.

---

## 🛠️ System Architecture & Tech Stack
                         +-----------------------------------+
                         |      Streamlit Frontend UI        |
                         |   (Session-State Input Handling)  |
                         +-----------------+-----------------+
                                           |
                                  REST API | JSON Payload
                                           v
                         +-----------------------------------+
                         |        FastAPI Backend Engine     |
                         +-----------------+-----------------+
                                           |
         +---------------------------------+---------------------------------+
         |                                 |                                 |
         v                                 v                                 v
+------------------+             +-------------------+             +------------------+
| Speech Subsystem |             |  Vision Subsystem |             | Agentic Engine   |
| (Groq Whisper)   |             | (Gemini 2.5 Flash)|             | (Groq + Gemini)  |
+------------------+             +-------------------+             +------------------+

| Component | Technology / Stack | Primary Role |
| :--- | :--- | :--- |
| **Frontend UI** | Python / Streamlit (`app.py`) | Multimodal intake, dynamic state holding, clinical display |
| **Backend API** | FastAPI / Uvicorn (`app/main.py`) | Orchestration, endpoint routing (`/api/v1/triage`), JSON serialization |
| **Primary Reasoning Engine** | Groq (`llama-3.3-70b-versatile`) | Fast-path triage classification and stabilization generation |
| **Fallback Reasoning Engine**| Google Gemini (`gemini-2.5-flash`)| Redundant decision processing on primary network failure |
| **Vision Model** | Gemini 2.5 Flash Vision | Zero-shot clinical injury & wound evaluation |
| **Speech Processing** | Groq Whisper Large v3 | Regional language (Pashto/Urdu) speech recognition |
| **Telemetry & Observability** | LangSmith (`LANGCHAIN_TRACING_V2=true`) | Execution tracing, latency monitoring, and agent debugging |

---

## ✨ Key Features

1. **🎙️ Voice-First Regional Intake:** Supports direct live browser microphone recording (`st.audio_input`) alongside multi-format static file uploads (`.wav`, `.mp3`, `.m4a`, `.ogg`) in Pashto and Urdu, translated via Groq Whisper.
2. **👁️ Computer Vision Wound Evaluation:** Zero-shot analysis of injury photos to determine primary wound classification (burns, lacerations, punctures), estimated surface area, and physical markers.
3. **⚡ Dual-Provider Resilient Inference:** Groq high-speed primary reasoning with automated fallback to Google Gemini to guarantee 100% uptime during clinical emergencies.
4. **🛡️ Agentic Safety & Guardrails:** Automatically sanitizes direct drug dosages to prevent unlicensed prescribing and enforces mandatory THQ/DHQ referral flags and doctor signoff requirements.

---

## 🚀 Local Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/pak-medtriage.git](https://github.com/your-username/pak-medtriage.git)
cd pak-medtriage

2. Install Dependencies
pip install -r requirements.txt

3. Configure Environment Variables
Create a .env file in the root directory based on .env.example:
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=pak-medtriage-capstone

4. Run the Application
Start the FastAPI backend and Streamlit frontend:
# Terminal 1: Start FastAPI backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Streamlit UI
streamlit run app.py

5. Docker Deployment
To run the containerized application locally using Docker Compose:
docker-compose up --build
