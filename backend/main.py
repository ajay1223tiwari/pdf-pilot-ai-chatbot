import logging
import os
import re
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pypdf import PdfReader

from backend.chat_store import (
    delete_chat_history,
    get_chat_history,
    initialize_database,
    save_message,
)
from backend.embeddings import generate_embeddings
from backend.llm import generate_answer
from backend.metadata_store import load_metadata, save_metadata
from backend.text_processor import split_text
from backend.vector_store import (
    create_vector_store,
    load_vector_store,
    save_vector_store,
    search_vectors,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories
UPLOAD_DIR = Path("uploads")
VECTOR_STORE_DIR = Path("vector_stores")
METADATA_DIR = Path("metadata")

for directory in (UPLOAD_DIR, VECTOR_STORE_DIR, METADATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Normalized embeddings + IndexFlatL2 produce squared L2 distances.
# This is a conservative starting point; tune after testing real PDFs.
RAG_MAX_L2_DISTANCE = float(os.getenv("RAG_MAX_L2_DISTANCE", "2.0"))
MAX_PDF_SIZE = 10 * 1024 * 1024
PDF_ID_PATTERN = re.compile(r"^[a-fA-F0-9]{32}$")

app = FastAPI(
    title="PDF Pilot API",
    description="Upload PDFs and ask grounded questions using AI and RAG.",
    version="1.1.0",
)

initialize_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
         "https://pdf-pilot-ai-chatbot.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    pdf_id: str = Field(pattern=r"^[a-fA-F0-9]{32}$")
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


def validate_pdf_id(pdf_id: str):
    if not PDF_ID_PATTERN.fullmatch(pdf_id):
        raise HTTPException(status_code=400, detail="Invalid PDF ID")


def get_document_resources(pdf_id: str):
    """Return the stored FAISS index and metadata for a PDF."""
    vector_file = VECTOR_STORE_DIR / f"{pdf_id}.faiss"
    metadata_file = METADATA_DIR / f"{pdf_id}.json"

    if not vector_file.is_file() or not metadata_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="PDF not found. Please upload the PDF again.",
        )

    try:
        index = load_vector_store(vector_file)
        metadata = load_metadata(pdf_id)
    except Exception as error:
        logger.exception("Could not load stored PDF resources")
        raise HTTPException(
            status_code=500,
            detail="Could not load the PDF search data. Please re-upload the PDF.",
        ) from error

    chunks = metadata.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise HTTPException(
            status_code=422,
            detail="No searchable text chunks are available for this PDF.",
        )

    if index.ntotal != len(chunks):
        raise HTTPException(
            status_code=500,
            detail="PDF index and metadata are out of sync. Please re-upload the PDF.",
        )

    return index, metadata


def retrieve_chunks(request: SearchRequest):
    """Embed the question and retrieve the closest PDF chunks."""
    index, metadata = get_document_resources(request.pdf_id)

    try:
        query_embeddings = generate_embeddings([request.question])
        if not query_embeddings:
            raise ValueError("Could not generate a query embedding")

        distances, indices = search_vectors(
            index,
            query_embeddings[0],
            request.top_k,
        )
    except Exception as error:
        logger.exception("PDF semantic search failed")
        raise HTTPException(
            status_code=500,
            detail="Could not search this PDF. Please try again.",
        ) from error

    chunks = metadata["chunks"]
    results = []

    for distance, chunk_index in zip(distances, indices):
        if 0 <= chunk_index < len(chunks):
            results.append(
                {
                    "chunk_index": chunk_index,
                    "text": chunks[chunk_index],
                    "distance": float(distance),
                }
            )

    return results


@app.get("/")
def home():
    return {
        "message": "Welcome to PDF Pilot",
        "status": "Running successfully",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "PDF Pilot",
    }


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    content = await file.read()
    await file.close()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must be under 10 MB.",
        )

    try:
        reader = PdfReader(BytesIO(content))

        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Password-protected PDFs are not supported.",
            )

        extracted_pages = []
        for page in reader.pages:
            extracted_pages.append(page.extract_text() or "")

        extracted_text = "\n".join(extracted_pages)

    except HTTPException:
        raise
    except Exception as error:
        logger.exception("PDF extraction failed")
        raise HTTPException(
            status_code=400,
            detail="Invalid or unreadable PDF file.",
        ) from error

    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No extractable text found. The PDF may be scanned or image-only.",
        )

    chunks = split_text(extracted_text)
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="Could not create text chunks from this PDF.",
        )

    pdf_id = uuid4().hex
    pdf_file = UPLOAD_DIR / f"{pdf_id}.pdf"
    vector_file = VECTOR_STORE_DIR / f"{pdf_id}.faiss"
    metadata_file = METADATA_DIR / f"{pdf_id}.json"

    try:
        embeddings = generate_embeddings(chunks)
        if len(embeddings) != len(chunks):
            raise ValueError("Embedding count does not match chunk count")

        index = create_vector_store(embeddings)

        pdf_file.write_bytes(content)
        save_vector_store(index, vector_file)
        save_metadata(chunks, pdf_id, file.filename)

        return {
            "message": "PDF uploaded and processed successfully",
            "pdf_id": pdf_id,
            "filename": file.filename,
            "pages": len(reader.pages),
            "characters_extracted": len(extracted_text),
            "total_chunks": len(chunks),
            "embedding_dimensions": len(embeddings[0]),
            "chunk_previews": chunks[:3],
        }

    except Exception as error:
        logger.exception("PDF processing failed")

        # Remove any files created by this incomplete upload.
        for path in (pdf_file, vector_file, metadata_file):
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                logger.warning("Could not remove incomplete file: %s", path)

        raise HTTPException(
            status_code=500,
            detail="PDF processing failed. Please check the server logs and try again.",
        ) from error


