## 🛠️ System Architecture & Technical Stack

This project is built as a containerized, document-based RAG (Retrieval-Augmented Generation) knowledge assistant designed for secure and grounded question answering[cite: 1].

### Core Technology Stack
* **Language & Framework:** Python 3.10+, FastAPI (typed request/response models)[cite: 1]
* **RAG Engine:** LlamaIndex[cite: 1]
* **Vector Database:** PostgreSQL with `pgvector` extension[cite: 1]
* **Containerization:** Docker & Docker Compose
* **Interface:** Streamlit / Web UI[cite: 1]

### System Workflow
1. **Document Ingestion:** Sources (PDF, TXT, Markdown) are processed, split into manageable chunks, and embedded with metadata (document ID, title, chunk index, page/section)[cite: 1].
2. **Vector Storage & Retrieval:** Embeddings are stored in PostgreSQL (`pgvector`), enabling similarity search to pull the top-$k$ relevant context chunks for any user question[cite: 1].
3. **Grounded Generation & Citations:** The LLM receives *only* the retrieved context to formulate an answer, accompanied by explicit source citations (document name, page, and chunk previews) and a fallback for unsupported questions[cite: 1].

### Database Schema Objects
* **Document:** Stores metadata (id, title, source_type, file_path, created_at)[cite: 1].
* **Chunk:** Stores text slices tied to documents (id, document_id, text, page, chunk_index)[cite: 1].
* **Embedding:** Stores high-dimensional vector representations (chunk_id, vector, model_name)[cite: 1].
* **ChatMessage / EvaluationCase:** Tracks interaction history and automated evaluation metrics[cite: 1].
