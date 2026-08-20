import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Locate and load local .env file if running locally
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

def get_secret(key_name: str, default: str = "") -> str:
    """Safely fetches credentials from Streamlit Secrets first, falling back to os.getenv."""
    # 1. Try Streamlit Secrets (Cloud)
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            val = st.secrets[key_name]
            if val:
                return str(val).strip()
    except Exception:
        pass

    # 2. Try OS Environment (Local .env)
    val = os.getenv(key_name, default)
    return str(val).strip() if val else default

# Fetch values securely with fallbacks
GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")
NEO4J_URI = get_secret("NEO4J_URI")
NEO4J_USERNAME = get_secret("NEO4J_USERNAME", default="neo4j")
NEO4J_PASSWORD = get_secret("NEO4J_PASSWORD")

# Validation check
missing = [
    k for k, v in {
        "GOOGLE_API_KEY": GOOGLE_API_KEY,
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USERNAME": NEO4J_USERNAME,
        "NEO4J_PASSWORD": NEO4J_PASSWORD
    }.items() if not v
]

if missing:
    print(f"⚠️ Warning: Missing credentials for: {', '.join(missing)}")
else:
    print("✅ Environment variables loaded successfully!")
