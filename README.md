# 🎬 Graph-Based Question Answering System using Graph RAG and Vector RAG

A Graph-Based Question Answering system that compares **Graph RAG** and **Vector RAG** for answering single-hop and multi-hop movie-related questions using a **Neo4j Knowledge Graph** and **ChromaDB Vector Database**.

---

# 📌 Project Overview

This project implements **Problem Statement 3 – Graph-Based Question Answering System** using a movie-domain dataset.

The system compares two Retrieval-Augmented Generation approaches over the same dataset:

* 🔹 **Graph RAG** using Neo4j
* 🔹 **Vector RAG** using ChromaDB

Graph RAG retrieves information by traversing explicit relationships between entities such as movies, actors, directors, writers, producers, genres, production houses, editors, music directors, and cinematographers.

Vector RAG retrieves relevant information using semantic similarity search over embedded movie data.

An interactive **Streamlit dashboard** executes the same question through both pipelines and allows their responses, latency, and evaluation results to be compared.

---

# ✨ Features

## 🕸️ Knowledge Graph

* Neo4j Knowledge Graph construction
* Multiple movie-domain entity types
* Explicit entity relationships
* Dynamic Cypher query generation
* Multi-hop graph traversal

---

## 📚 Vector Retrieval

* ChromaDB Vector Database
* Google Gemini embeddings
* Semantic similarity search
* Context-based answer generation

---

## 🤖 AI Question Answering

* Google Gemini 2.5 Flash
* Graph RAG pipeline
* Vector RAG pipeline
* Natural-language question processing
* Support for single-hop and multi-hop questions

---

## 📊 Comparative Evaluation

The system compares both approaches using:

* Retrieval Accuracy
* Answer Accuracy
* Execution Latency
* Multi-Hop Reasoning
* Response Completeness

---

## 🖥️ User Interface

* Interactive Streamlit dashboard
* Side-by-side Graph RAG and Vector RAG responses
* Knowledge Graph exploration
* Graph schema and architecture view
* Evaluation metrics visualization

---

# 🏗️ System Architecture

```text
                         User Question
                              │
                              ▼
                    Streamlit Web Application
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
          Graph RAG Pipeline         Vector RAG Pipeline
                 │                         │
          Gemini 2.5 Flash          Gemini Embeddings
                 │                         │
        Cypher Query Generation    Semantic Similarity Search
                 │                         │
                 ▼                         ▼
        Neo4j Knowledge Graph       Chroma Vector Database
                 │                         │
                 └────────────┬────────────┘
                              ▼
                  Comparative Evaluation
                              │
                              ▼
                     Final Answers
```

---

# 🧠 Retrieval Approaches

## 🔷 Graph RAG

The Graph RAG pipeline retrieves structured information by traversing relationships stored in the Neo4j Knowledge Graph.

### Workflow

1. User submits a natural-language question.
2. Gemini 2.5 Flash generates a Cypher query.
3. The query is executed against Neo4j.
4. Relevant nodes and relationships are retrieved.
5. Gemini generates the final response from the retrieved graph context.

### Strengths

* Multi-hop reasoning
* Relationship-aware retrieval
* Structured information retrieval
* Explainable graph traversal

---

## 📚 Vector RAG

The Vector RAG pipeline retrieves semantically similar information from ChromaDB.

### Workflow

1. User submits a question.
2. The question is converted into an embedding.
3. ChromaDB performs similarity search.
4. Relevant document chunks are retrieved.
5. Gemini generates the final response using the retrieved context.

### Strengths

* Fast semantic retrieval
* Effective for direct factual questions
* Simple document-based retrieval
* Lower retrieval overhead

### Limitations

* No explicit relationship traversal
* More challenging multi-hop reasoning
* Retrieved chunks may not preserve complete entity relationships

---

# 🕸️ Knowledge Graph Design

The Knowledge Graph represents the movie domain as interconnected entities rather than isolated documents.

## Node Labels

| Node                 | Description                  |
| -------------------- | ---------------------------- |
| 🎬 `Movie`           | Movie details                |
| 🎭 `Actor`           | Cast members                 |
| 🎥 `Director`        | Film directors               |
| 🎵 `MusicDirector`   | Music composers              |
| ✍️ `Writer`          | Story and screenplay writers |
| ✂️ `Editor`          | Editors                      |
| 📷 `Cinematographer` | Cinematographers             |
| 👤 `Producer`        | Producers                    |
| 🏢 `ProductionHouse` | Production banners           |
| 🎭 `Genre`           | Movie genres                 |

## Relationship Types

| Relationship         | Description              |
| -------------------- | ------------------------ |
| `ACTED_IN`           | Actor → Movie            |
| `DIRECTED`           | Director → Movie         |
| `COMPOSED_MUSIC_FOR` | Music Director → Movie   |
| `WROTE`              | Writer → Movie           |
| `EDITED`             | Editor → Movie           |
| `FILMED`             | Cinematographer → Movie  |
| `PRODUCED`           | Producer → Movie         |
| `PRODUCED_BY_BANNER` | Production House → Movie |
| `BELONGS_TO`         | Movie → Genre            |

This structure enables explicit relationship traversal and supports multi-hop question answering.

---

# 📂 Repository Structure

