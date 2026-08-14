from fastapi import FastAPI
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest import get_collection

app = FastAPI(title="Finance RAG API")


@app.get("/stats")
def stats():
    collection = get_collection()
    return {
        "collection_name": "finance_rag",
        "total_chunks": collection.count(),
        "embedding_model": "text-embedding-3-small",
        "llm_model": "gpt-4o",
    }
from pydantic import BaseModel
from rag import answer_question


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


@app.post("/ask")
def ask(payload: AskRequest):
    result = answer_question(payload.question)
    return result
import tempfile
from fastapi import UploadFile, File
from typing import List
from ingest import ingest_files


@app.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    tmp_dir = tempfile.mkdtemp()
    paths = []
    for f in files:
        path = os.path.join(tmp_dir, f.filename)
        with open(path, "wb") as out:
            out.write(await f.read())
        paths.append(path)

    result = ingest_files(paths)
    return result