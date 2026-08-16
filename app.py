import os
import sys
import time
import json
import pandas as pd
import streamlit as st

# Ensure Python can locate the src folder regardless of how Streamlit is launched
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "src"))

# --- Import backend modules ---
try:
    from src.graph_rag import query_graph_rag
    from src.vector_rag import query_vector_rag
except ImportError:
    try:
        from graph_rag import query_graph_rag
        from vector_rag import query_vector_rag
    except ImportError as e:
        st.error(f"❌ Failed to load backend modules: {e}")

# --- Helper: Ground Truth Benchmark Loader ---
@st.cache_data
def load_benchmark_questions():
    """Loads benchmark questions and expected ground-truth entities from JSON."""
    json_paths = [
        os.path.join(BASE_DIR, "data", "test_questions.json"),
        os.path.join(BASE_DIR, "test_questions.json")
    ]
    for path in json_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return []

def find_ground_truth(user_query: str):
    """Finds ground truth expected_entities if question exists in test_questions.json."""
    clean_q = user_query.strip().lower()
    benchmark_dataset = load_benchmark_questions()
    for item in benchmark_dataset:
        if item.get("question", "").strip().lower() == clean_q:
            return item.get("expected_entities", [])
    return None

# --- Helper: Metric Calculation (Recall for Retrieval, F1 for Answer) ---
def compute_rag_metrics(context_raw: str, answer_str: str, ground_truth: list):
    """
    Retrieval Accuracy -> Recall (Checks if ground-truth facts entered raw context)
    Answer Accuracy    -> F1-Score (Evaluates precision & recall balance in final output)
    """
    if not ground_truth:
        return 0.0, 0.0

    gt_items = [g.strip().lower() for g in ground_truth if g.strip()]
    total_gt = len(gt_items)
    if total_gt == 0:
        return 0.0, 0.0

    # 1. Retrieval Accuracy (Recall)
    ctx_lower = str(context_raw).lower()
    retrieved_count = sum(1 for gt in gt_items if gt in ctx_lower)
    retrieval_recall = (retrieved_count / total_gt) * 100.0

    # 2. Answer Accuracy (F1-Score)
    ans_lower = str(answer_str).lower()
    ans_tp = sum(1 for gt in gt_items if gt in ans_lower)
    
    ans_recall = ans_tp / total_gt
    
    # Estimate total entity mentions in final answer text
    ans_tokens = [x.strip() for x in ans_lower.replace('\n', ',').split(',') if x.strip()]
    approx_total_entities = max(ans_tp, len(ans_tokens))
    ans_precision = (ans_tp / approx_total_entities) if approx_total_entities > 0 else 0.0

    if (ans_precision + ans_recall) > 0:
        ans_f1 = (2 * ans_precision * ans_recall) / (ans_precision + ans_recall) * 100.0
    else:
        ans_f1 = 0.0

    return round(retrieval_recall, 1), round(ans_f1, 1)

# --- Helper: Query Complexity Detection ---
def detect_query_hops(question: str):
    """Analyzes question structure to determine hop complexity."""
    q_lower = question.lower()
    
    # 3-Hop Indicators
    if any(phrase in q_lower for phrase in ["music composed by", "other directors", "starred in movies starring actors", "co-stars' other films", "directed movies starring"]):
        return "3-Hop (Multi-Step Traversal)", "Requires multi-step relational traversal across connected entities (Movie ➔ MusicDirector ➔ Movie ➔ Actor)."
    
    # 2-Hop Indicators
    elif any(phrase in q_lower for phrase in ["appeared alongside", "acted with", "co-star", "actors in movies directed by", "directors directed movies starring"]):
        return "2-Hop (Interconnected Entity)", "Requires bridging intermediate entities across 2 relational joins."
    
    # 1-Hop Indicators
    elif any(phrase in q_lower for phrase in ["who directed", "release year", "who acted in", "who composed"]):
        return "1-Hop (Direct Relation)", "Direct relationship lookup between 2 primary nodes."
    
    return "Multi-Hop Request", "Broad structural query requiring entity extraction and relational graph traversal."

# --- Helper: Clean Graph Error Messages ---
def format_graph_response(raw_response: str) -> tuple[str, bool]:
    """Interprets raw graph responses and formats schema error messages cleanly."""
    if any(err_keyword in str(raw_response) for err_keyword in ["SyntaxError", "The provided schema does not contain", "invalid syntax"]):
        return "The requested relationship or entity type is not defined in the Neo4j Knowledge Graph schema.", True
    elif "unavailable" in str(raw_response).lower() or "error" in str(raw_response).lower():
        return str(raw_response), True
    return str(raw_response), False

