# flashcards/gemini_service.py  ← nouveau fichier

import google.generativeai as genai
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)


def generate_flashcards_from_chunks(
    chunks: list[str],
    topic: str,
    num_cards: int = 10
) -> list[dict]:
    """
    Génère des fiches recto/verso à partir des chunks du cours.
    """
    context = "\n\n---\n\n".join(chunks)

    prompt = f"""
Tu es un professeur expert qui crée des fiches de révision pédagogiques.

Voici des extraits d'un cours sur le sujet : "{topic}"

EXTRAITS DU COURS :
{context}

INSTRUCTIONS :
- Génère exactement {num_cards} fiches de révision basées UNIQUEMENT sur ces extraits
- Chaque fiche a un RECTO (concept/question courte) et un VERSO (explication complète)
- Le recto doit être court et précis (une question ou un concept clé)
- Le verso doit être clair et complet (2-4 phrases maximum)
- Ajoute un indice (hint) court et utile pour chaque fiche
- Les fiches doivent couvrir les concepts les plus importants
- Tout en français

IMPORTANT : Réponds UNIQUEMENT avec un JSON valide, sans texte avant ou après.
Format exact :
[
  {{
    "front": "Qu'est-ce que [concept clé] ?",
    "back": "Explication complète et claire du concept en 2-4 phrases.",
    "hint": "Pense à [indice utile]..."
  }}
]
"""

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model    = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text     = response.text.strip()

        # Nettoie les balises markdown si Gemini en ajoute
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        flashcards = json.loads(text)
        logger.info(f"Gemini a généré {len(flashcards)} fiches")
        return flashcards

    except json.JSONDecodeError as e:
        logger.error(f"Erreur parsing JSON Gemini : {e}")
        raise ValueError("Gemini n'a pas retourné un JSON valide")

    except Exception as e:
        logger.error(f"Erreur Gemini flashcards : {e}")
        raise