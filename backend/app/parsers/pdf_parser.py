import os
from typing import Optional, Dict, Any


def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Extract text and metadata from PDF using PyMuPDF (fitz)
    with a fallback to pypdf.
    """
    if not os.path.exists(file_path):
        return {"text": "", "page_count": 0, "error": "File not found"}

    text_content = []
    page_count = 0

    # 1. Try PyMuPDF (fitz)
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        doc = fitz.open(file_path)
        if doc.is_encrypted:
            return {"text": "", "page_count": 0, "error": "Password-protected PDF document"}

        page_count = len(doc)
        for page in doc:
            t = page.get_text("text")
            if t:
                text_content.append(t)
        doc.close()
        
        extracted = "\n".join(text_content).strip()
        if extracted:
            return {
                "text": extracted,
                "page_count": page_count,
                "extractor": "PyMuPDF",
                "error": None
            }
    except Exception as e:
        # Fall back to pypdf
        pass

    # 2. Fallback to pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        if reader.is_encrypted:
            return {"text": "", "page_count": 0, "error": "Password-protected PDF document"}

        page_count = len(reader.pages)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_content.append(t)
        
        extracted = "\n".join(text_content).strip()
        if not extracted:
            return {
                "text": "",
                "page_count": page_count,
                "error": "Document contains no readable text or is scanned image without OCR."
            }

        return {
            "text": extracted,
            "page_count": page_count,
            "extractor": "pypdf",
            "error": None
        }
    except Exception as e:
        return {
            "text": "",
            "page_count": page_count,
            "error": f"Failed to parse PDF: {str(e)}"
        }
