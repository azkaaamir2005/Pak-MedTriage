import streamlit as st
import requests
import os
import io
from PIL import Image
from app.vision.wound_analyzer import WoundAnalyzer
from app.speech.pashto_transcriber import PashtoTranscriber

# Page Config
st.set_page_config(page_title="Pak-MedTriage Engine", page_icon="🏥", layout="wide")

st.title("🏥 Pak-MedTriage")
st.caption("AI-Powered Multimodal Decision Support System for Rural BHUs in Khyber Pakhtunkhwa")

# Initialize session state for speech transcription
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📥 Patient Clinical Inputs")
    
    # 1. Audio / Voice Input (Pashto/Urdu)
    st.markdown("#### 1. Audio / Voice Input (Pashto/Urdu)")
    
    # Live Recording Feature
    recorded_audio = st.audio_input("🎙️ Record Live Voice Note (Pashto/Urdu)")
    
    # File Upload (including .ogg)
    uploaded_audio = st.file_uploader(
        "Or upload a voice note file (.wav, .mp3, .m4a, .ogg)", 
        type=["wav", "mp3", "m4a", "ogg"]
    )
    
    # Priority handling: use live recording if captured, otherwise uploaded file
    active_audio = recorded_audio if recorded_audio is not None else uploaded_audio
    
    if active_audio is not None:
        st.audio(active_audio)
        file_ext = active_audio.name.split(".")[-1] if hasattr(active_audio, "name") else "wav"
        temp_path = f"temp_recording.{file_ext}"
        
        with open(temp_path, "wb") as f:
            f.write(active_audio.getbuffer())
        
        with st.spinner("Transcribing spoken query..."):
            try:
                result = PashtoTranscriber.transcribe_audio(temp_path)
                if result and result.strip():
                    st.session_state.transcribed_text = result.strip()
                    st.success("Transcription complete!")
                else:
                    st.warning("Transcription returned empty text. Please speak clearly or type symptoms manually.")
            except Exception as tx_err:
                st.error(f"Transcription error: {tx_err}")
            
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 2. Text Symptoms Input (Persists transcribed audio in session state)
    symptoms_input = st.text_area(
        "Patient Symptoms / Spoken History",
        value=st.session_state.transcribed_text,
        placeholder="Type patient symptoms here or record a voice note above...",
        height=100
    )

    # 3. Clinical Wound Image Input
    st.markdown("#### 2. Clinical Image Input (Wound / Injury)")
    uploaded_image = st.file_uploader("Upload injury photo", type=["png", "jpg", "jpeg"])
    
    vision_text = ""
    if uploaded_image is not None:
        img_bytes = uploaded_image.getvalue()
        st.image(Image.open(io.BytesIO(img_bytes)), caption="Uploaded Patient Injury", use_container_width=True)
        with st.spinner("Analyzing image findings..."):
            vision_text = WoundAnalyzer.analyze_image(img_bytes)
            st.info(f"**Vision Analysis:** {vision_text}")
    else:
        vision_text = st.text_input(
            "Visual Findings / Description",
            value="",
            placeholder="Describe visual findings or upload an image above..."
        )

    # Trigger Evaluation
    run_btn = st.button("🚨 Run Triage Evaluation", type="primary", use_container_width=True)

with col_right:
    st.subheader("📋 Clinical Decision & Stabilization")
    
    if run_btn:
        if not symptoms_input.strip() and not vision_text.strip():
            st.warning("⚠️ Please record audio, type symptoms, or upload an image before running the evaluation.")
        else:
            with st.spinner("Processing through Strands Agent & Safety Guardrails..."):
                try:
                    res = requests.post(
                        "http://127.0.0.1:8000/api/v1/triage",
                        json={
                            "symptoms": symptoms_input,
                            "symptoms_text": symptoms_input,
                            "vision_data": vision_text,
                            "vision_finding": vision_text
                        }
                    )
                    
                    if res.status_code == 200:
                        data = res.json()
                        priority = data.get("triage_priority", "UNKNOWN")
                        
                        # Alert Badges
                        if "RED" in priority.upper():
                            st.error(f"### Triage Category: {priority}")
                        elif "YELLOW" in priority.upper():
                            st.warning(f"### Triage Category: {priority}")
                        else:
                            st.success(f"### Triage Category: {priority}")
                        
                        st.markdown("### 🚑 Stabilization Guidance")
                        st.write(data.get("recommended_stabilization", data.get("summary", "No guidance generated.")))
                        
                        st.divider()
                        c1, c2 = st.columns(2)
                        c1.metric("THQ/DHQ Referral Required", str(data.get("requires_thq_dhq_referral", True)))
                        c2.metric("Doctor Signoff Required", str(data.get("human_doctor_signoff_required", True)))
                    else:
                        st.error(f"Backend Error ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"Could not connect to FastAPI server at http://127.0.0.1:8000. Is Uvicorn running? Error: {e}")