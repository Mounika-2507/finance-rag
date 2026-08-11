import os
import glob
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()  # reads your .env file so OPENAI_API_KEY becomes available

CHROMA_DIR = "chroma_db"       # folder where the database gets saved to disk
COLLECTION_NAME = "finance_rag"

CHUNK_SIZE = 1100
CHUNK_OVERLAP = 150


def load_pdf_pages(file_path):
    """Read a PDF, return one dict per page with its text + source info."""
    reader = PdfReader(file_path)
    file_name = os.path.basename(file_path)  # just the filename, not the full path
    pages = []
    for i, page in enumerate(reader.pages, start=1):  # start=1 so page numbers match what a human sees
        text = page.extract_text() or ""
        text = text.strip()
        if text:  # skip blank pages
            pages.append({"text": text, "file": file_name, "page": i})
    return pages


def chunk_pages(pages):
    """Split each page's text into overlapping chunks, keeping file/page metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = []
    for page in pages:
        pieces = splitter.split_text(page["text"])
        for piece in pieces:
            chunks.append({"text": piece, "file": page["file"], "page": page["page"]})
    return chunks
def get_collection():
    """Open (or create) our persistent Chroma collection."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)  # "persistent" = saved to disk, survives restarts
    embed_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small",
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )
    return collection

def store_chunks(chunks):
    """Embed every chunk and store it in Chroma."""
    collection = get_collection()

    # Remove any existing chunks from these same files first, so
    # re-indexing the same file doesn't create duplicate entries
    files_in_batch = set(c["file"] for c in chunks)
    for file_name in files_in_batch:
        collection.delete(where={"file": file_name})

    ids = [f"{c['file']}-p{c['page']}-{i}" for i, c in enumerate(chunks)]
    documents = [c["text"] for c in chunks]
    metadatas = [{"file": c["file"], "page": c["page"]} for c in chunks]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Stored {len(chunks)} chunks in ChromaDB.")
    

if __name__ == "__main__":
    pdf_files = glob.glob("data/*.pdf")  # finds every .pdf in the data folder automatically
    print(f"Found {len(pdf_files)} PDF files: {pdf_files}")

    all_chunks = []
    for path in pdf_files:
        pages = load_pdf_pages(path)
        chunks = chunk_pages(pages)
        all_chunks.extend(chunks)
        print(f"  {os.path.basename(path)}: {len(pages)} pages -> {len(chunks)} chunks")


    print(f"\nTotal chunks across all files: {len(all_chunks)}")
    print(all_chunks[0])
    store_chunks(all_chunks)