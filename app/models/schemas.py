from pydantic import BaseModel, Field

class TriageRequest(BaseModel):
    symptoms_text: str = Field(
        ..., 
        json_schema_extra={"example": "Patient has a painful red burn with severe blistering on the left forearm caused by hot cooking oil."}
    )
    vision_finding: str = Field(
        ..., 
        json_schema_extra={"example": "Second-degree partial-thickness burn covering approximately 5% surface area on forearm."}
    )

class TriageResponse(BaseModel):
    status: str
    triage_priority: str
    clinical_summary: str
    recommended_stabilization: str
    requires_thq_dhq_referral: bool
    human_doctor_signoff_required: bool