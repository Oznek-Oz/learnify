# courses/vector_store.py ← remplace le début du fichier

import chromadb
from django.conf import settings
import os

# ─── Lazy loading ─────────────────────────────────────
_embedding_model = None
_chroma_client   = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedding_model

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=os.path.join(settings.BASE_DIR, 'chromadb_data')
        )
    return _chroma_client


def get_or_create_collection(course_id: int):
    return get_chroma_client().get_or_create_collection(
        name=f"course_{course_id}",
        metadata={"hnsw:space": "cosine"}
    )


def store_chunks_embeddings(course_id: int, chunks: list[dict]):
    collection = get_or_create_collection(course_id)

    texts      = [chunk["content"]          for chunk in chunks]
    ids        = [str(chunk["chunk_index"]) for chunk in chunks]
    metadatas  = [{"page": chunk["page"]}   for chunk in chunks]

    embeddings = get_embedding_model().encode(texts).tolist()

    collection.add(
        ids        = ids,
        documents  = texts,
        embeddings = embeddings,
        metadatas  = metadatas
    )
    return len(chunks)


def search_similar_chunks(course_id: int, query: str, n_results=5) -> list[str]:
    collection  = get_or_create_collection(course_id)
    query_embed = get_embedding_model().encode([query]).tolist()

    results = collection.query(
        query_embeddings = query_embed,
        n_results        = n_results
    )
    return results["documents"][0] if results["documents"] else []


def delete_course_collection(course_id: int):
    try:
        get_chroma_client().delete_collection(f"course_{course_id}")
    except Exception:
        pass