@app.post("/search")
def search_pdf(request: SearchRequest):
    results = retrieve_chunks(request)

    return {
        "message": "Search completed successfully",
        "pdf_id": request.pdf_id,
        "question": request.question,
        "total_results": len(results),
        "results": results,
    }


@app.post("/ask")
def ask_pdf(request: SearchRequest):
    results = retrieve_chunks(request)

    # Filter weak matches before sending context to the language model.
    relevant_results = [
        item
        for item in results
        if item["distance"] <= RAG_MAX_L2_DISTANCE
    ]

    if not relevant_results:
        answer = (
            "I could not find sufficiently relevant information "
            "about this question in the uploaded PDF."
        )
        sources = []
    else:
        context = "\n\n".join(item["text"] for item in relevant_results)

        try:
            answer = generate_answer(request.question, context)
        except RuntimeError as error:
            logger.warning("AI providers unavailable: %s", type(error).__name__)
            raise HTTPException(
                status_code=503,
                detail="AI services are temporarily unavailable. Please try again.",
            ) from error
        except Exception as error:
            logger.exception("Unexpected AI answer generation error")
            raise HTTPException(
                status_code=500,
                detail="Could not generate an answer. Please try again.",
            ) from error

        sources = [
            {
                "chunk_index": item["chunk_index"],
                "text": item["text"],
                "distance": item["distance"],
            }
            for item in relevant_results
        ]

    # Save both messages only after a successful answer path.
    try:
        save_message(request.pdf_id, "user", request.question)
        save_message(request.pdf_id, "assistant", answer)
    except Exception as error:
        logger.exception("Could not save chat history")
        # Keep the answer available even if history storage fails.
        # The response still returns a successful AI answer.

    return {
        "message": "Answer generated successfully",
        "pdf_id": request.pdf_id,
        "question": request.question,
        "answer": answer,
        "sources": sources,
    }


@app.get("/documents/{pdf_id}/file")
def get_pdf_file(pdf_id: str):
    validate_pdf_id(pdf_id)

    pdf_file = UPLOAD_DIR / f"{pdf_id}.pdf"
    if not pdf_file.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found.")

    try:
        metadata = load_metadata(pdf_id)
    except Exception as error:
        logger.exception("Could not load PDF metadata")
        raise HTTPException(
            status_code=500,
            detail="Could not load PDF information.",
        ) from error

    filename = metadata.get("filename") or f"{pdf_id}.pdf"

    return FileResponse(
        path=pdf_file,
        media_type="application/pdf",
        filename=filename,
        content_disposition_type="inline",
    )


@app.get("/chat-history/{pdf_id}")
def chat_history(pdf_id: str):
    validate_pdf_id(pdf_id)

    metadata_file = METADATA_DIR / f"{pdf_id}.json"
    if not metadata_file.is_file():
        raise HTTPException(status_code=404, detail="PDF not found.")

    history = get_chat_history(pdf_id)

    return {
        "pdf_id": pdf_id,
        "total_messages": len(history),
        "messages": history,
    }


@app.get("/documents")
def get_documents():
    documents = []

    for metadata_file in METADATA_DIR.glob("*.json"):
        pdf_id = metadata_file.stem

        if not PDF_ID_PATTERN.fullmatch(pdf_id):
            continue

        try:
            metadata = load_metadata(pdf_id)
            documents.append(
                {
                    "pdf_id": pdf_id,
                    "filename": metadata.get("filename", f"{pdf_id}.pdf"),
                    "total_chunks": metadata.get("total_chunks", 0),
                }
            )
        except Exception:
            logger.warning("Skipping unreadable metadata file: %s", metadata_file)

    return {
        "message": "Documents fetched successfully",
        "total_documents": len(documents),
        "documents": documents,
    }


@app.delete("/documents/{pdf_id}")
def delete_document(pdf_id: str):
    validate_pdf_id(pdf_id)

    pdf_file = UPLOAD_DIR / f"{pdf_id}.pdf"
    vector_file = VECTOR_STORE_DIR / f"{pdf_id}.faiss"
    metadata_file = METADATA_DIR / f"{pdf_id}.json"

    if not metadata_file.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        delete_chat_history(pdf_id)

        for path in (pdf_file, vector_file, metadata_file):
            if path.exists():
                path.unlink()
    except Exception as error:
        logger.exception("Document deletion failed")
        raise HTTPException(
            status_code=500,
            detail="Could not completely delete the document.",
        ) from error

    return {
        "message": "Document deleted successfully",
        "pdf_id": pdf_id,
    }
