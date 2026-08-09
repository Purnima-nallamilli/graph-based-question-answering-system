# Technical Report
## Graph-Based Question Answering System using Graph RAG and Vector RAG

---

## 1. Introduction

Traditional Retrieval-Augmented Generation (RAG) retrieves information based on semantic similarity between a query and stored text chunks. This works well for direct factual questions but struggles when a question requires connecting multiple related entities.

This project implements **Problem Statement 3 – Graph-Based Question Answering System** in the movie domain, comparing two retrieval approaches on the same dataset: **Graph RAG** (Neo4j Knowledge Graph) and **Vector RAG** (ChromaDB). The Knowledge Graph models movies and related entities as connected nodes, enabling relationship-aware, multi-hop retrieval, while the Vector RAG pipeline retrieves semantically similar chunks via embeddings. Both use Google Gemini 2.5 Flash for query processing and answer generation.

A Streamlit application runs the same question through both pipelines and compares them on retrieval accuracy, answer accuracy, latency, multi-hop reasoning, and response completeness.

---

## 2. Problem Statement

Problem Statement 3 requires building a Knowledge-Graph-based QA system for a chosen domain, storing it in a graph database, answering questions via graph traversal, and comparing performance against a traditional Vector RAG system.

The movie domain was selected: Neo4j powers structured relationship-based retrieval, and ChromaDB powers semantic vector retrieval. Both are evaluated on the same benchmark questions — single-hop, two-hop, and three-hop — to identify where graph-based retrieval outperforms vector retrieval, particularly for multi-relationship questions.

---

## 3. Objectives

- Build a structured movie Knowledge Graph using Neo4j.
- Design meaningful nodes and relationships between movie-domain entities.
- Implement Graph RAG using natural-language-to-Cypher query generation.
- Implement Vector RAG using ChromaDB and semantic embeddings.
- Evaluate both approaches on the same benchmark questions.
- Compare retrieval accuracy, answer accuracy, execution speed, and response completeness.

---

# 4. System Overview

Two independent retrieval pipelines sit behind a common Streamlit interface. A submitted question is processed through both pipelines simultaneously.

**Graph RAG:** converts the question to a Cypher query, executes it against Neo4j, retrieves graph information, and generates the final response with Gemini.

**Vector RAG:** embeds the question, searches ChromaDB for semantically similar chunks, and supplies that context to Gemini for answer generation.

Outputs from both pipelines are shown side by side, with execution latency recorded and benchmark evaluation applied.

**Stack:** Python, Streamlit, LangChain, Google Gemini, Neo4j, ChromaDB, Cypher, Google embedding models.

---

# 5. Graph Design

Rather than storing movie information as isolated documents, the graph models the domain as interconnected entities.

## 5.1 Node Types

| Node | Description |
|---|---|
| `Movie` | Movie information |
| `Actor` | Actors appearing in movies |
| `Director` | Directors of movies |
| `MusicDirector` | Music composers |
| `Writer` | Story and screenplay writers |
| `Editor` | Film editors |
| `Cinematographer` | Cinematographers |
| `Producer` | Movie producers |
| `ProductionHouse` | Production banners |
| `Genre` | Movie genres |

## 5.2 Relationship Types

| Relationship | Meaning |
|---|---|
| `ACTED_IN` | Actor → Movie |
| `DIRECTED` | Director → Movie |
| `COMPOSED_MUSIC_FOR` | Music Director → Movie |
| `WROTE` | Writer → Movie |
| `EDITED` | Editor → Movie |
| `FILMED` | Cinematographer → Movie |
| `PRODUCED` | Producer → Movie |
| `PRODUCED_BY_BANNER` | Production House → Movie |
| `BELONGS_TO` | Movie → Genre |

This structure lets the system explicitly follow relationships, so multi-hop questions traverse several connected nodes rather than relying on a single text chunk. The graph is stored in Neo4j and populated via the project's ingestion pipeline.

### Graph Schema and Architecture

![Graph Schema and Architecture](screenshots/graph_schema_architecture.png)


### Knowledge Graph in neo4j aura

![Graph Schema and Architecture](screenshots/neo4j_database_overview.png)


---

# 6. Retrieval Approach

## 6.1 Graph RAG

1. User submits a natural-language question.
2. Gemini 2.5 Flash interprets it.
3. A Cypher query is generated per the graph schema.
4. The query runs against Neo4j.
5. Relevant nodes/relationships are retrieved.
6. Retrieved graph context is passed to Gemini.
7. Gemini generates the final answer.

Explicit relationship representation makes this approach well-suited to multi-hop questions.

## 6.2 Vector RAG

1. User submits the same question.
2. The question is embedded.
3. ChromaDB performs semantic similarity search.
4. Relevant chunks are retrieved.
5. Context is supplied to Gemini 2.5 Flash.
6. Gemini generates the final answer.

This is simpler and effective for direct factual questions, but semantic similarity doesn't explicitly preserve relationships between entities.

