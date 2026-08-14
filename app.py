import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Finance RAG", page_icon="📊")
st.title("📊 Quarterly Financial Results — RAG Assistant")

st.subheader("1. Upload & Index")
uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

if st.button("Index uploaded files", disabled=not uploaded_files):
    with st.spinner("Processing..."):
        files_payload = [
            ("files", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files
        ]
        response = requests.post(f"{API_URL}/ingest", files=files_payload)
        result = response.json()
        st.success(f"{result['files']} files processed, {result['chunks']} chunks stored")

st.divider()


st.subheader("2. Ask a question")
question = st.text_input("Question")

if st.button("Ask", disabled=not question):
    with st.spinner("Thinking..."):
        response = requests.post(f"{API_URL}/ask", json={"question": question, "top_k": 4})
        result = response.json()

    st.markdown("#### Answer")
    st.write(result["answer"])

    st.markdown("#### Sources")
    for s in result["sources"]:
        st.write(f"- `{s['file']}`, page {s['page']}")