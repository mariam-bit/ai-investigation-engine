import streamlit as st
import requests

st.set_page_config(page_title="AI Investigation Engine", layout="wide")

API_URL = "http://127.0.0.1:8000"

st.title("AI Investigation Engine")
st.markdown("Advanced RAG-based document analysis, hybrid search, and multi-source reasoning.")

st.sidebar.header("Document Management")
uploaded_file = st.sidebar.file_uploader("Upload Document (PDF, TXT, CSV)", type=["pdf", "txt", "csv"])

if uploaded_file is not None:
    if st.sidebar.button("Ingest File"):
        with st.spinner("Processing and indexing document..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            try:
                res = requests.post(f"{API_URL}/upload", files=files)
                if res.status_code == 200:
                    st.sidebar.success(res.json()["message"])
                else:
                    st.sidebar.error(res.json().get("detail", "Upload failed"))
            except Exception as e:
                st.sidebar.error(f"Connection error: {e}")

st.header("Investigation Query")
question = st.text_input("Enter your investigation question:", placeholder="e.g., What caused payment processing failures in March?")

if st.button("Run Investigation"):
    if question:
        with st.spinner("Analyzing documents across sources..."):
            try:
                res = requests.post(f"{API_URL}/ask", json={"question": question})
                if res.status_code == 200:
                    data = res.json()
                    
                    st.subheader("Investigation Findings")
                    st.write(data["answer"])
                    
                    st.subheader("📚 Source Citations & Evidence")
                    for i, source in enumerate(data["sources"], 1):
                        st.info(f"**Source {i}:** {source}")
                else:
                    st.error(res.json().get("detail", "Query failed"))
            except Exception as e:
                    st.error(f"Failed to connect to backend API: {e}")
    else:
        st.warning("Please enter a question.")