import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Points to project root directory (Graph_QA/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from root .env file
load_dotenv(BASE_DIR / ".env", override=True)

# Neo4j Database Connection Settings
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Dataset File Path inside project data/ directory
DATA_DIR = BASE_DIR / "data"
INPUT_FILE = DATA_DIR / "movies_dataset.json"


# =============================================================================
# 2. Python Data Enrichment Helpers
# =============================================================================
def parse_currency_to_crores(val_str: str) -> float:
    """Converts strings like '₹10 crore', '150 Cr', or '$5 Million' to numeric Crores."""
    if not val_str or not isinstance(val_str, str):
        return 0.0

    cleaned = val_str.replace(",", "").strip()
    numbers = [float(n) for n in re.findall(r'(\d+(?:\.\d+)?)', cleaned)]
    if not numbers:
        return 0.0

    val = numbers[0]
    lower_str = cleaned.lower()

    if "million" in lower_str:
        val = val / 10.0
    elif "billion" in lower_str:
        val = val * 100.0
    elif "lakh" in lower_str:
        val = val / 100.0

    return round(val, 2)


def parse_date_and_season(date_str: str):
    """
    Parses dates in 'YYYY-MM-DD' or 'DD Month YYYY' format and returns:
    (Month Name, Quarter, Festival/Release Season)
    """
    if not date_str or not isinstance(date_str, str):
        return "Unknown", "Unknown", "Regular Release"

    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    
    found_month = ""

    # ISO Format: YYYY-MM-DD
    if len(date_str) >= 10 and date_str[4] == '-' and date_str[7] == '-':
        try:
            m_idx = int(date_str[5:7]) - 1
            if 0 <= m_idx < 12:
                found_month = month_names[m_idx]
        except ValueError:
            pass

    # Fallback text search
    if not found_month:
        for m in month_names:
            if m.lower() in date_str.lower():
                found_month = m
                break

    if not found_month:
        return "Unknown", "Unknown", "Regular Release"

    month_idx = month_names.index(found_month) + 1
    quarter = f"Q{(month_idx - 1) // 3 + 1} 2025"

    # Tollywood Cultural Release Windows
    if found_month == "January":
        season = "Sankranti Release"
    elif found_month in ["April", "May"]:
        season = "Summer Release"
    elif found_month in ["September", "October"]:
        season = "Dussehra / Diwali Release"
    else:
        season = "Regular Release"

    return found_month, quarter, season


def preprocess_movie_record(movie: dict) -> dict:
    """Prepares and cleans a single JSON movie record for Cypher ingestion."""
    m = movie.copy()

    # Title & Metadata
    m["title"] = movie.get("title", "").strip()
    m["year"] = movie.get("year", 2025)
    m["language"] = movie.get("language", "Telugu")
    m["plot_summary"] = movie.get("plot_summary", "")

    # Financials
    fin = movie.get("financials", {})
    budget_raw = fin.get("budget", "")
    box_office_raw = fin.get("box_office", "")

    b_num = parse_currency_to_crores(budget_raw)
    bo_num = parse_currency_to_crores(box_office_raw)

    m["budget_str"] = str(budget_raw) if budget_raw else ""
    m["box_office_str"] = str(box_office_raw) if box_office_raw else ""
    m["budget_in_cr"] = b_num
    m["box_office_in_cr"] = bo_num
    m["profit_in_cr"] = round(bo_num - b_num, 2) if (bo_num > 0 and b_num > 0) else 0.0
    m["verdict"] = fin.get("verdict", "N/A")

    # Release Details
    rel = movie.get("release_details", {})
    raw_date = rel.get("date", "")
    m["release_date"] = raw_date
    m["running_time_minutes"] = rel.get("running_time_minutes", 0)
    
    month, quarter, season = parse_date_and_season(raw_date)
    m["release_month"] = month
    m["release_quarter"] = quarter
    m["holiday_season"] = season

    # Cast Processing (Extract billing order & lead actor status)
    raw_cast = movie.get("cast", [])
    clean_cast = []
    for idx, c in enumerate(raw_cast):
        actor_name = c.get("actor", "").strip()
        if actor_name and actor_name != "Information Pending":
            role_str = c.get("role", "").strip()
            clean_cast.append({
                "name": actor_name,
                "role": role_str if role_str else "Main Cast",
                "billing_order": idx + 1,
                "is_lead": idx < 2  # First two actors marked as Lead
            })
    m["clean_cast"] = clean_cast

    # Combined Writers (story_by + screenplay + dialogues)
    writers = set()
    for w_list in [movie.get("story_by", []), movie.get("screenplay", []), movie.get("dialogues", [])]:
        if isinstance(w_list, list):
            for w in w_list:
                if w and isinstance(w, str) and w.strip():
                    writers.add(w.strip())
    m["writers"] = list(writers)

    # Crew & Entity Deduplication
    m["directors"] = [d.strip() for d in movie.get("director", []) if d and d.strip()]
    m["producers"] = [p.strip() for p in movie.get("producers", []) if p and p.strip()]
    m["production_companies"] = [pc.strip() for pc in movie.get("production_company", []) if pc and pc.strip()]
    m["genres"] = [g.strip() for g in movie.get("genre", []) if g and g.strip()]
    #m["ott_platforms"] = [o.strip() for o in movie.get("ott_platform", []) if o and o.strip()]

    crew = movie.get("crew", {})
    m["music_directors"] = [md.strip() for md in crew.get("music_director", []) if md and md.strip()]
    m["cinematographers"] = [c.strip() for c in crew.get("cinematographer", []) if c and c.strip()]
    
    raw_editors = crew.get("editors") or crew.get("editor") or []
    m["editors"] = [e.strip() for e in raw_editors if e and e.strip()]

    return m


# =============================================================================
# 3. Neo4j Schema Constraints
# =============================================================================
CONSTRAINTS_QUERIES = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Movie) REQUIRE m.title IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Director) REQUIRE d.name IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (md:MusicDirector) REQUIRE md.name IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:ProductionHouse) REQUIRE p.name IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (prod:Producer) REQUIRE prod.name IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Writer) REQUIRE w.name IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Cinematographer) REQUIRE c.name IS UNIQUE;",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Editor) REQUIRE e.name IS UNIQUE;"
   # "CREATE CONSTRAINT IF NOT EXISTS FOR (ott:OTTPlatform) REQUIRE ott.name IS UNIQUE;"
]


