import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Automatically locate the .env file in the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

def get_secret(key_name: str) -> str:
    """Fetches credentials from Streamlit Cloud Secrets first, falling back to os.getenv."""
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, "")

# Fetch values securely across both Local and Cloud environments
GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
NEO4J_URI = get_secret("NEO4J_URI")
NEO4J_USERNAME = get_secret("NEO4J_USERNAME")
NEO4J_PASSWORD = get_secret("NEO4J_PASSWORD")

if not GOOGLE_API_KEY or not NEO4J_PASSWORD or not NEO4J_URI:
    print("⚠️ Warning: Missing GOOGLE_API_KEY, NEO4J_URI, or NEO4J_PASSWORD!")
else:
    print("✅ Environment variables loaded successfully!")
