import fitz
import logging
from pathlib import Path
from config.app_config import COURSE_CHUNK_OVERLAP, COURSE_CHUNK_SIZE

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract non disponible. Les scans ne seront pas supportés.")


def _is_scanned_page(page) -> bool:
    """Détecte si une page est un scan (peu ou pas de texte extractible)."""
    return len(page.get_text().strip()) < 50


def _ocr_page(page) -> str:
    """OCR d'une page via Tesseract."""
    if not TESSERACT_AVAILABLE:
        return ""
    mat = fitz.Matrix(2, 2)  # zoom x2 pour meilleure qualité
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return pytesseract.image_to_string(img, lang="fra+eng")


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Hybride : PyMuPDF pour les pages vectorielles, Tesseract pour les scans.
    """
    doc = fitz.open(file_path)
    pages = []

    for page_num, page in enumerate(doc, start=1):
        if _is_scanned_page(page):
            logger.info(f"Page {page_num} : scan détecté → OCR Tesseract")
            text = _ocr_page(page)
        else:
            text = page.get_text().strip()

        pages.append({"page": page_num, "text": text})

    doc.close()
    return pages


def extract_text_from_image(file_path: str) -> list[dict]:
    """
    OCR sur fichier image (jpg, png, etc.) via Tesseract.
    """
    if not TESSERACT_AVAILABLE:
        logger.error("Tesseract non disponible.")
        return [{"page": 1, "text": ""}]

    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang="fra+eng")
        return [{"page": 1, "text": text.strip()}]
    except Exception as e:
        logger.error(f"Erreur OCR image {file_path}: {e}")
        return [{"page": 1, "text": ""}]


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

    return chunks


def chunk_text_adaptive(pages: list[dict], file_type='pdf') -> list[dict]:
    if file_type == 'pdf':
        return _chunk_pdf_content(pages)
    elif file_type == 'image':
        return _chunk_image_content(pages)
    else:
        return chunk_text(pages)


def _chunk_pdf_content(pages: list[dict]) -> list[dict]:
    chunks = []
    chunk_index = 0

    for page_data in pages:
        paragraphs = [p.strip() for p in page_data["text"].split('\n\n') if p.strip()]

        for para in paragraphs:
            words = para.split()
            if len(words) < 50:
                chunks.append({
                    "chunk_index": chunk_index,
                    "page": page_data["page"],
                    "content": para
                })
                chunk_index += 1
            else:
                for i in range(0, len(words), 250):
                    chunk_words = words[i:i+300]
                    if chunk_words:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "page": page_data["page"],
                            "content": " ".join(chunk_words)
                        })
                        chunk_index += 1

    return chunks


def _chunk_image_content(pages: list[dict]) -> list[dict]:
    chunks = []
    chunk_index = 0

    for page_data in pages:
        words = page_data["text"].split()
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

def extract_text_from_word(file_path: str) -> list[dict]:
    """
    Extrait le texte d'un fichier Word (.docx).
    Chaque paragraphe est regroupé par page simulée (tous les 3000 caractères).
    """
    try:
        from docx import Document
        doc = Document(file_path)
        
        pages = []
        page_num = 1
        current_text = ""

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            current_text += text + "\n\n"

            # Simule une "page" tous les ~3000 caractères
            if len(current_text) >= 3000:
                pages.append({"page": page_num, "text": current_text.strip()})
                page_num += 1
                current_text = ""

        # Dernier bloc
        if current_text.strip():
            pages.append({"page": page_num, "text": current_text.strip()})

        return pages if pages else [{"page": 1, "text": ""}]

    except Exception as e:
        logger.error(f"Erreur lecture Word {file_path}: {e}")
        return [{"page": 1, "text": ""}]