import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Ensure project root directory is in sys.path for modular imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Unified secret retrieval from src.config (or local .env fallback)
try:
    from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
except ImportError:
    load_dotenv(BASE_DIR / ".env", override=True)
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def test_connection() -> bool:
    """Verifies Neo4j database connectivity and credentials."""
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("❌ Error: NEO4J_URI or NEO4J_PASSWORD missing in config / .env", file=sys.stderr)
        return False

    auth = (NEO4J_USERNAME, NEO4J_PASSWORD)
    print(f"🔌 Connecting to Neo4j instance at '{NEO4J_URI}'...")

    try:
        with GraphDatabase.driver(NEO4J_URI, auth=auth) as driver:
            driver.verify_connectivity()
            print("\n✅ SUCCESS: Credentials are valid and Neo4j database is accessible!")
            return True
    except Exception as e:
        print("\n❌ FAILURE: Connection rejected.", file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    test_connection()
