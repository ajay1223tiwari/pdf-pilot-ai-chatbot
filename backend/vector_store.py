
import faiss
import numpy as np
from pathlib import Path


def create_vector_store(embeddings):
    """
    Create a FAISS index and store normalized embeddings.
    """

    if embeddings is None or len(embeddings) == 0:
        raise ValueError("Embeddings cannot be empty")

    vectors = np.asarray(embeddings, dtype=np.float32)

    if vectors.ndim != 2:
        raise ValueError("Embeddings must be a 2D array")

    if vectors.shape[1] == 0:
        raise ValueError("Embedding dimension cannot be zero")

    if not np.isfinite(vectors).all():
        raise ValueError("Embeddings contain invalid values")

    # Create L2-based FAISS index
    dimension = vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)

    # Add vectors to index
    index.add(vectors)

    return index


def search_vectors(index, query_embedding, top_k=3):
    """
    Search for the most similar vectors.
    """

    if index is None:
        raise ValueError("FAISS index cannot be None")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    if index.ntotal == 0:
        return [], []

    query_vector = np.asarray(
        query_embedding,
        dtype=np.float32
    )

    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)

    if query_vector.ndim != 2 or query_vector.shape[0] != 1:
        raise ValueError("Query embedding must contain one vector")

    if query_vector.shape[1] != index.d:
        raise ValueError("Query embedding dimension does not match index")

    if not np.isfinite(query_vector).all():
        raise ValueError("Query embedding contains invalid values")

    k = min(top_k, index.ntotal)

    distances, indices = index.search(query_vector, k)

    # Remove invalid FAISS indices
    results = [
        (float(distance), int(idx))
        for distance, idx in zip(distances[0], indices[0])
        if idx >= 0
    ]

    return (
        [item[0] for item in results],
        [item[1] for item in results]
    )


def save_vector_store(index, file_path):
    """
    Save FAISS index to disk.
    """

    if index is None:
        raise ValueError("FAISS index cannot be None")

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(file_path))


def load_vector_store(file_path):
    """
    Load FAISS index from disk.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Vector store not found: {file_path}"
        )

    index = faiss.read_index(str(file_path))

    return index
