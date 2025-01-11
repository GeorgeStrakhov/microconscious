import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Logging configuration
    LOG_FILE = "logs/app.log"
    LOG_ROTATION = "1 day"
    LOG_RETENTION = "7 days"
    LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    LOG_LEVEL = "INFO"

    # LLM config
    LLM = "anthropic/claude-3-5-sonnet-20240620"
    # LLM = "groq/llama-3.1-70b-versatile"
