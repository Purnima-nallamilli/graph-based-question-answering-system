import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# =============================================================================
# Load Environment Configuration
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not PASSWORD:
    print("❌ Error: NEO4J_URI or NEO4J_PASSWORD missing from .env", file=sys.stderr)
    sys.exit(1)

AUTH = (USER, PASSWORD)

# =============================================================================
# Execute Connection Test
# =============================================================================
def test_connection():
    print(f"Connecting to Neo4j instance at {URI}...")
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("\n>>> SUCCESS: Credentials are valid and Neo4j database is accessible! <<<")
    except Exception as e:
        print(f"\n>>> FAILURE: Connection rejected. <<<", file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)

if __name__ == "__main__":
    test_connection()