```text
graph-based-question-answering-system/
│
├── app.py                         # Streamlit application
├── README.md                      # Project documentation
├── REPORT.md                      # Technical report
├── requirements.txt               # Project dependencies
├── .env.example                   # Environment variable template
├── .gitignore
│
├── data/
│   ├── movies_dataset.json        # Processed movie dataset
│   └── test_questions.json        # Benchmark questions
│
├── scripts/
│   ├── wiki_scrapper.py           # Dataset collection
│   ├── patch_data.py              # Metadata enrichment         
│   ├── ingest.py                  # Neo4j graph ingestion
│   ├── ingest_vector.py           # ChromaDB ingestion
│   └── test_conn.py               # Neo4j connection verification
│
├── src/
│   ├── config.py                  # Environment configuration
│   ├── graph_rag.py               # Graph RAG pipeline
│   ├── vector_rag.py              # Vector RAG pipeline
│   └── evaluator.py               # Comparative evaluation
│
└── screenshots/                   # Project screenshots
```

---

# 🛠️ Technologies Used

| Category               | Technologies                 |
| ---------------------- | ---------------------------- |
| Programming Language   | Python 3.11                  |
| User Interface         | Streamlit                    |
| Large Language Model   | Google Gemini 2.5 Flash      |
| Knowledge Graph        | Neo4j AuraDB                 |
| Vector Database        | ChromaDB                     |
| Framework              | LangChain                    |
| Embeddings             | GoogleGenerativeAIEmbeddings |
| Graph Query Language   | Cypher                       |
| Dataset Sources        | Wikipedia, TMDB API          |
| Environment Management | python-dotenv                |
| Version Control        | Git & GitHub                 |

---

# ⚙️ Installation & Setup

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Purnima-nallamilli/graph-based-question-answering-system.git
cd graph-based-question-answering-system
```

---

## 2️⃣ Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configure Environment Variables

Create a `.env` file in the project root using `.env.example` as a template.

```env
GOOGLE_API_KEY=your_google_api_key
TMDB_API_KEY=your_tmdb_api_key
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

Do not commit your `.env` file or API keys to GitHub.

---

# 🚀 Running the Project

## Step 1 — Verify Neo4j Connection

```bash
python scripts/test_conn.py
```

---

## Step 2 — Build the Knowledge Graph

```bash
python scripts/ingest.py
```

This loads the processed movie dataset into Neo4j.

---

## Step 3 — Create the Vector Database

```bash
python scripts/ingest_vector.py
```

This creates the ChromaDB vector store used by the Vector RAG pipeline.

---

## Step 4 — Launch the Application

```bash
streamlit run app.py
```

The Streamlit application will open in the browser.

---

# 💬 Sample Questions

## 1-Hop Question

```text
Who directed the movie Game Changer?
```

---

## 2-Hop Question

```text
Which actors have co-starred in multiple movies with Nandamuri Balakrishna?
```

---

## 3-Hop Question

```text
Which actors starred in movies that had music composed by Bheems Ceciroleo?
```

These questions demonstrate increasing levels of relationship traversal and reasoning complexity.

---

# 📊 Evaluation Methodology

To ensure a fair comparison, **Graph RAG and Vector RAG use the same benchmark questions**.

The evaluation considers:

* ✅ Retrieval Accuracy
* ✅ Answer Accuracy
* ✅ Execution Latency
* ✅ Multi-Hop Reasoning Capability
* ✅ Response Completeness

The benchmark contains:

* Single-Hop Questions
* Two-Hop Questions
* Three-Hop Questions

The application provides comparative results for both retrieval approaches.

---

# 📈 Results & Observations

The evaluation demonstrates different strengths for the two retrieval approaches.

### Graph RAG

* Strong performance on relationship-intensive questions.
* Explicit multi-hop traversal through Neo4j.
* Better structural understanding of connected entities.
* Suitable for complex relational queries.

### Vector RAG

* Efficient semantic retrieval.
* Effective for straightforward factual questions.
* Lower retrieval overhead in the demonstrated comparison.
* More challenging for complex multi-hop relationships.

Overall, **Graph RAG is better suited to relationship-heavy and multi-hop questions, while Vector RAG is useful for fast semantic retrieval of straightforward information.**

---

# ⚠️ Challenges Faced

* Designing a suitable Knowledge Graph schema and relationships.
* Converting natural-language questions into valid Cypher queries.
* Keeping both retrieval approaches based on the same dataset for a fair comparison.
* Handling multi-hop questions.
* Measuring retrieval and answer quality consistently.
* Integrating Neo4j, ChromaDB, Gemini, LangChain, and Streamlit into one application.

---

# 🔮 Future Improvements

Possible improvements include:

* Hybrid Graph + Vector Retrieval
* Larger movie datasets
* More complex multi-hop benchmark questions
* Real-time Knowledge Graph updates
* Advanced evaluation metrics such as Precision@K, Recall@K, and F1-score
* Improved Cypher validation and error handling
* Conversational multi-turn question answering
* Docker and cloud deployment
* Enhanced graph visualization

---

# 🎥 Demonstration

The project can be demonstrated through the Streamlit application, covering:

* Movie question submission
* Graph RAG response generation
* Vector RAG response generation
* Side-by-side response comparison
* Knowledge Graph exploration
* Evaluation metrics

---

# 📄 Technical Report

A detailed technical report covering the system architecture, Graph RAG and Vector RAG approaches, Knowledge Graph design, experimental comparison, observations, trade-offs, challenges, and future improvements is available in:

```text
REPORT.md
```

---

# 👩‍💻 Author

**Purnima Nallamilli**

B.Tech – Information Technology

Vishnu Institute of Technology

GitHub: https://github.com/Purnima-nallamilli

---

# 📄 License

This project was developed as part of an AI Internship Technical Assessment for **Problem Statement 3 – Graph-Based Question Answering System**.
