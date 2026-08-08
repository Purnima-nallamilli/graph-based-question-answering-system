# Technical Report
## Graph-Based Question Answering System using Graph RAG and Vector RAG

---

## 1. Introduction

Traditional Retrieval-Augmented Generation (RAG) systems primarily retrieve information using semantic similarity between a user query and stored text chunks. Although this works well for direct factual questions, it can become challenging when a question requires connecting multiple related entities.

This project implements the solution for **Problem Statement 3 – Graph-Based Question Answering System** using the movie domain. The system compares two retrieval approaches over the same dataset: **Graph RAG** using a Neo4j Knowledge Graph and **Vector RAG** using ChromaDB.

The Knowledge Graph represents movies and their associated entities as connected nodes and relationships, allowing the system to perform relationship-aware and multi-hop retrieval. The Vector RAG pipeline retrieves semantically similar document chunks using embeddings. Both approaches use Google Gemini 2.5 Flash for query processing and answer generation.

An interactive Streamlit application allows the same question to be executed through both pipelines and provides comparative evaluation based on retrieval accuracy, answer accuracy, execution latency, multi-hop reasoning capability, and response completeness.

---

## 2. Problem Statement

Problem Statement 3 requires the development of a Question Answering system using a Knowledge Graph. The system must build a graph from a selected domain, store it in a graph database, answer questions through graph traversal, and compare its performance with a traditional Vector RAG system.

For this project, the movie domain was selected. The system uses a Neo4j Knowledge Graph for structured relationship-based retrieval and ChromaDB for semantic vector retrieval. Both approaches are evaluated using the same benchmark questions, including single-hop, two-hop, and three-hop questions.

The purpose of the comparison is to understand where graph-based retrieval provides advantages over traditional vector retrieval, particularly for questions requiring multiple connected relationships.

---

## 3. Objectives

The main objectives of the project are:

- Build a structured movie Knowledge Graph using Neo4j.
- Design meaningful nodes and relationships between movie-domain entities.
- Implement Graph RAG using natural-language-to-Cypher query generation.
- Implement Vector RAG using ChromaDB and semantic embeddings.
- Evaluate both approaches using the same benchmark questions.
- Compare retrieval accuracy, answer accuracy, execution speed, and response completeness.

---

# 4. System Overview

The system provides two independent retrieval pipelines behind a common Streamlit interface.

When a user submits a movie-related question, the application processes the same question through both Graph RAG and Vector RAG. The Graph RAG pipeline converts the natural-language question into a Cypher query, executes the query against Neo4j, retrieves the required graph information, and generates the final response using Gemini.

The Vector RAG pipeline converts the question into an embedding, searches ChromaDB for semantically similar document chunks, and supplies the retrieved context to Gemini for answer generation.

The outputs of both pipelines are presented for comparison. The application also records execution latency and evaluates the responses using the project's benchmark questions.

The implementation uses Python, Streamlit, LangChain, Google Gemini, Neo4j, ChromaDB, Cypher, and Google embedding models.

---

# 5. Graph Design

The Knowledge Graph is the central component of the Graph RAG pipeline. Instead of storing movie information as isolated documents, the system models the movie domain as interconnected entities.

## 5.1 Node Types

The graph contains the following major node labels:

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

The main relationships in the Knowledge Graph are:

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

This graph structure allows the system to explicitly follow relationships between entities. For example, a multi-hop question can require traversal across several connected nodes rather than retrieving a single text chunk.

The graph is stored in Neo4j and populated using the project's ingestion pipeline.

### Graph Schema and Architecture

![Graph Schema and Architecture](screenshots/graph_schema_architecture.png)

---

# 6. Retrieval Approach

The project implements two retrieval approaches using the same underlying movie information.

## 6.1 Graph RAG

Graph RAG uses the Knowledge Graph to retrieve structured information through graph traversal.

The workflow is:

1. The user submits a natural-language question.
2. Gemini 2.5 Flash interprets the question.
3. A Cypher query is generated according to the graph schema.
4. The Cypher query is executed against Neo4j.
5. Relevant nodes and relationships are retrieved.
6. The retrieved graph context is provided to Gemini.
7. Gemini generates the final natural-language answer.

The main advantage of this approach is that relationships are explicitly represented. This makes Graph RAG particularly suitable for multi-hop questions.

## 6.2 Vector RAG

Vector RAG uses semantic similarity to retrieve relevant information.

The workflow is:

1. The user submits the same question.
2. The question is converted into an embedding.
3. ChromaDB performs semantic similarity search.
4. Relevant document chunks are retrieved.
5. The retrieved context is supplied to Gemini 2.5 Flash.
6. Gemini generates the final answer.

Vector RAG provides a simpler retrieval mechanism and is effective for direct factual or document-level questions. However, semantic similarity alone does not explicitly represent the relationships between entities.

---

# 7. Experimental Comparison

A common benchmark dataset is used so that Graph RAG and Vector RAG receive the same questions. This provides a consistent basis for comparing the two retrieval strategies.

The benchmark contains questions with different reasoning requirements:

- **Single-hop questions** – require one direct relationship.
- **Two-hop questions** – require connecting two relationships.
- **Three-hop questions** – require multiple connected relationships.

The evaluation considers:

| Metric | Purpose |
|---|---|
| Retrieval Accuracy | Measures whether relevant information is retrieved |
| Answer Accuracy | Measures correctness of the final answer |
| Execution Latency | Measures processing time |
| Multi-Hop Reasoning | Measures ability to follow connected relationships |
| Response Completeness | Measures whether the pipeline successfully completes the task |