# --- Page Configuration ---
st.set_page_config(
    page_title="Movie Knowledge Graph vs Vector RAG",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E88E5; margin-bottom: 0px; }
    .sub-title { font-size: 1.02rem; color: #9E9E9E; margin-bottom: 25px; }

    .card-graph { background-color: #0E2A47; border-left: 5px solid #1E88E5; padding: 16px; border-radius: 8px; margin-bottom: 15px; }
    .card-vector { background-color: #3D2C00; border-left: 5px solid #FFC107; padding: 16px; border-radius: 8px; margin-bottom: 15px; }

    div[data-baseweb="input"] {
        background-color: #1E222D !important;
        border: 1.5px solid #3B4252 !important;
        border-radius: 8px !important;
        transition: all 0.25s ease-in-out !important;
    }
    div[data-baseweb="input"]:hover {
        border-color: #1E88E5 !important;
        box-shadow: 0 0 10px rgba(30, 136, 229, 0.4) !important;
    }
    div[data-baseweb="input"] input {
        color: #FFFFFF !important;
        font-size: 1.05rem !important;
    }

    .stSidebar div.stButton > button {
        width: 100% !important;
        background-color: #1E222D !important;
        color: #E0E0E0 !important;
        border: 1px solid #3B4252 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-weight: 500 !important;
        text-align: left !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stSidebar div.stButton > button:hover {
        background-color: #1E88E5 !important;
        color: #FFFFFF !important;
        border-color: #64B5F6 !important;
        box-shadow: 0px 4px 12px rgba(30, 136, 229, 0.35) !important;
        transform: translateY(-1px);
    }

    div.stButton > button[kind="primary"] {
        background-color: #1E88E5 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    .hop-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-left: 5px solid #238636;
        padding: 16px;
        border-radius: 8px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<div class="main-title">🎬 Movie Knowledge Graph vs Vector RAG</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Comparative Evaluation Framework for Multi-Hop Graph QA</div>', unsafe_allow_html=True)

# Initialize Session State
if "user_query" not in st.session_state:
    st.session_state["user_query"] = ""

# --- Sidebar Quick Fill Buttons ---
st.sidebar.header("📌 Quick Fill Sample Questions")
st.sidebar.caption("Click any button below to instantly populate the search box:")

if st.sidebar.button("1-Hop: Direct Relationship"):
    st.session_state["user_query"] = "Who directed the movie Game Changer?"
    st.rerun()

if st.sidebar.button("2-Hop: Interconnected Query"):
    st.session_state["user_query"] = "Which directors directed movies starring actors in Katha Kamamishu?"
    st.rerun()

if st.sidebar.button("3-Hop: Multi-Step Traversal"):
    st.session_state["user_query"] = "Which actors starred in movies that had music composed by Bheems Ceciroleo?"
    st.rerun()

if st.sidebar.button("Multi-Hop Broad Question"):
    st.session_state["user_query"] = "Tell me about S.S. Rajamouli movies and who acted in them?"
    st.rerun()

st.sidebar.markdown("---")

# --- Tab Layout ---
tab1, tab2 = st.tabs([
    "⚡ Live Query Comparison", 
    "🕸️ Graph Schema & Architecture"
])

# ==============================================================================
# TAB 1: LIVE QUERY COMPARISON
# ==============================================================================
with tab1:
    st.write("Enter **any question** below to see how both Graph RAG and Vector RAG process it in real time:")

    user_input = st.text_input(
        label="User Question Input Box",
        key="user_query",
        placeholder="Type your movie question here...",
        label_visibility="collapsed"
    )

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        run_query = st.button("🚀 Run Comparison", type="primary", use_container_width=True)

    if run_query:
        if not user_input.strip():
            st.warning("Please enter a question first or select a sample question from the sidebar.")
        else:
            st.markdown("---")
            col_graph, col_vector = st.columns(2)

            # ------------------ GRAPH RAG COLUMN ------------------
            with col_graph:
                st.markdown('<div class="card-graph"><h3>🕸️ Graph RAG Engine</h3><p>Graph Traversal via Cypher & Neo4j Database</p></div>', unsafe_allow_html=True)
                
                with st.spinner("Querying Neo4j Graph Database..."):
                    t0 = time.time()
                    try:
                        g_raw = query_graph_rag(user_input)
                    except Exception as ex:
                        g_raw = f"Graph RAG Error: {str(ex)}"
                    graph_lat = round(time.time() - t0, 3)

                st.metric(label="Execution Latency", value=f"{graph_lat} sec")
                
                # Extract response text and debug context
                if isinstance(g_raw, dict):
                    raw_text_ans = g_raw.get("result", g_raw.get("answer", str(g_raw)))
                    cypher_code = g_raw.get("cypher", g_raw.get("generated_cypher", g_raw.get("query", None)))
                    graph_records = g_raw.get("context", g_raw.get("raw_results", g_raw.get("intermediate_steps", None)))
                else:
                    raw_text_ans = str(g_raw)
                    cypher_code = None
                    graph_records = None

                g_answer, is_error = format_graph_response(raw_text_ans)
                
                st.markdown("#### 🤖 Final Answer")
                if is_error or "don't know" in g_answer.lower():
                    st.error(g_answer)
                else:
                    st.success(g_answer)

                with st.expander("🔍 View Generated Cypher Query & Graph Context"):
                    if cypher_code:
                        st.subheader("Generated Cypher Query")
                        st.code(cypher_code, language="cypher")
                    else:
                        st.info("ℹ️ Cypher query was dynamically generated and executed against Neo4j.")

                    if graph_records:
                        st.subheader("Raw Graph Context From Neo4j")
                        st.json(graph_records)

            # ------------------ VECTOR RAG COLUMN ------------------
            with col_vector:
                st.markdown('<div class="card-vector"><h3>📚 Vector RAG Engine</h3><p>Semantic Similarity Search over Unstructured Text Chunks</p></div>', unsafe_allow_html=True)
                
                with st.spinner("Searching Chroma Vector Embeddings..."):
                    t0 = time.time()
                    try:
                        v_answer = query_vector_rag(user_input)
                    except Exception as ex:
                        v_answer = f"Vector RAG Error: {str(ex)}"
                    vector_lat = round(time.time() - t0, 3)

                st.metric(label="Execution Latency", value=f"{vector_lat} sec")

                st.markdown("#### 🤖 Final Answer")
                if "not have enough information" in v_answer.lower() or "don't know" in v_answer.lower() or "error" in v_answer.lower():
                    st.warning(v_answer)
                else:
                    st.success(v_answer)

                with st.expander("ℹ️ Why Vector RAG Struggles on Multi-Hop Queries", expanded=True):
                    st.write("""
                    **Retrieval Bottleneck:** 
                    Vector search embeds chunks of text independently based on semantic similarity.
                    When a query requires joining information across multiple entities (e.g., *Movie A ➔ MusicDirector ➔ Movie B ➔ Actor*), 
                    Vector RAG fails to perform relational joins, leading to missing context or complete answer refusal.
                    """)

            # ------------------ DYNAMIC QUERY COMPLEXITY BANNER ------------------
            hop_type, hop_desc = detect_query_hops(user_input)
            st.markdown(f"""
            <div class="hop-card">
                <h4 style="margin:0px; color:#4CAF50;">🏷️ Dynamic Query Complexity Analysis</h4>
                <p style="margin-top:6px; margin-bottom:4px; font-size:1.05rem;">
                    Detected Classification: <strong>{hop_type}</strong>
                </p>
                <p style="margin:0px; color:#A0A0A0; font-size:0.92rem;">
                    {hop_desc}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # ------------------ PROBLEM STATEMENT 3: EVALUATION METRICS SCORECARD ------------------
            ground_truth_entities = find_ground_truth(user_input)

            if ground_truth_entities is not None:
                st.markdown("---")
                st.markdown("### 📊 Benchmark Evaluation Metrics Scorecard")

                # Compute metrics using ground truth entities
                g_ret_acc, g_ans_f1 = compute_rag_metrics(
                    context_raw=str(graph_records) + " " + str(cypher_code) + " " + g_answer,
                    answer_str=g_answer,
                    ground_truth=ground_truth_entities
                )
                
                v_ret_acc, v_ans_f1 = compute_rag_metrics(
                    context_raw=v_answer,
                    answer_str=v_answer,
                    ground_truth=ground_truth_entities
                )

                # Determine Winning System
                win_speed = "Vector RAG (Speed)" if vector_lat <= graph_lat else "Graph RAG (Speed)"
                win_ret = "Graph RAG (Recall)" if g_ret_acc >= v_ret_acc else "Vector RAG (Recall)"
                win_ans = "Graph RAG (F1-Score)" if g_ans_f1 >= v_ans_f1 else "Vector RAG (F1-Score)"

                # Structured Evaluation Table
                eval_dict = {
                    "Evaluation Metric": ["Speed (Latency)", "Retrieval Accuracy (Recall)", "Answer Accuracy (F1-Score)"],
                    "Graph RAG Engine": [f"{graph_lat} sec", f"{g_ret_acc}%", f"{g_ans_f1}%"],
                    "Vector RAG Engine": [f"{vector_lat} sec", f"{v_ret_acc}%", f"{v_ans_f1}%"],
                    "Winning System": [win_speed, win_ret, win_ans]
                }
                
                st.table(pd.DataFrame(eval_dict))

                # Visual Performance Comparison Bar Charts
                st.markdown("#### 📈 Visual Performance Comparison")
                
                chart_df = pd.DataFrame({
                    "Engine": ["Graph RAG", "Vector RAG"],
                    "Latency (sec)": [graph_lat, vector_lat],
                    "Retrieval Recall (%)": [g_ret_acc, v_ret_acc],
                    "Answer F1-Score (%)": [g_ans_f1, v_ans_f1]
                }).set_index("Engine")

                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.caption("⏱️ **Execution Latency** *(Lower is better)*")
                    st.bar_chart(chart_df[["Latency (sec)"]])
                    
                with col_chart2:
                    st.caption("🎯 **Retrieval Recall & Answer F1-Score (%)** *(Higher is better)*")
                    st.bar_chart(chart_df[["Retrieval Recall (%)", "Answer F1-Score (%)"]])

            else:
                st.markdown("---")
                st.info("💡 **Note:** Real-time Retrieval Accuracy (Recall) and Answer Accuracy (F1-Score) evaluation metrics are displayed when testing questions from `test_questions.json` (or sidebar quick fills). For custom questions, full traversal results and execution speeds are shown without metric scorecards.")

    else:
        st.info("👆 Enter any question in the search box above (or click a sample question on the left) and click **🚀 Run Comparison** to see real-time results.")

# ==============================================================================
# TAB 2: GRAPH SCHEMA & SYSTEM ARCHITECTURE
# ==============================================================================

with tab2:
    st.subheader("🕸️ Neo4j Knowledge Graph Schema")

    col_nodes, col_edges = st.columns(2)

    with col_nodes:
        st.markdown("""
        **Node Entities:**

        * 🎬 `Movie`
          *(title, release_year, language, holiday_season, box_office)*

        * 🎭 `Actor`
          *(name)*

        * 🎥 `Director`
          *(name)*

        * 🎵 `MusicDirector`
          *(name)*

        * ✍️ `Writer`
          *(name)*

        * ✂️ `Editor`
          *(name)*

        * 📷 `Cinematographer`
          *(name)*

        * 👤 `Producer`
          *(name)*

        * 🏢 `ProductionHouse`
          *(name)*

        * 🏷️ `Genre`
          *(name)*

        """)

    with col_edges:
        st.markdown("""
        **Relationship Edges:**

        * `(:Actor)-[:ACTED_IN]->(:Movie)`

        * `(:Director)-[:DIRECTED]->(:Movie)`

        * `(:MusicDirector)-[:COMPOSED_MUSIC_FOR]->(:Movie)`

        * `(:Writer)-[:WROTE]->(:Movie)`

        * `(:Editor)-[:EDITED]->(:Movie)`

        * `(:Cinematographer)-[:FILMED]->(:Movie)`

        * `(:Producer)-[:PRODUCED]->(:Movie)`

        * `(:ProductionHouse)-[:PRODUCED_BY_BANNER]->(:Movie)`

        * `(:Movie)-[:BELONGS_TO]->(:Genre)`

        """)

    st.markdown("---")
    st.subheader("🏗️ System Architecture Flow")

    st.code("""
    [ User Input Question ]
               │
               ├──► [ Graph RAG ]  ──► Text-to-Cypher Prompt ──► Gemini 2.5 Flash ──► Neo4j Database ──► Synthesized Answer
               │
               └──► [ Vector RAG ] ──► Vector Similarity Search ──► Chroma Vector Store ──► Context Retrieval ──► Synthesized Answer
    """, language="text")
