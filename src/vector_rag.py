import sys
import os
from pathlib import Path

# Ensure project root directory is in sys.path for modular imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Centralized secret retrieval from src.config (handles st.secrets + local .env)
from src.config import GOOGLE_API_KEY

from langchain_chroma import Chroma
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

vector_chain = None

if not GOOGLE_API_KEY:
    print("❌ Vector RAG Notice: GOOGLE_API_KEY missing in config. Check Streamlit Secrets or .env file.")
else:
    try:
        # 1. Initialize Embeddings & Load Existing Vector Store
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=GOOGLE_API_KEY
        )

        chroma_path = str(BASE_DIR / "chroma_db")
        vector_store = Chroma(
            persist_directory=chroma_path,
            embedding_function=embeddings
        )

        # Retrieve top-3 most similar document chunks
        retriever = vector_store.as_retriever(
            search_kwargs={"k": 3}
        )

        # 2. Setup Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )

        # 3. Create RAG Prompt Template
        template = """You are a helpful movie assistant. Answer the user's question using ONLY the provided text context below.

If the information is not explicitly present in the context, state that you do not have enough information to answer.

Context:
{context}

Question:
{question}

Answer:"""

        prompt = ChatPromptTemplate.from_template(template)

        def format_docs(docs):
            return "\n\n".join(
                doc.page_content for doc in docs
            )

        # 4. Construct RAG Chain
        vector_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        print("✅ Vector RAG initialized successfully!")
    except Exception as e:
        print(f"❌ Vector RAG Initialization Error: {e}")


def query_vector_rag(query: str) -> str:
    """Invokes the Vector RAG pipeline with a given query."""
    if not vector_chain:
        return "Vector RAG unavailable: Initialization failed or missing GOOGLE_API_KEY."
    
    try:
        return vector_chain.invoke(query)
    except Exception as e:
        return f"Vector RAG Error: {str(e)}"


if __name__ == "__main__":
    test_question = (
        "What other movies were directed by the director of Game Changer?"
    )

    print(f"🔍 Testing Vector RAG Question: '{test_question}'")

    answer = query_vector_rag(test_question)

    print(f"🤖 Vector RAG Answer:\n{answer}")
