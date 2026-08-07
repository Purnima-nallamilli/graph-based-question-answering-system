import json
import os
import re
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# =============================================================================
# 1. Configuration & Path Setup
# =============================================================================
# Set root project folder (Graph_QA/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load TMDB API Key securely from .env
load_dotenv(BASE_DIR / ".env", override=True)
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    print("⚠️ Warning: TMDB_API_KEY is missing from your .env file!")

# Dataset File Paths inside project data/ directory
DATA_DIR = BASE_DIR / "data"
INPUT_FILE = DATA_DIR / "unpatched_dataset.json"  # Change filename here if different
OUTPUT_FILE = DATA_DIR / "movies_dataset.json"


# =============================================================================
# 2. TMDB Helper Functions
# =============================================================================
def clean_title(title):
    """Removes Wikipedia parenthetical tags."""
    return re.sub(r'\s*\([^)]*\)', '', title).strip()

def execute_tmdb_search(query_title, year=None):
    """Safely executes a target search request against the TMDB movie index."""
    if not TMDB_API_KEY:
        return []

    url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query_title, "language": "en-US"}
    if year:
        params["year"] = year
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            return res.json().get("results", [])
    except Exception:
        pass
    return []

def fetch_tmdb_fallback(title, year, needs_plot, needs_cast):
    """Executes a multi-tiered search strategy to resolve stubborn metadata gaps."""
    fallback_data = {"plot": "", "cast": []}
    if not TMDB_API_KEY:
        return fallback_data

    base_title = clean_title(title)
    
    # Tier 1: Strict match with original title and year
    results = execute_tmdb_search(base_title, year)
    
    # Tier 2: Muted year constraint (handles mismatched database release years)
    if not results:
        results = execute_tmdb_search(base_title)
        
    # Tier 3: Punctuation normalization (converts colons/hyphens to spaces for search parsing)
    if not results and (":" in base_title or "-" in base_title):
        normalized_title = base_title.replace(":", " ").replace("-", " ")
        normalized_title = re.sub(r'\s+', ' ', normalized_title).strip()
        results = execute_tmdb_search(normalized_title)

    if not results:
        return fallback_data

    # Prioritize Telugu ("te") language matches from broad search pools
    target_movie = results[0]
    for match in results:
        if match.get("original_language") == "te":
            target_movie = match
            break
            
    tmdb_id = target_movie.get("id")
    
    if needs_plot and target_movie.get("overview"):
        fallback_data["plot"] = target_movie.get("overview").strip()
        
    if needs_cast and tmdb_id:
        try:
            credits_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits"
            credits_res = requests.get(credits_url, params={"api_key": TMDB_API_KEY}, timeout=5)
            if credits_res.status_code == 200:
                tmdb_cast = credits_res.json().get("cast", [])
                fallback_data["cast"] = [
                    {
                        "actor": actor["name"].strip(),
                        "role": actor.get("character", "Unknown Role").strip()
                    } for actor in tmdb_cast[:5]
                ]
        except Exception:
            pass
            
    return fallback_data

def patch_existing_dataset():
    if not INPUT_FILE.exists():
        print(f"❌ Error: Could not find dataset at '{INPUT_FILE}'.")
        return

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            movies_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading dataset: {e}")
        return

    print(f"Scanning '{INPUT_FILE.name}' to resolve final gaps...")
    patched_count = 0

    for movie in movies_data:
        needs_plot = not movie.get("plot_summary")
        needs_cast = not movie.get("cast")

        if needs_plot or needs_cast:
            title = movie.get("title", "Unknown Title")
            year = movie.get("year", 2025)
            
            api_patch = fetch_tmdb_fallback(title, year, needs_plot, needs_cast)
            
            if (needs_plot and api_patch["plot"]) or (needs_cast and api_patch["cast"]):
                print(f"🎬 Resolved -> {clean_title(title)} ({year})")
                if needs_plot and api_patch["plot"]:
                    movie["plot_summary"] = api_patch["plot"]
                if needs_cast and api_patch["cast"]:
                    movie["cast"] = api_patch["cast"]
                patched_count += 1
            
            time.sleep(0.2)

    # Ensure output directory exists before writing
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Operation finalized. Saved output to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    patch_existing_dataset()