---

# 7. Experimental Comparison

A common benchmark ensures both pipelines receive identical questions, spanning:

- **Single-hop** – one direct relationship.
- **Two-hop** – two connected relationships.
- **Three-hop** – multiple connected relationships.

| Metric | Purpose |
|---|---|
| Retrieval Accuracy | Whether relevant information is retrieved |
| Answer Accuracy | Correctness of the final answer |
| Execution Latency | Processing time |
| Multi-Hop Reasoning | Ability to follow connected relationships |
| Response Completeness | Whether the pipeline completes the task |

### Comparison Screenshot

![Graph RAG vs Vector RAG Comparison](screenshots/comparison_results.png)

Running the same query through both pipelines lets the evaluator directly compare retrieved information, generated answers, and execution time.

---

# 8. Evaluation Results

For the demonstrated relationship-intensive evaluation:

| Metric | Graph RAG | Vector RAG |
|---|---:|---:|
| Execution Latency | 4.735 sec | 3.458 sec |
| Retrieval Accuracy | 90% | 30% |
| Answer Accuracy | 95% | 20% |
| Execution Status | Completed | Partial |

Vector RAG was faster (3.458s vs 4.735s), since Graph RAG performs query generation and traversal before generating a response. However, Graph RAG achieved substantially higher retrieval and answer accuracy on this relationship-intensive query, as its explicit graph structure allowed it to follow the required relationships, unlike Vector RAG's reliance on semantic similarity alone.

These figures reflect the demonstrated evaluation on this project's dataset and benchmark, not a universal Graph RAG vs. Vector RAG benchmark.

### Evaluation Metrics Screenshot

![Evaluation Metrics](screenshots/evaluation_metrics.png)

---

# 9. Observations

**Graph RAG** performed strongly on multi-entity relationship questions, since relationships are explicitly stored in Neo4j and retrieval can follow a defined path — this also gives better structural explainability, as retrieved information maps to specific nodes/relationships.

**Vector RAG** showed lower latency and works well for straightforward factual questions without needing an explicit graph. However, complex relational questions are harder, since semantically similar chunks don't necessarily preserve the full relationship chain a multi-hop question needs.

**Overall:** the two approaches have different strengths — **Graph RAG suits structured, relationship-heavy, multi-hop questions; Vector RAG suits fast semantic retrieval of straightforward facts.** Neither is universally better; the right choice depends on the query's structure and reasoning needs.

---

# 10. Trade-offs

## Graph RAG
**Advantages:** explicit entity/relationship representation; strong multi-hop reasoning; relationship-aware retrieval; better structural explainability; suited to highly connected domains.
**Limitations:** needs careful schema design; requires maintaining nodes/relationships; Cypher generation adds processing overhead; more complex to build than basic vector indexing.

## Vector RAG
**Advantages:** simple semantic retrieval architecture; fast for straightforward questions; easy to apply to text data; no explicit relationship schema required.
**Limitations:** relationships not explicitly represented; multi-hop reasoning is difficult; relevant chunks may not preserve the needed relationship chain; lower structural explainability than graph traversal.

---

# 11. Challenges

- Designing a graph schema that clearly represents movie entities and relationships.
- Converting natural-language questions into valid Cypher queries.
- Keeping both pipelines on the same dataset for a fair comparison.
- Handling multi-hop questions requiring several connected relationships.
- Measuring retrieval quality and answer accuracy consistently.
- Integrating Neo4j, ChromaDB, Gemini, LangChain, and Streamlit into one application.
- Balancing retrieval accuracy with execution latency.

---

# 12. Future Improvements

- Implement a hybrid Graph + Vector retrieval strategy.
- Expand the movie dataset for greater knowledge coverage.
- Add more two-hop and three-hop benchmark questions.
- Support real-time Knowledge Graph updates.
- Add further graph-based retrieval approaches for comparison.
- Introduce Precision@K, Recall@K, and F1-score metrics.
- Improve Cypher validation and error handling.
- Add conversational multi-turn QA.
- Deploy via Docker or a cloud platform.

---

# 13. Conclusion

This project delivers a working Graph-Based QA system comparing Graph RAG with traditional Vector RAG over the same movie-domain dataset, combining Neo4j, ChromaDB, Google Gemini 2.5 Flash, LangChain, and Streamlit. The Knowledge Graph explicitly models relationships between movies, actors, directors, writers, producers, genres, and other entities, enabling structured traversal for multi-hop questions.

The comparison shows Vector RAG offers lower latency for semantic retrieval, while Graph RAG delivers stronger retrieval and answer accuracy for relationship-intensive questions — demonstrating graph retrieval's core advantage: explicit relationships make it easier to reason across multiple connected entities.

**Graph RAG is most valuable when questions depend on relationships and multi-hop reasoning, while Vector RAG remains useful for fast semantic retrieval of straightforward information.**

---
