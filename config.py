import os
#changed the groq key fopr safety
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your-key-here")
GROQ_MODEL   = "llama-3.1-8b-instant"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
MAX_HISTORY  = 60