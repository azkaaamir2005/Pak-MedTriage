import re

class SafetyGuardrail:
    RESTRICTED_KEYWORDS = [
        "prescribe", "mg", "dosage", "antibiotic",
        "amoxicillin", "paracetamol", "take 500mg", "administer medicine",
        "ibuprofen"
    ]

    @classmethod
    def validate_triage_output(cls, text: str) -> str:
        validated_text = text
        triggered = False

        for kw in cls.RESTRICTED_KEYWORDS:
            # Check if keyword exists using case-insensitive regex word boundaries
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, validated_text, re.IGNORECASE):
                triggered = True
                # Redact restricted term instead of wiping the entire response
                validated_text = re.sub(
                    pattern, 
                    "[REDACTED MEDICATION]", 
                    validated_text, 
                    flags=re.IGNORECASE
                )

        # Append a safety warning banner if any restricted terms were redacted
        if triggered:
            validated_text += (
                "\n\n> ⚠️ **[SAFETY GUARDRAIL ENFORCED]:** Direct medication prescriptions "
                "or specific drug dosages have been redacted. Consult a licensed medical officer for prescriptions."
            )

        return validated_text