import chromadb
from chromadb.utils import embedding_functions

# Local, on-disk vector database (persists between restarts)
_client = chromadb.PersistentClient(path="data/chroma")

# Free local embedding model - turns text into vectors, no API key needed
_embed = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def get_collection():
    return _client.get_or_create_collection(name="documents", embedding_function=_embed)

def add_chunks(doc_id: str, filename: str, chunks: list[str]):
    """Store chunks. Chroma runs each chunk through the embedding model and
    saves (vector, text, metadata) to disk automatically."""
    col = get_collection()
    col.add(
        ids=[f"{doc_id}::{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[
            {"doc_id":doc_id, "filename":filename, "chunk_index":i}
            for i in range(len(chunks))
        ],
    )

def count() -> int:
    return get_collection().count()