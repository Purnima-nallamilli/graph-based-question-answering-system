import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically locate the .env file in the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

# Load .env when running locally
# Do not override existing environment variables
load_dotenv(dotenv_path=env_path, override=False)

# Fetch configuration values
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# If running on Streamlit Cloud, read from Streamlit Secrets
try:
    import streamlit as st

    GOOGLE_API_KEY = GOOGLE_API_KEY or st.secrets.get("GOOGLE_API_KEY")
    NEO4J_URI = NEO4J_URI or st.secrets.get("NEO4J_URI")
    NEO4J_USERNAME = NEO4J_USERNAME or st.secrets.get("NEO4J_USERNAME")
    NEO4J_PASSWORD = NEO4J_PASSWORD or st.secrets.get("NEO4J_PASSWORD")

except Exception:
    pass

if not GOOGLE_API_KEY or not NEO4J_PASSWORD:
    print("⚠️ Warning: Missing GOOGLE_API_KEY or NEO4J_PASSWORD!")
else:
    print("✅ Configuration loaded successfully!")
