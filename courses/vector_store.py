# courses/vector_store.py ← remplace le début du fichier

import chromadb
from django.conf import settings
from django.core.cache import cache
import os
import hashlib
import numpy as np

# ─── Lazy loading ─────────────────────────────────────
_embedding_model = None
_chroma_client   = None

# ─── Lazy loading ─────────────────────────────────────
_embedding_model = None
_chroma_client   = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        import os
        from sentence_transformers import SentenceTransformer
        os.environ['TRANSFORMERS_OFFLINE'] = '1'  # ← cache local uniquement
        _embedding_model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2'
        )
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
    """Stocke les chunks et leurs embeddings dans ChromaDB"""
    # Guard : vérifier qu'on a des chunks
    if not chunks:
        raise ValueError(f"Impossible de stocker 0 embeddings pour le cours {course_id}")
    
    collection = get_or_create_collection(course_id)

    texts      = [chunk["content"]          for chunk in chunks]
    ids        = [str(chunk["chunk_index"]) for chunk in chunks]
    metadatas  = [{"page": chunk["page"]}   for chunk in chunks]

    # Encode embeddings
    embeddings = get_embedding_model().encode(texts)

    # Quantize to int8 (4x space reduction, minimal quality loss)
    embeddings_int8 = (embeddings * 127).astype(np.int8)
    embeddings_list = embeddings_int8.tolist()

    collection.add(
        ids        = ids,
        documents  = texts,
        embeddings = embeddings,
        metadatas  = metadatas
    )
    return len(chunks)


def search_similar_chunks(course_id: int, query: str, n_results=5) -> list[str]:
    # Cache key basé sur course_id, query et n_results
    cache_key = f"search:{course_id}:{hashlib.md5(f'{query}:{n_results}'.encode()).hexdigest()}"
    cache_timeout = 3600  # 1 heure

    # Vérifie le cache
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Si pas en cache, fait la recherche
    collection  = get_or_create_collection(course_id)
    query_embed = get_embedding_model().encode([query])

    # Quantize query embedding to match stored format
    query_embed_int8 = (query_embed * 127).astype(np.int8)
    query_embed_list = query_embed_int8.tolist()

    results = collection.query(
        query_embeddings = query_embed_list,
        n_results        = n_results
    )
    documents = results["documents"][0] if results["documents"] else []

    # Met en cache le résultat
    cache.set(cache_key, documents, timeout=cache_timeout)
    return documents


def delete_course_collection(course_id: int):
    try:
        get_chroma_client().delete_collection(f"course_{course_id}")
    except Exception:
        pass