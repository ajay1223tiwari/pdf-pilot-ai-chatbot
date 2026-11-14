
import json
from pathlib import Path


METADATA_DIR = Path("metadata")
METADATA_DIR.mkdir(exist_ok=True)


def save_metadata(chunks, pdf_id, filename=None):
    metadata = {
        "pdf_id": pdf_id,
        "filename": filename or f"{pdf_id}.pdf",
        "total_chunks": len(chunks),
        "chunks": chunks
    }

    metadata_file = METADATA_DIR / f"{pdf_id}.json"

    with open(metadata_file, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)

    return metadata_file


def load_metadata(pdf_id):
    metadata_file = METADATA_DIR / f"{pdf_id}.json"

    if not metadata_file.exists():
        raise FileNotFoundError("Metadata file not found")

    with open(metadata_file, "r", encoding="utf-8") as file:
        return json.load(file)
