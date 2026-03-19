# test_gemini.py  ← crée ce fichier temporaire à la racine
import google.generativeai as genai
genai.configure(api_key="AIzaSyDS5etLut8ivC1C4AnXqoWOmxUWGcsYFg8")

for model in genai.list_models():
    if "generateContent" in model.supported_generation_methods:
        print(model.name)