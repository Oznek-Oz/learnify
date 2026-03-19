# courses/services.py

import fitz  # PyMuPDF uniquement pour l'instant

def extract_text_from_pdf(file_path: str) -> list[dict]:
    doc   = fitz.open(file_path)
    pages = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        pages.append({"page": page_num, "text": text if text else ""})

    doc.close()
    return pages


def extract_text_from_image(file_path: str) -> list[dict]:
    """
    EasyOCR temporairement désactivé.
    On l'activera une fois le pipeline de base validé.
    """
    return [{"page": 1, "text": "Traitement image non disponible pour le moment."}]


def chunk_text(pages: list[dict], chunk_size=500, overlap=50) -> list[dict]:
    chunks       = []
    chunk_index  = 0
    buffer       = []
    current_page = 1

    for page_data in pages:
        words        = page_data["text"].split()
        current_page = page_data["page"]
        buffer.extend(words)

        while len(buffer) >= chunk_size:
            chunk_words = buffer[:chunk_size]
            chunks.append({
                "chunk_index": chunk_index,
                "page":        current_page,
                "content":     " ".join(chunk_words)
            })
            chunk_index += 1
            buffer = buffer[chunk_size - overlap:]

    if buffer:
        chunks.append({
            "chunk_index": chunk_index,
            "page":        current_page,
            "content":     " ".join(buffer)
        })

    return chunks