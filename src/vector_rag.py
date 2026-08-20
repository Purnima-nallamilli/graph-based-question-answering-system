from pathlib import Path

from langchain_chroma import Chroma
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.config import GOOGLE_API_KEY


if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY is missing!")


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


# 1. Initialize Embeddings & Load Existing Vector Store
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY
)

vector_store = Chroma(
    persist_directory=str(BASE_DIR / "chroma_db"),
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


def query_vector_rag(query: str) -> str:
    """Invokes the Vector RAG pipeline with a given query."""
    return vector_chain.invoke(query)


if __name__ == "__main__":
    test_question = (
        "What other movies were directed by the director of Game Changer?"
    )

    print(f"🔍 Testing Vector RAG Question: '{test_question}'")

    answer = query_vector_rag(test_question)

    print(f"🤖 Vector RAG Answer:\n{answer}")
