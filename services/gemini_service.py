import os
import google.generativeai as genai

# Configurează cheia API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-pro")

def ask_gemini(question: str) -> str:
    prompt = f"""
Ești un co-prezentator AI pentru o emisiune TV live. Răspunde pe scurt, prietenos, cu un strop de umor, dar la obiect.

Întrebarea publicului: {question}
Răspuns:
"""
    response = model.generate_content(prompt)
    return response.text.strip()

