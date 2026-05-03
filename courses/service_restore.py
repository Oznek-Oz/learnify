import fitz  # PyMuPDF uniquement pour l'instant
from config.app_config import COURSE_CHUNK_OVERLAP, COURSE_CHUNK_SIZE


def extract_text_from_pdf(file_path: str) -> list[dict]:
    doc = fitz.open(file_path)
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


def chunk_text(pages: list[dict], chunk_size=COURSE_CHUNK_SIZE, overlap=COURSE_CHUNK_OVERLAP) -> list[dict]:
    chunks = []
    chunk_index = 0
    buffer = []
    current_page = 1

    for page_data in pages:
        words = page_data["text"].split()
        current_page = page_data["page"]
        buffer.extend(words)

        while len(buffer) >= chunk_size:
            chunk_words = buffer[:chunk_size]
            chunks.append({
                "chunk_index": chunk_index,
                "page": current_page,
                "content": " ".join(chunk_words)
            })
            chunk_index += 1
            buffer = buffer[chunk_size - overlap:]

    if buffer:
        chunks.append({
            "chunk_index": chunk_index,
            "page": current_page,
            "content": " ".join(buffer)
        })

def chunk_text_adaptive(pages: list[dict], file_type='pdf') -> list[dict]:
    """
    Chunking adaptatif selon le type de contenu.
    - PDF: chunking par paragraphes avec paramètres optimisés
    - Image: chunks plus petits (contenu OCR souvent dense)
    """
    if file_type == 'pdf':
        return _chunk_pdf_content(pages)
    elif file_type == 'image':
        return _chunk_image_content(pages)
    else:
        # Fallback vers chunking classique
        return chunk_text(pages)


def _chunk_pdf_content(pages: list[dict]) -> list[dict]:
    """
    Chunking optimisé pour PDF: par paragraphes avec chevauchement intelligent.
    """
    chunks = []
    chunk_index = 0

    for page_data in pages:
        # Divise par paragraphes (double saut de ligne)
        paragraphs = [p.strip() for p in page_data["text"].split('\n\n') if p.strip()]

        for para in paragraphs:
            words = para.split()
            if len(words) < 50:  # Paragraphe court, garde entier
                chunks.append({
                    "chunk_index": chunk_index,
                    "page": page_data["page"],
                    "content": para
                })
                chunk_index += 1
            else:
                # Paragraphe long, découpe en chunks de 200-300 mots
                for i in range(0, len(words), 250):  # 250 mots avec overlap
                    chunk_words = words[i:i+300]  # 300 mots max
                    if chunk_words:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "page": page_data["page"],
                            "content": " ".join(chunk_words)
                        })
                        chunk_index += 1

    return chunks


def _chunk_image_content(pages: list[dict]) -> list[dict]:
    """
    Chunking optimisé pour contenu OCR (images): chunks plus petits.
    """
    chunks = []
    chunk_index = 0

    for page_data in pages:
        words = page_data["text"].split()
        # Chunks plus petits pour OCR (150 mots avec overlap de 30)
        chunk_size = 150
        overlap = 30

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i+chunk_size]
            if chunk_words:
                chunks.append({
                    "chunk_index": chunk_index,
                    "page": page_data["page"],
                    "content": " ".join(chunk_words)
                })
                chunk_index += 1

    return chunks
