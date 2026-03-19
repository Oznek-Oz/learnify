# quiz/gemini_service.py

import google.generativeai as genai
from django.conf import settings
import json
import re
import logging

logger = logging.getLogger(__name__)


def get_gemini_model():
    """Initialise Gemini avec la clé API."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-2.5-flash')


def extract_json(text: str) -> list:
    """
    Extrait le JSON de la réponse Gemini même si elle contient
    des blocs markdown, du texte avant/après, ou des codes imbriqués.
    """
    text = text.strip()

    # Méthode 1 — cherche un tableau JSON directement
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Méthode 2 — nettoie les blocs ```json ... ```
    if '```' in text:
        parts = text.split('```')
        for part in parts:
            part = part.strip()
            if part.startswith('json'):
                part = part[4:].strip()
            if part.startswith('['):
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    pass

    # Méthode 3 — tente le texte brut
    return json.loads(text)


def generate_quiz_from_chunks(
    chunks: list[str],
    topic: str,
    difficulty: str,
    num_questions: int = 5
) -> list[dict]:
    """
    Envoie les chunks + instructions à Gemini.
    Retourne une liste de questions QCM en JSON.
    """

    difficulty_map = {
        'easy':   'facile (questions directes, vocabulaire simple)',
        'medium': 'moyen (compréhension et application des concepts)',
        'hard':   'difficile (analyse, synthèse, cas complexes)'
    }
    difficulty_label = difficulty_map.get(difficulty, 'moyen')

    context = "\n\n---\n\n".join(chunks)

    prompt = f"""
Tu es un professeur expert qui crée des quiz pédagogiques.

Voici des extraits d'un cours sur le sujet : "{topic}"

EXTRAITS DU COURS :
{context}

INSTRUCTIONS :
- Génère exactement {num_questions} questions QCM basées UNIQUEMENT sur ces extraits
- Niveau de difficulté : {difficulty_label}
- Chaque question doit avoir 4 options (A, B, C, D)
- Une seule bonne réponse par question
- Fournis une explication courte pour la bonne réponse
- Les questions doivent être en français

RÈGLES ABSOLUES SUR LA FORMULATION DES QUESTIONS :
- Chaque question doit être AUTONOME et COMPRÉHENSIBLE sans avoir accès au document
- INTERDIT de dire "dans l'exemple ci-dessus", "selon l'extrait", "d'après le code montré",
  "dans l'exemple XQuery présenté", "tel que présenté dans les extraits" ou toute
  référence à un exemple externe non inclus dans la question
- Si la question porte sur un exemple de code ou un extrait, INCLURE
  directement cet exemple dans le texte de la question
- La question doit avoir du sens pour quelqu'un qui n'a PAS le document sous les yeux

EXEMPLE DE MAUVAISE QUESTION (interdit) :
"Étant donné l'exemple XQuery présenté, quelle est la différence..."
→ L'utilisateur ne voit pas l'exemple !

EXEMPLE DE BONNE QUESTION (correct) :
"Considérant que XQuery utilise des clauses FLWOR pour construire
directement des balises XML, et que XSLT utilise des templates pour
transformer des données, quelle est la différence fondamentale ?"
→ La question contient elle-même le contexte nécessaire ✅

IMPORTANT : Réponds UNIQUEMENT avec un JSON valide, sans texte avant ou après.
Format exact :
[
  {{
    "question": "Question autonome et complète ?",
    "option_a": "Première option",
    "option_b": "Deuxième option",
    "option_c": "Troisième option",
    "option_d": "Quatrième option",
    "correct_answer": "A",
    "explanation": "Explication de la bonne réponse"
  }}
]
"""

    try:
        model    = get_gemini_model()
        response = model.generate_content(prompt)
        text     = response.text.strip()

        questions = extract_json(text)  # ← parsing robuste
        logger.info(f"Gemini a généré {len(questions)} questions")
        return questions

    except json.JSONDecodeError as e:
        logger.error(f"Erreur parsing JSON Gemini : {e}")
        logger.error(f"Réponse brute : {response.text}")
        raise ValueError("Gemini n'a pas retourné un JSON valide")

    except Exception as e:
        logger.error(f"Erreur Gemini : {e}")
        raise