### Comparison Screenshot

![Graph RAG vs Vector RAG Comparison](screenshots/graph_vs_vector_comparison.png)

The same user query is executed through both pipelines, allowing the evaluator to directly observe differences in retrieved information, generated answers, and execution time.

---

# 8. Evaluation Results

The evaluation interface provides a direct comparison of Graph RAG and Vector RAG using the benchmark questions.

For the demonstrated relationship-intensive evaluation, the observed results were:

| Metric | Graph RAG | Vector RAG |
|---|---:|---:|
| Execution Latency | 4.735 sec | 3.458 sec |
| Retrieval Accuracy | 90% | 30% |
| Answer Accuracy | 95% | 20% |
| Execution Status | Completed | Partial |

The observed results show a clear trade-off.

Vector RAG completed the demonstrated query faster, with an observed latency of 3.458 seconds. Graph RAG required 4.735 seconds, mainly because the pipeline performs query generation and graph traversal before generating the final response.

However, Graph RAG achieved substantially higher retrieval and answer accuracy for the relationship-intensive query. Its explicit graph structure allowed the system to follow the required relationships between entities, whereas Vector RAG relied on semantic similarity between stored text chunks.

These values represent the observed results for the demonstrated evaluation and should be interpreted within the scope of the project's dataset and benchmark rather than as a universal benchmark of Graph RAG versus Vector RAG.

### Evaluation Metrics Screenshot

![Evaluation Metrics](screenshots/evaluation_metrics.png)

---

# 9. Observations

The experimental comparison produced several important observations.

### Graph RAG

Graph RAG performed strongly on questions requiring relationships between multiple entities. Since the relationships are explicitly stored in Neo4j, the retrieval process can follow a defined path through the graph.

This makes Graph RAG particularly suitable for multi-hop questions where the answer depends on combining information from several connected entities.

Graph traversal also provides better structural explainability because the retrieved information can be associated with specific nodes and relationships.

### Vector RAG

Vector RAG demonstrated lower execution latency in the observed comparison. Semantic retrieval is useful for straightforward factual questions because relevant information can be retrieved without constructing or traversing an explicit graph.

However, complex relational questions can be more difficult because semantically similar document chunks do not necessarily preserve the complete chain of relationships required to answer a multi-hop question.

### Overall Observation

The experiment indicates that the two approaches have different strengths.

**Graph RAG is more suitable for structured, relationship-heavy and multi-hop questions, while Vector RAG is effective for fast semantic retrieval and straightforward factual questions.**

Therefore, the results do not suggest that one retrieval method is universally better. The appropriate approach depends on the structure and reasoning requirements of the query.

---

# 10. Trade-offs

## Graph RAG

### Advantages

- Explicit representation of entities and relationships.
- Strong support for multi-hop reasoning.
- Relationship-aware retrieval.
- Better structural explainability.
- Suitable for highly connected domains.

### Limitations

- Requires careful graph schema design.
- Requires maintaining nodes and relationships.
- Cypher generation introduces additional processing.
- Graph construction is more complex than basic vector indexing.

## Vector RAG

### Advantages

- Simple semantic retrieval architecture.
- Fast retrieval for straightforward questions.
- Easy to apply to text-based information.
- Does not require an explicit relationship schema.

### Limitations

- Relationships are not explicitly represented.
- Multi-hop reasoning can be difficult.
- Relevant chunks may not preserve the required relationship chain.
- Lower structural explainability compared with graph traversal.

---

# 11. Challenges

Several challenges were encountered during implementation:

- Designing a graph schema that represents different movie entities and their relationships clearly.
- Converting natural-language questions into valid Cypher queries.
- Keeping the Graph RAG and Vector RAG pipelines based on the same dataset for a fair comparison.
- Handling multi-hop questions requiring several connected relationships.
- Measuring retrieval quality and answer accuracy consistently.
- Integrating Neo4j, ChromaDB, Gemini, LangChain, and Streamlit into a single application.
- Balancing retrieval accuracy with execution latency.

---

# 12. Future Improvements

The system can be improved in several directions:

- Implement a hybrid Graph + Vector retrieval strategy.
- Expand the movie dataset to increase knowledge coverage.
- Add more two-hop and three-hop benchmark questions.
- Support real-time updates to the Knowledge Graph.
- Add additional graph-based retrieval approaches for comparison.
- Introduce advanced retrieval metrics such as Precision@K, Recall@K, and F1-score.
- Improve Cypher validation and error handling.
- Add conversational multi-turn question answering.
- Deploy the application using Docker or a cloud platform.

---

# 13. Conclusion

This project demonstrates a working Graph-Based Question Answering system that compares Graph RAG with traditional Vector RAG over the same movie-domain dataset.

The system combines a Neo4j Knowledge Graph, ChromaDB vector retrieval, Google Gemini 2.5 Flash, LangChain, and Streamlit. The Knowledge Graph explicitly models relationships between movies, actors, directors, writers, producers, genres, and other entities, enabling structured graph traversal for multi-hop questions.

The experimental comparison shows that Vector RAG can provide lower latency for semantic retrieval, while Graph RAG can provide stronger retrieval and answer accuracy for relationship-intensive questions. The results demonstrate the main advantage of graph-based retrieval: explicit relationships make it easier to reason across multiple connected entities.

Overall, the project shows that **Graph RAG is particularly valuable when the question depends on relationships and multi-hop reasoning, while Vector RAG remains useful for fast semantic retrieval of straightforward information.**

---
