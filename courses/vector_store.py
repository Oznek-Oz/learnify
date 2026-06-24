"""Postgres / pgvector based vector store for course chunks.

This file replaces the previous ChromaDB-backed implementation. It stores
embeddings in the `CourseChunk.embedding` VectorField and performs nearest
neighbour search using the `<->` operator provided by pgvector.

Notes:
- Requires Postgres extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- Requires `django-pgvector` and `pgvector` Python packages.
"""
# courses/vector_store.py
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from .models import CourseChunk
import hashlib

_embedding_model = None


"""def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        import os
        from sentence_transformers import SentenceTransformer
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedding_model"""


from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"

_embedding_model = None

def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        import torch

        torch.set_num_threads(1)

        _embedding_model = SentenceTransformer(MODEL_NAME)

    return _embedding_model

def store_chunks_embeddings(course_id: int, chunks: list[dict]):
    """Compute embeddings for provided chunks and save them on CourseChunk.embedding.

    `chunks` is expected to be a list of dicts with keys: `content`, `chunk_index`, `page`.
    The CourseChunk rows were created earlier in the pipeline and are updated here.
    """
    if not chunks:
        raise ValueError(f"Impossible de stocker 0 embeddings pour le cours {course_id}")

    texts = [c['content'] for c in chunks]
    embeddings = get_embedding_model().encode(texts)

    # Save embeddings to DB: match by course_id + chunk_index
    for chunk, emb in zip(chunks, embeddings):
        CourseChunk.objects.filter(course_id=course_id, chunk_index=chunk['chunk_index']).update(embedding=emb.tolist())

    return len(chunks)


def search_similar_chunks(course_id: int, query: str, n_results=5) -> list[str]:
    """Return list of chunk contents most similar to `query`.

    Results are cached for 1 hour.
    """
    cache_key = f"search:{course_id}:{hashlib.md5(f'{query}:{n_results}'.encode()).hexdigest()}"
    cache_timeout = 3600

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Compute query embedding
    #q_emb = get_embedding_model().encode([query])[0].tolist()
    q_emb = get_embedding_model().encode(
        [f"query: {query}"],
        convert_to_numpy=True,
    )[0].tolist()

    # Use raw SQL to take advantage of pgvector operator
    sql = """
    SELECT content
    FROM courses_coursechunk
    WHERE course_id = %s AND embedding IS NOT NULL
    ORDER BY embedding <-> %s
    LIMIT %s
    """

    with connection.cursor() as cur:
        cur.execute(sql, [course_id, q_emb, n_results])
        rows = cur.fetchall()

    documents = [r[0] for r in rows]
    cache.set(cache_key, documents, timeout=cache_timeout)
    return documents


def delete_course_collection(course_id: int):
    """No-op for pgvector (data stored inline in CourseChunk rows)."""
    # Keep API compatibility with previous implementation
    return