import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from ingest import load_pdf_pages, chunk_pages, store_chunks, get_collection
from rag import answer_question

load_dotenv()

st.set_page_config(page_title="Finance RAG", page_icon="📊")
st.title("📊 Quarterly Financial Results — RAG Assistant")

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY not found. Check your .env file.")
    st.stop()

# --- Upload + Index ---
st.subheader("1. Upload & Index")
uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if st.button("Index uploaded files", disabled=not uploaded_files):
    with st.spinner("Processing..."):
        all_chunks = []
        for f in uploaded_files:
            # Streamlit gives us the file in memory; save it to a temp path so pypdf can open it
            tmp_path = os.path.join(tempfile.mkdtemp(), f.name)
            with open(tmp_path, "wb") as out:
                out.write(f.getbuffer())

            pages = load_pdf_pages(tmp_path)
            chunks = chunk_pages(pages)
            all_chunks.extend(chunks)

        store_chunks(all_chunks)
        st.success(f"{len(uploaded_files)} files processed, {len(all_chunks)} chunks stored")

st.divider()

# --- Ask ---
st.subheader("2. Ask a question")
question = st.text_input("Question")

if st.button("Ask", disabled=not question):
    with st.spinner("Thinking..."):
        result = answer_question(question)

    st.markdown("#### Answer")
    st.write(result["answer"])

    st.markdown("#### Sources")
    for s in result["sources"]:
        st.write(f"- `{s['file']}`, page {s['page']}")