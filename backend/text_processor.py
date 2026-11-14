
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text(text):
    """
    Split extracted PDF text into meaningful chunks
    for better embedding generation and RAG retrieval.
    """

    if not text or not text.strip():
        return []

    # Clean unnecessary whitespace
    text = text.replace("\x00", " ")
    text = "\r\n".join(
        line.strip() for line in text.splitlines()
    )

    # Improved text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            ". ",
            "? ",
            "! ",
            "; ",
            ", ",
            " ",
            ""
        ],
        is_separator_regex=False
    )

    chunks = text_splitter.split_text(text)

    # Remove empty chunks
    chunks = [
        chunk.strip()
        for chunk in chunks
        if chunk.strip()
    ]

    return chunks
