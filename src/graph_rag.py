import sys
import os
from pathlib import Path

# Ensure project root directory is in sys.path for modular imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# Centralized secret retrieval from src.config (handles st.secrets + local .env)
from src.config import GOOGLE_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Custom Cypher generation prompt to handle titles with suffixes like '(film)'
CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided schema.
Schema:
{schema}

CRITICAL RULE FOR MOVIE TITLES:
When matching movie titles, ALWAYS use case-insensitive fuzzy matching with `toLower()` and `CONTAINS` or `STARTS WITH` (e.g., `WHERE toLower(m.title) CONTAINS toLower('Game Changer')`) because titles in the database often contain extra text or suffixes like '(film)'.

Question: {question}
Cypher Query:"""

cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

chain = None

if not NEO4J_URI or not NEO4J_PASSWORD or not GOOGLE_API_KEY:
    print("❌ Graph RAG Notice: Credentials missing in config. Check Streamlit Secrets or .env file.")
else:
    try:
        graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD
        )
        graph.refresh_schema()

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )

        chain = GraphCypherQAChain.from_llm(
            graph=graph,
            llm=llm,
            cypher_prompt=cypher_prompt,
            verbose=True,
            allow_dangerous_requests=True
        )
        print("✅ Graph RAG initialized successfully!")
    except Exception as e:
        print(f"❌ Neo4j Connection Notice: {e}")

def query_graph_rag(query: str) -> str:
    """Invokes the Graph RAG pipeline with a given query."""
    if not chain:
        return "Graph RAG unavailable: Neo4j connection failed or missing credentials."
    
    try:
        response = chain.invoke({"query": query})
        return response.get("result", "No result returned.")
    except Exception as e:
        return f"Graph RAG Error: {str(e)}"

if __name__ == "__main__":
    test_question = "Which production banners produced OTHER movies starring the lead actor of Game Changer?"
    print(f"🔍 Testing Graph RAG Question: '{test_question}'")
    answer = query_graph_rag(test_question)
    print(f"🤖 Graph RAG Answer:\n{answer}")