# =============================================================================
# 4. Master Cypher Ingestion Query
# =============================================================================
CYPHER_INGESTION = """
UNWIND $movies AS mData

// A. Central Movie Node
MERGE (m:Movie {title: mData.title})
SET m.year = mData.year,
    m.language = mData.language,
    m.plot = mData.plot_summary,
    m.verdict = mData.verdict,
    m.budget_str = mData.budget_str,
    m.box_office_str = mData.box_office_str,
    m.budget_in_cr = mData.budget_in_cr,
    m.box_office_in_cr = mData.box_office_in_cr,
    m.profit_in_cr = mData.profit_in_cr,
    m.runtime_minutes = mData.running_time_minutes,
    m.release_date = mData.release_date,
    m.release_month = mData.release_month,
    m.release_quarter = mData.release_quarter,
    m.holiday_season = mData.holiday_season

// B. Connect Cast with Role, Billing Order & Lead Status
WITH m, mData
UNWIND mData.clean_cast AS c
MERGE (a:Actor {name: c.name})
MERGE (a)-[r:ACTED_IN]->(m)
SET r.role = c.role,
    r.billing_order = c.billing_order,
    r.is_lead = c.is_lead

// C. Connect Directors
WITH DISTINCT m, mData
UNWIND mData.directors AS dirName
MERGE (d:Director {name: dirName})
MERGE (d)-[:DIRECTED]->(m)

// D. Connect Music Directors
WITH DISTINCT m, mData
UNWIND mData.music_directors AS composer
MERGE (md:MusicDirector {name: composer})
MERGE (md)-[:COMPOSED_MUSIC_FOR]->(m)

// E. Connect Producers (Individual People)
WITH DISTINCT m, mData
UNWIND mData.producers AS prodName
MERGE (prod:Producer {name: prodName})
MERGE (prod)-[:PRODUCED]->(m)

// F. Connect Production Companies (Studios / Banners)
WITH DISTINCT m, mData
UNWIND mData.production_companies AS studio
MERGE (p:ProductionHouse {name: studio})
MERGE (p)-[:PRODUCED_BY_BANNER]->(m)

// G. Connect Genres
WITH DISTINCT m, mData
UNWIND mData.genres AS gName
MERGE (g:Genre {name: gName})
MERGE (m)-[:BELONGS_TO]->(g)

// H. Connect Writers (Story, Screenplay, Dialogues)
WITH DISTINCT m, mData
UNWIND mData.writers AS wName
MERGE (w:Writer {name: wName})
MERGE (w)-[:WROTE]->(m)

// I. Connect Cinematographers
WITH DISTINCT m, mData
UNWIND mData.cinematographers AS dp
MERGE (c:Cinematographer {name: dp})
MERGE (c)-[:FILMED]->(m)

// J. Connect Editors
WITH DISTINCT m, mData
UNWIND mData.editors AS edName
MERGE (e:Editor {name: edName})
MERGE (e)-[:EDITED]->(m)

"""


# =============================================================================
# 5. Main Execution Entrypoint
# =============================================================================
def run_pipeline():
    if not INPUT_FILE.exists():
        print(f"❌ Error: Could not find input file at '{INPUT_FILE}'")
        return

    print(f"📂 Reading raw JSON dataset from '{INPUT_FILE.name}'...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_dataset = json.load(f)

    print(f"⚙️ Preprocessing and enriching {len(raw_dataset)} movie records...")
    processed_movies = [preprocess_movie_record(m) for m in raw_dataset]

    print("🔌 Connecting to Neo4j instance...")
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

    try:
        with driver.session() as session:
            # Step 1: Create Database Constraints
            print("🛡️ Applying uniqueness constraints on node labels...")
            for query in CONSTRAINTS_QUERIES:
                session.run(query)

            # Step 2: Batch Ingest Data
            print(" Executing batch ingestion query...")
            session.run(CYPHER_INGESTION, movies=processed_movies)

            print("✅ Ingestion successfully completed!")

    except Exception as e:
        print(f" An error occurred during ingestion: {e}")
    finally:
        driver.close()


if __name__ == "__main__":
    run_pipeline()