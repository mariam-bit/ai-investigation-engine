# AI Investigation Engine

An advanced, production-ready RAG-based (Retrieval-Augmented Generation) document analysis and investigation engine built with **FastAPI**, **Streamlit**, **ChromaDB**, **LangChain**, and the **Google Gemini API**.

Unlike standard document chat tools, this engine is designed to handle complex multi-source inquiries, perform hybrid semantic/keyword search, execute structured tool calls, cross-reference multiple document formats, and deliver reasoned answers with direct evidence citations.

---

## Technical Architecture & Stack

- **Backend Framework**: FastAPI (Python 3.14) delivering RESTful endpoints (`/ingest`, `/upload`, `/ask`).
- **User Interface**: Streamlit web application providing intuitive document management, real-time querying, and source inspection.
- **Vector Storage**: ChromaDB with persistent storage (`./chroma_db`).
- **Embeddings**: HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`).
- **LLM Engine**: Google Gemini API (`google-genai` SDK) featuring an automated fallback and retry mechanism across models (`gemini-3.7-flash` → `gemini-3.5-flash-lite` → `gemma-4-31b-it` → `gemini-3.8-flash`).
- **Search Logic**: Hybrid Search combining semantic vector search with custom algorithmic keyword relevance scoring.

---

## Project Structure

```text
ai-investigation-engine/
│
├── main.py               # FastAPI backend, RAG pipeline, tool calling, & hybrid search
├── app.py                # Streamlit user interface
├── evaluate.py           # Automated evaluation suite 
├── requirements.txt      # Python dependencies
├── chroma_db/            # Persistent ChromaDB vector storage
└── uploaded_docs/        # Ingested multi-format files (PDF, TXT, CSV)