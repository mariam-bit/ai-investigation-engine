# AI Usage Report

## 1. AI Tools Used
 **Claude (Anthropic)**: Used primarily for error handling, debugging Streamlit exceptions, and refining the multi-file ingestion loop logic.
 **Gemini (Google)**: Used for general architectural guidance and structuring the hybrid RAG + conversational prompt.

## 2. How the AI Helped
 **Error Handling & Debugging**: Claude helped diagnose and resolve missing package errors (`pypdf`) and fixed the `NameError` / singular vs. plural state mismatches in the Streamlit file uploader loop.
***Prompt Engineering**: Assisted in designing a flexible prompt that switches between general Q&A and document-based RAG analysis seamlessly.

## 3. Independent Modifications & Decisions
 **UI/UX Refinement**: Chose to structure the layout independently, ensuring the chat interface stays clean and functional.
 **Pipeline Integration**: Verified and tested the ChromaDB vector storage integration and chunking parameters manually to fit the project requirements.