import os

AGENT_MODEL = "gemini-2.0-flash"

SYSTEM_INSTRUCTION = """You are Flowgent, an expert AI assistant for n8n workflow automation.
Your goal is to help users build, debug, and understand n8n workflows.
"""

def get_gemini_api_key() -> str:
    # ADK typically uses GOOGLE_GENAI_API_KEY
    api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_GENAI_API_KEY environment variable not set")
    return api_key
