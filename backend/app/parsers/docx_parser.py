import os
from typing import Dict, Any


def extract_text_from_docx(file_path: str) -> Dict[str, Any]:
    """
    Extract text from DOCX documents using python-docx.
    Extracts paragraphs, tables, and headers.
    """
    if not os.path.exists(file_path):
        return {"text": "", "paragraph_count": 0, "error": "File not found"}

    try:
        import docx
        doc = docx.Document(file_path)
        full_text = []

        # 1. Paragraphs
        for para in doc.paragraphs:
            txt = para.text.strip()
            if txt:
                full_text.append(txt)

        # 2. Tables
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    full_text.append(" | ".join(row_cells))

        extracted = "\n".join(full_text).strip()
        if not extracted:
            return {
                "text": "",
                "paragraph_count": len(doc.paragraphs),
                "error": "Document contains no readable text."
            }

        return {
            "text": extracted,
            "paragraph_count": len(doc.paragraphs),
            "extractor": "python-docx",
            "error": None
        }
    except Exception as e:
        return {
            "text": "",
            "paragraph_count": 0,
            "error": f"Failed to parse DOCX: {str(e)}"
        }
