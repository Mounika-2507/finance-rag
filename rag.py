import os
from dotenv import load_dotenv
from openai import OpenAI

from ingest import get_collection

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a financial research assistant. Answer using only \
the context provided below, which was retrieved from the company's own \
quarterly results PDFs.

Rules:
- You may summarize, paraphrase, or synthesize what the context says — this \
counts as answering "from the context," not guessing.
- Only refuse if the context truly contains nothing relevant to the question. \
If so, reply exactly: "The information is not available in the uploaded \
documents."
- Cite the file name and page number for every claim, \
e.g. (source: Q2 FY25-26.pdf, page 2).
- Never invent numbers, dates, or facts not present in the context. Quote \
figures exactly as they appear.
"""


def retrieve(question, top_k=5):
    """Find the top_k chunks most relevant to the question (single global search)."""
    collection = get_collection()
    results = collection.query(query_texts=[question], n_results=top_k)

    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": doc, "file": meta["file"], "page": meta["page"]})
    return chunks


def retrieve_across_files(question, per_file_k=3):
    """
    For comparison questions, retrieve the best few chunks from EACH file
    separately, instead of one global top_k search. This guarantees every
    indexed document gets a chance to contribute, rather than one dominant
    file crowding out the rest.
    """
    collection = get_collection()

    all_metadata = collection.get(limit=10000)["metadatas"]
    files = sorted(set(m["file"] for m in all_metadata))

    chunks = []
    for file_name in files:
        results = collection.query(
            query_texts=[question],
            n_results=per_file_k,
            where={"file": file_name},
        )
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            chunks.append({"text": doc, "file": meta["file"], "page": meta["page"]})
    return chunks


def answer_question(question, top_k=5):
    """Retrieve relevant chunks, then ask GPT-4o to answer using only those."""
    chunks = retrieve_across_files(question, per_file_k=3)

    context_parts = []
    for c in chunks:
        context_parts.append(f"[Source: {c['file']}, page {c['page']}]\n{c['text']}")
    context = "\n\n---\n\n".join(context_parts)

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    answer = response.choices[0].message.content

    seen = set()
    sources = []
    for c in chunks:
        key = (c["file"], c["page"])
        if key not in seen:
            seen.add(key)
            sources.append({"file": c["file"], "page": c["page"]})

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    result = answer_question("What did management say about the demand outlook or business environment?")
    print("Answer:", result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  - {s['file']}, page {s['page']}")