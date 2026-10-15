from fastapi import FastAPI, HTTPException
from app.models.schemas import TriageRequest, TriageResponse
from app.agents.triage_agent import run_triage_pipeline

app = FastAPI(
    title="Pak-MedTriage API",
    description="Multimodal Clinical Decision Support Engine for Peripheral BHUs in KP",
    version="1.0.0"
)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "system": "Pak-MedTriage Strands Agent Engine",
        "region": "Khyber Pakhtunkhwa BHU Network"
    }

@app.post("/api/v1/triage", response_model=TriageResponse)
async def process_triage(request: TriageRequest):
    try:
        result = run_triage_pipeline(request.symptoms_text, request.vision_finding)
        
        # Safely pull values with fallbacks to avoid KeyErrors
        raw_summary = result.get("summary", result.get("safe_advice", ""))
        safe_advice = result.get("safe_advice", result.get("recommended_stabilization", raw_summary))
        
        # Determine priority dynamically
        priority = result.get("triage_priority")
        if not priority:
            summary_upper = raw_summary.upper()
            if "RED" in summary_upper:
                priority = "RED (Immediate)"
            elif "YELLOW" in summary_upper or "URGENT" in summary_upper:
                priority = "YELLOW (Urgent)"
            else:
                priority = "GREEN (Non-Urgent)"
        
        is_referral_needed = "RED" in priority.upper() or "YELLOW" in priority.upper()

        return TriageResponse(
            status="success",
            triage_priority=priority,
            clinical_summary=request.symptoms_text,
            recommended_stabilization=safe_advice,
            requires_thq_dhq_referral=is_referral_needed,
            human_doctor_signoff_required=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))