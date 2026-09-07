"""Turns a stored lease file into plain text for ModelProvider.extract_lease.

This is mechanical text extraction, not agent reasoning — pdfplumber pulls
characters off the page; the agent boundary starts at extract_lease()."""

import io

import pdfplumber
from storage.storage import Storage


def read_document_text(storage: Storage, ref: str) -> str:
    if ref.lower().endswith(".pdf"):
        content = storage.read_bytes(ref)
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    return storage.read_text(ref)
