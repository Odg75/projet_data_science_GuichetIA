"""
Exécute le jeu de questions de test_questions.json à travers le pipeline RAG,
et enregistre les réponses + sources récupérées pour une relecture manuelle.

Sert de base aux deux mesures demandées dans le cahier des charges :
  - pertinence du retrieval (les sources récupérées correspondent-elles à la bonne démarche ?)
  - taux d'hallucination (l'agent dit-il "je ne sais pas" sur les questions hors périmètre ?)

Usage:
    python evaluation/evaluate.py
"""

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from app import rag  # réutilise la logique RAG de l'API (app/rag.py)

load_dotenv()

QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), "test_questions.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.json")


def main():
    retriever = rag.load_retriever()
    llm = rag.load_llm()

    if retriever is None or llm is None:
        print("Index ou clé API manquante. Vérifie data/chroma_db/ et GROQ_API_KEY dans .env.")
        return

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    for item in questions:
        question = item["question"]
        print(f"\nQ: {question}")
        result = rag.answer_question(question, retriever, llm)
        answer, sources = result["answer"], result["sources"]
        print(f"R: {answer}")
        print(f"Sources: {sources}")

        results.append({
            "question": question,
            "demarche_attendue": item["demarche"],
            "in_scope_attendu": item["in_scope"],
            "reponse": answer,
            "sources_recuperees": sources,
            # A compléter manuellement après relecture :
            "retrieval_pertinent": None,   # true / false
            "hallucination_detectee": None,  # true / false
        })

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{len(results)} questions évaluées. Résultats enregistrés dans {RESULTS_PATH}.")
    print("Complète manuellement les champs 'retrieval_pertinent' et 'hallucination_detectee' "
          "pour chaque question avant de les reporter dans le rapport technique.")


if __name__ == "__main__":
    main()
