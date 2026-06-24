from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"

print(f"Téléchargement de {MODEL_NAME}...")

SentenceTransformer(MODEL_NAME)

print("Téléchargement terminé.")