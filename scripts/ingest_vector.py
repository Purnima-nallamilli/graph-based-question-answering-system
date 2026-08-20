import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Ensure project root directory is in sys.path for modular imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Unified secret retrieval from src.config (or local .env fallback)
try:
    from src.config import GOOGLE_API_KEY
except ImportError:
    load_dotenv(BASE_DIR / ".env", override=True)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def ingest_vectors():
    if not GOOGLE_API_KEY:
        print("❌ Error: GOOGLE_API_KEY is missing. Check .env or Streamlit secrets.")
        return

    data_path = BASE_DIR / "data" / "movies_dataset.json"
    if not data_path.exists():
        print(f"❌ Error: Could not find dataset at '{data_path}'")
        return

    print(f"📂 Loading movie data from: {data_path.name}")
    with open(data_path, "r", encoding="utf-8") as f:
        movies = json.load(f)

    # Convert JSON movie items to LangChain documents
    documents = []
    for movie in movies:
        title = movie.get("title", "Unknown Title").strip()

        # Handle directors list or string
        raw_director = movie.get("director", [])
        if isinstance(raw_director, list):
            director_str = ", ".join([str(d).strip() for d in raw_director if d])
        else:
            director_str = str(raw_director).strip()

        # Handle cast parsing
        cast = movie.get("cast", [])
        if isinstance(cast, list):
            cast_names = []
            for item in cast:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("actor") or item.get("actor_name") or str(item)
                    cast_names.append(str(name).strip())
                else:
                    cast_names.append(str(item).strip())
            cast_str = ", ".join([c for c in cast_names if c])
        else:
            cast_str = str(cast).strip()

        # Handle genre parsing
        raw_genre = movie.get("genre", [])
        genre_str = ", ".join(raw_genre) if isinstance(raw_genre, list) else str(raw_genre)

        synopsis = movie.get("synopsis") or movie.get("plot_summary") or ""

        page_content = (
            f"Title: {title}\n"
            f"Director: {director_str}\n"
            f"Cast: {cast_str}\n"
            f"Genre: {genre_str}\n"
            f"Synopsis: {synopsis}"
        )

        doc = Document(
            page_content=page_content,
            metadata={"title": title, "director": director_str}
        )
        documents.append(doc)

    total_docs = len(documents)
    print(f"📄 Generated {total_docs} document chunks.")

    # Initialize Embeddings and Vector DB
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY
    )

    chroma_path = str(BASE_DIR / "chroma_db")
    vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory=chroma_path
    )

    # Reset collection if available to avoid duplicate entries on re-runs
    try:
        vector_store.reset_collection()
        print("🧹 Existing collection reset for clean re-ingestion.")
    except Exception:
        pass

    # Batch Ingestion with Throttling
    BATCH_SIZE = 20
    print(f"🧠 Ingesting in batches of {BATCH_SIZE} with rate-limit throttling...")

    for i in range(0, total_docs, BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        current_batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total_docs + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"⏳ Processing batch {current_batch_num}/{total_batches} ({len(batch)} docs)...")

        try:
            vector_store.add_documents(batch)
        except Exception as e:
            print(f"⚠️ Rate limit or API error: {e}. Waiting 15 seconds before retrying batch...")
            time.sleep(15)
            vector_store.add_documents(batch)

        time.sleep(2)

    print("\n✅ Vector ingestion complete! Saved Chroma DB to './chroma_db'.")


if __name__ == "__main__":
    ingest_vectors()
