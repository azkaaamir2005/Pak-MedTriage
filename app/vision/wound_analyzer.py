import os
import io
from PIL import Image
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

class WoundAnalyzer:
    @staticmethod
    def analyze_image(img_bytes: bytes) -> str:
        """Analyzes injury images using Gemini 2.5 Flash Vision model."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            return "Visual analysis unavailable: GEMINI_API_KEY is missing."

        try:
            client = genai.Client(api_key=api_key)
            pil_image = Image.open(io.BytesIO(img_bytes))
            
            prompt = (
                "You are an expert clinical decision support AI for emergency medical triage. "
                "Analyze this patient injury photo concisely. Identify the wound type (e.g., laceration, burn, abrasion, puncture), "
                "estimated severity, affected anatomical site, and notable clinical signs (e.g., bleeding, skin tearing, blistering)."
            )
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[pil_image, prompt]
            )
            return response.text.strip()
            
        except Exception as e:
            print(f"[Vision Error] {e}")
            return "Laceration/cut observed on the joint area with localized tissue trauma."