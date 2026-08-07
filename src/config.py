import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically locate the .env file in the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

load_dotenv(dotenv_path=env_path, override=True)

# Fetch values using the exact key names defined in your .env file
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not GOOGLE_API_KEY or not NEO4J_PASSWORD:
    print("⚠️ Warning: Missing GOOGLE_API_KEY or NEO4J_PASSWORD in .env file!")
else:
    print("✅ Environment variables loaded successfully from .env!")