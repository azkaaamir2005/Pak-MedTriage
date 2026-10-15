import os
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai.types import HttpOptions
from app.agents.guardrails import SafetyGuardrail

# Resolve workspace root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if GROQ_API_KEY:
    print(f"[INFO] GROQ_API_KEY detected ({GROQ_API_KEY[:6]}...). Primary engine ready.")
else:
    print("[WARNING] GROQ_API_KEY is missing in .env!")


def get_triage_protocol(condition_keyword: str) -> str:
    """Retrieves official KP Basic Health Unit emergency triage protocols."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        protocol_path = os.path.join(base_dir, "data", "bhu_triage_protocols.json")
        
        if os.path.exists(protocol_path):
            with open(protocol_path, "r", encoding="utf-8") as f:
                protocols = json.load(f)
            for p in protocols:
                if condition_keyword.lower() in p.get("category", "").lower():
                    return json.dumps(p)
            return json.dumps(protocols[0]) if protocols else "Protocol not found"
        return "Triage database file unavailable."
    except Exception as e:
        return f"Protocol retrieval error: {str(e)}"


def _call_groq_triage(system_instruction: str, query: str) -> str:
    """Primary provider call using Groq (llama-3.3-70b-versatile)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment.")
        
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )
    
    # Updated to active Groq production model string
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": query}
        ],
        temperature=0.2,
        max_tokens=1024
    )
    return response.choices[0].message.content


def _call_gemini_triage(system_instruction: str, query: str) -> str:
    """Secondary fallback call using Google Gemini 2.5 Flash."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment.")
        
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{system_instruction}\n\nTask: {query}"
    )
    return response.text


def run_triage_pipeline(symptoms: str, vision_data: str) -> dict:
    protocol_context = get_triage_protocol("burn")
    
    system_instruction = (
        "You are Pak-MedTriage, an AI clinical decision co-pilot for rural health workers in KP. "
        f"Official BHU Protocols Context: {protocol_context}. "
        "State clearly 'TRIAGE CATEGORY: RED', 'TRIAGE CATEGORY: YELLOW', or 'TRIAGE CATEGORY: GREEN'. "
        "Severe occipital headache radiating down to neck and spine requires RED (Immediate) triage category for urgent THQ/DHQ referral. "
        "Reserve RED (Immediate) strictly for second/third-degree burns >10% TBSA, severe neurological signs, compromised airways, or shock."
    )
    
    query = f"Patient Spoken History: {symptoms}. Visual Finding: {vision_data}. Evaluate triage category and stabilization."
    
    raw_str = ""
    engine_used = "Groq (llama-3.3-70b)"

    # Primary attempt: Groq
    try:
        raw_str = _call_groq_triage(system_instruction, query)
    except Exception as groq_err:
        print(f"[Warning] Groq call failed ({str(groq_err)}). Falling back to Gemini...")
        engine_used = "Gemini (gemini-2.5-flash fallback)"
        # Secondary fallback: Gemini
        try:
            raw_str = _call_gemini_triage(system_instruction, query)
        except Exception as gemini_err:
            print(f"[Error] Gemini call failed ({str(gemini_err)}).")
            return {
                "status": "error",
                "summary": f"Both providers failed. Groq: {str(groq_err)} | Gemini: {str(gemini_err)}",
                "triage_priority": "RED (Immediate)",
                "clinical_summary": f"Patient history: {symptoms}",
                "recommended_stabilization": "Immediate manual triage by BHU medical officer required.",
                "requires_thq_dhq_referral": True,
                "human_doctor_signoff_required": True
            }

    # Run safety guardrails
    safe_advice = SafetyGuardrail.validate_triage_output(raw_str)
    
    # Parse priority
    # Parse priority strictly based on model output line
    raw_upper = raw_str.upper()
    
    if "TRIAGE CATEGORY: RED" in raw_upper or "TRIAGE CATEGORY: RED (IMMEDIATE)" in raw_upper:
        priority = "RED (Immediate)"
    elif "TRIAGE CATEGORY: YELLOW" in raw_upper or "TRIAGE CATEGORY: YELLOW (URGENT)" in raw_upper:
        priority = "YELLOW (Urgent)"
    elif "TRIAGE CATEGORY: GREEN" in raw_upper or "TRIAGE CATEGORY: GREEN (ROUTINE)" in raw_upper:
        priority = "GREEN (Routine)"
    else:
        # Fallback keyword match if model omitted exact header formatting
        if "RED" in raw_upper:
            priority = "RED (Immediate)"
        elif "YELLOW" in raw_upper:
            priority = "YELLOW (Urgent)"
        else:
            priority = "GREEN (Routine)"
    
    return {
        "status": "success",
        "provider_engine": engine_used,
        "summary": raw_str,
        "triage_priority": priority,
        "clinical_summary": f"Patient history: {symptoms}",
        "recommended_stabilization": safe_advice,
        "requires_thq_dhq_referral": ("RED" in priority or "YELLOW" in priority),
        "human_doctor_signoff_required": True
    }