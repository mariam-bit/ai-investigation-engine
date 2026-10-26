import os
import time
import traceback
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader
from google import genai
from google.genai import errors
from google.genai import types

app = FastAPI(title="AI Investigation Engine", version="2.0")

persist_directory = "./chroma_db"
UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".csv")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

PRIMARY_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemma-4-31b-it", "gemini-3.8-flash"]

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=30000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

sample_docs = [
    "Organization has technical documentation regarding payment system changes in March. Server X malfunctioned during the deployment.",
    "Incident report: March 15, payment processing service experienced degradation due to unexpected server memory leaks.",
    "Log history shows changes applied to the gateway router by the DevOps team at 02:00 AM.",
]


class QueryRequest(BaseModel):
    question: str


def generate_with_retry(prompt: str, retries_per_model: int = 1):
    last_error = None
    for model in [PRIMARY_MODEL, *FALLBACK_MODELS]:
        for attempt in range(retries_per_model + 1):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                print(f"[gemini] answered by {model}")
                return response
            except errors.ServerError as e:
                last_error = e
                print(f"[gemini] {model} attempt {attempt + 1} failed: {e.code}")
                if attempt < retries_per_model:
                    time.sleep(2)
            except errors.ClientError as e:
                if e.code in (404, 429):
                    print(f"[gemini] {model} unavailable ({e.code}), trying next model")
                    last_error = e
                    break
                raise
    raise last_error


def get_system_status() -> str:
    """Tool: Returns operational system status and storage configuration."""
    return f"Investigation Engine Status: Operational. Vector DB store: {persist_directory}. Active docs folder: {UPLOAD_DIR}"


@app.post("/ingest")
def ingest_documents():
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.create_documents(sample_docs)
        ids = [f"sample-chunk-{i}" for i in range(len(docs))]
        Chroma.from_documents(
            docs,
            embeddings,
            ids=ids,
            persist_directory=persist_directory,
        )
        return {"message": f"Successfully ingested {len(docs)} sample chunks into ChromaDB."}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Multi-format document ingestion endpoint (Supports PDF, TXT, CSV)."""
    filename = os.path.basename(file.filename or "")
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext or 'none'}'. Please upload PDF, TXT, or CSV.",
        )

    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if ext == ".pdf":
            docs = PyPDFLoader(file_path).load()
        elif ext == ".txt":
            docs = TextLoader(file_path, encoding="utf-8").load()
        else:  
            docs = CSVLoader(file_path).load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        split_docs = text_splitter.split_documents(docs)

        if not split_docs:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from this file (is it a scanned PDF or empty?).",
            )

        ids = [f"{filename}-chunk-{i}" for i in range(len(split_docs))]
        Chroma.from_documents(
            split_docs,
            embeddings,
            ids=ids,
            persist_directory=persist_directory,
        )
        return {"message": f"Successfully uploaded, parsed, and indexed {len(split_docs)} chunks from {filename}."}

    except HTTPException:
        raise 
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Could not read the file as UTF-8 text.")
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
def ask_question(request: QueryRequest):
    if not os.path.exists(persist_directory):
        raise HTTPException(
            status_code=400,
            detail="Database not initialized. Please call /ingest or upload documents first.",
        )

    try:
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )

        semantic_docs = vectorstore.similarity_search(request.question, k=3)

        all_data = vectorstore.get()
        keyword_matched_chunks = []
        query_terms = [word.lower() for word in request.question.split() if len(word) > 3]
        semantic_texts = {d.page_content for d in semantic_docs}

        if all_data.get("documents"):
            for doc_text in all_data["documents"]:
                matches = sum(1 for term in query_terms if term in doc_text.lower())
                if matches > 0 and doc_text not in semantic_texts:
                    keyword_matched_chunks.append((matches, doc_text))

        keyword_matched_chunks.sort(key=lambda x: x[0], reverse=True)
        top_keyword_texts = [chunk[1] for chunk in keyword_matched_chunks[:2]]

        combined_sources = [doc.page_content for doc in semantic_docs] + top_keyword_texts
        context = "\n---\n".join(combined_sources)

        tool_feedback = ""
        if "status" in request.question.lower() or "system" in request.question.lower():
            tool_feedback = f"\n[System Tool Executed]: {get_system_status()}\n"

        prompt = f"""
        You are an advanced AI Investigation Engine. Answer the user's question using ONLY the provided context and tool outputs below.
        If the context is insufficient or contradictory, state that clearly and do not make up facts.
        Always cite your sources/evidence directly from the context.

        {tool_feedback}
        Context:
        {context}

        Question: {request.question}
        """

        response = generate_with_retry(prompt)

        return {
            "answer": response.text,
            "sources": combined_sources,
        }

    except HTTPException:
        raise
    except errors.ServerError:
        raise HTTPException(
            status_code=503,
            detail="The Gemini model is overloaded right now. Please try again shortly.",
        )
    except errors.ClientError as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Gemini request rejected: {e}")
    except Exception as e:
        print("--- DETAILED ERROR TRACEBACK ---")
        print(traceback.format_exc())
        print("--------------------------------")
        raise HTTPException(status_code=500, detail=str(e))