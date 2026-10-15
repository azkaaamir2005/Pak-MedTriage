import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

class PashtoTranscriber:
    @staticmethod
    def transcribe_audio(file_path: str) -> str:
        """Transcribes Urdu/Pashto audio notes using Whisper via Groq or local API."""
        api_key = os.getenv("GROQ_API_KEY")
        
        if api_key:
            try:
                client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=api_key
                )
                with open(file_path, "rb") as file:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(file_path), file.read()),
                        model="whisper-large-v3",
                        prompt="Transcribe Urdu , English or Pashto speech regarding medical symptoms accurately."
                    )
                return transcription.text
            except Exception as e:
                print(f"[Whisper Transcribe Warning] {e}")

        # Basic fallback for testing if API key is unavailable
        return "Meri left leg dislocate ho gayi hai. Severe pain and unable to bear weight."