import os
import time
import traceback
import shutil
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader
from google import genai
from google.genai import errors
from google.genai import types

st.set_page_config(page_title="AI Investigation Engine", layout="wide")

persist_directory = "./chroma_db"
UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".csv")

GEMINI_API_KEY = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("⚠️ GEMINI_API_KEY is not set. Please add it to Streamlit Secrets.")
    st.stop()

PRIMARY_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash"]

@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embeddings = load_embeddings()
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=30000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

def generate_with_retry(prompt: str, retries_per_model: int = 1):
    last_error = None
    for model in [PRIMARY_MODEL, *FALLBACK_MODELS]:
        for attempt in range(retries_per_model + 1):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                return response
            except errors.ServerError as e:
                last_error = e
                if attempt < retries_per_model:
                    time.sleep(2)
            except errors.ClientError as e:
                if e.code in (404, 429):
                    last_error = e
                    break
                raise
    raise last_error

def get_system_status() -> str:
    return f"Investigation Engine Status: Operational. Vector DB store: {persist_directory}. Active docs folder: {UPLOAD_DIR}"

st.title("AI Investigation Engine")
st.markdown("Advanced RAG-based document analysis, hybrid search, and multi-source reasoning.")

st.sidebar.header("Document Management")
uploaded_file = st.sidebar.file_uploader("Upload Document (PDF, TXT, CSV)", type=["pdf", "txt", "csv"])

if uploaded_file is not None:
    if st.sidebar.button("Ingest File"):
        with st.spinner("Processing and indexing document..."):
            filename = os.path.basename(uploaded_file.name)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in SUPPORTED_EXTENSIONS:
                st.sidebar.error("Unsupported file format.")
            else:
                file_path = os.path.join(UPLOAD_DIR, filename)
                with open(file_path, "wb") as buffer:
                    buffer.write(uploaded_file.getvalue())
                
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
                        st.sidebar.error("No text could be extracted from this file.")
                    else:
                        ids = [f"{filename}-chunk-{i}" for i in range(len(split_docs))]
                        Chroma.from_documents(
                            split_docs,
                            embeddings,
                            ids=ids,
                            persist_directory=persist_directory,
                        )
                        st.sidebar.success(f"Successfully indexed {len(split_docs)} chunks from {filename}!")
                except Exception as e:
                    st.sidebar.error(f"Error processing file: {e}")

st.header("Investigation Query")
question = st.text_input("Enter your investigation question:", placeholder="e.g., What caused payment processing failures in March?")

if st.button("Run Investigation"):
    if question:
        if not os.path.exists(persist_directory):
            st.warning("Database not initialized. Please upload a document first or run initial ingestion.")
        else:
            with st.spinner("Analyzing documents across sources..."):
                try:
                    vectorstore = Chroma(
                        persist_directory=persist_directory,
                        embedding_function=embeddings,
                    )

                    semantic_docs = vectorstore.similarity_search(question, k=3)
                    all_data = vectorstore.get()
                    keyword_matched_chunks = []
                    query_terms = [word.lower() for word in question.split() if len(word) > 3]
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
                    if "status" in question.lower() or "system" in question.lower():
                        tool_feedback = f"\n[System Tool Executed]: {get_system_status()}\n"

                    prompt = f"""
                    You are an advanced AI Investigation Engine. Answer the user's question using ONLY the provided context and tool outputs below.
                    If the context is insufficient or contradictory, state that clearly and do not make up facts.
                    Always cite your sources/evidence directly from the context.

                    {tool_feedback}
                    Context:
                    {context}

                    Question: {question}
                    """

                    response = generate_with_retry(prompt)

                    st.subheader("Investigation Findings")
                    st.write(response.text)
                    
                    st.subheader("Source Citations & Evidence")
                    if combined_sources:
                        for i, source in enumerate(combined_sources, 1):
                            st.info(f"**Source {i}:** {source}")
                    else:
                        st.info("No external document chunks matched, used baseline reasoning.")

                except Exception as e:
                    st.error(f"An error occurred during investigation: {e}")
    else:
        st.warning("Please enter a question.")