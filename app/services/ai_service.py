"""
AI Service Factory for EngineerOS.

Returns the appropriate AI service based on configuration:
  - GeminiService  if GEMINI_API_KEY is set in .env
  - MockAIService  otherwise (no API key needed for development)

The Gemini model name is read from Flask config (GEMINI_MODEL)
and is never hard-coded.
"""
import os


def get_ai_service():
    """
    Return the appropriate AI service instance.

    Checks for GEMINI_API_KEY in the environment. If present, returns
    a GeminiService configured with the key and model name.
    Otherwise returns a MockAIService for offline development.
    """
    api_key = os.environ.get('GEMINI_API_KEY', '')
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')

    if api_key:
        from app.services.gemini_service import GeminiService
        return GeminiService(api_key, model_name=model_name)
    else:
        from app.services.mock_ai_service import MockAIService
        return MockAIService()
