import os
import sys
from tabulate import tabulate

# Ensure parent directory is in path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Import backend modules safely
try:
    from src.graph_rag import query_graph_rag
    from src.vector_rag import query_vector_rag
except ImportError:
    from graph_rag import query_graph_rag
    from vector_rag import query_vector_rag

# Benchmark Test Suite with Ground Truth Answers
TEST_QUESTIONS = [
    {
        "type": "1-Hop",
        "question": "Who directed the movie Game Changer?",
        "expected": "S. Shankar"
    },
    {
        "type": "1-Hop",
        "question": "What other movies were directed by the director of Game Changer?",
        "expected": "Indian 2, Bharateeyudu 2"
    },
    {
        "type": "2-Hop",
        "question": "Which directors directed movies starring actors in Katha Kamamishu?",
        "expected": "Goutham, Karthik, Amma Rajashekar, Sriharsha Manne"
    },
    {
        "type": "3-Hop",
        "question": "Which actors starred in movies that had music composed by Bheems Ceciroleo?",
        "expected": "Multi-step relational path across composer filmographies"
    }
    
]

def clean_response(response) -> str:
    """Extracts raw text answer if output is returned as a dictionary."""
    if isinstance(response, dict):
        return response.get("result", response.get("answer", str(response)))
    return str(response)

def run_evaluation():
    print("Starting RAG Benchmark Evaluation..\n")
    
    results = []
    total_q = len(TEST_QUESTIONS)
    
    for idx, item in enumerate(TEST_QUESTIONS, 1):
        hop_type = item["type"]
        question = item["question"]
        expected = item["expected"]
        
        print(f"[{idx}/{total_q}] 🔍 Testing ({hop_type}): '{question}'")
        
        # Execute Graph RAG
        try:
            g_raw = query_graph_rag(question)
            graph_ans = clean_response(g_raw)
        except Exception as e:
            graph_ans = f"Graph RAG Error: {e}"
            
        # Execute Vector RAG
        try:
            v_raw = query_vector_rag(question)
            vector_ans = clean_response(v_raw)
        except Exception as e:
            vector_ans = f"Vector RAG Error: {e}"
        
        # Store for tabular summary
        results.append([
            hop_type,
            question,
            expected,
            graph_ans,
            vector_ans
        ])
        print("-" * 70)

    print("\n" + "=" * 120)
    print("RAG EVALUATION SUMMARY")
    print("=" * 120)
    
    headers = [
        "Complexity",
        "Question",
        "Expected Answer (Ground Truth)",
        "Graph RAG Answer",
        "Vector RAG Answer"
    ]
    
    # maxcolwidths ensures clean word wrapping in the terminal output grid
    print(tabulate(
        results, 
        headers=headers, 
        tablefmt="grid", 
        maxcolwidths=[10, 25, 25, 30, 30]
    ))

if __name__ == "__main__":
    run_evaluation()