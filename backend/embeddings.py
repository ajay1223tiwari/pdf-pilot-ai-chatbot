
from sentence_transformers import SentenceTransformer

# Load pre-trained embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def generate_embeddings(chunks):
    """
    Convert text chunks into normalized numerical vectors
    for semantic search and RAG retrieval.
    """

    if not chunks:
        return []

    # Remove empty chunks
    clean_chunks = [
        chunk.strip()
        for chunk in chunks
        if isinstance(chunk, str) and chunk.strip()
    ]

    if not clean_chunks:
        return []

    # Generate embeddings in small batches
    embeddings = model.encode(
        clean_chunks,
        batch_size=16,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings.tolist()
