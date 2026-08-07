import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# 1. Load environment variables from .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY is missing from your .env file!")

def ingest_vectors():
    data_path = BASE_DIR / "data" / "movies_dataset.json"
    if not data_path.exists():
        data_path = BASE_DIR / "data" / "movies_dataset.json"

    print(f"📂 Loading movie data from: {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        movies = json.load(f)

    # 2. Convert JSON movie items to LangChain documents
    documents = []
    for movie in movies:
        title = movie.get("title", "Unknown Title")
        director = movie.get("director", "Unknown Director")
        
        cast = movie.get("cast", [])
        if isinstance(cast, list):
            cast_names = []
            for item in cast:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("actor") or item.get("actor_name") or str(item)
                    cast_names.append(str(name))
                else:
                    cast_names.append(str(item))
            cast_str = ", ".join(cast_names)
        else:
            cast_str = str(cast)

        synopsis = movie.get("synopsis") or movie.get("plot_summary") or ""
        page_content = f"Title: {title}\nDirector: {director}\nCast: {cast_str}\nSynopsis: {synopsis}"
        
        doc = Document(
            page_content=page_content,
            metadata={"title": title, "director": str(director)}
        )
        documents.append(doc)

    total_docs = len(documents)
    print(f"📄 Generated {total_docs} document chunks.")

    # 3. Initialize Embeddings and Vector DB
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY
    )

    chroma_path = str(BASE_DIR / "chroma_db")
    vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory=chroma_path
    )

    # 4. Batch Ingestion with Throttling to respect API Limits
    BATCH_SIZE = 20
    print(f"🧠 Ingesting in batches of {BATCH_SIZE} with pauses to avoid API Rate Limits...")

    for i in range(0, total_docs, BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        current_batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total_docs + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"⏳ Processing batch {current_batch_num}/{total_batches} ({len(batch)} docs)...")

        try:
            vector_store.add_documents(batch)
        except Exception as e:
            print("⚠️ Temporary limit hit, waiting 15 seconds before retrying this batch...")
            time.sleep(15)
            vector_store.add_documents(batch)

        # Brief pause between batches
        time.sleep(2)

    print("\n✅ Vector ingestion complete! Saved Chroma DB to './chroma_db'.")

if __name__ == "__main__":
    ingest_vectors()