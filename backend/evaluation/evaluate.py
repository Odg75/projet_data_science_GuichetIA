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
from app import rag

load_dotenv()

QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), "test_questions.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.json")


def main():
    vdb = rag.load_vectordb()
    llm = rag.load_llm()

    if vdb is None or llm is None:
        print("Index ou clé API manquante. Vérifie data/chroma_db/ et les variables dans .env.")
        return

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    in_scope_total = 0
    retrieval_ok_total = 0
    out_scope_total = 0
    no_hallucination_total = 0

    for item in questions:
        question = item["question"]
        demarche_attendue = item["demarche"]
        in_scope = item["in_scope"]

        print(f"\nQ: {question}")
        result = rag.answer_question(question, llm=llm)
        answer = result["answer"]
        sources = result["sources"]
        scores = result["scores"]
        score_moyen = result["score_moyen"]

        print(f"R: {answer[:120]}...")
        print(f"Sources récupérées : {sources}")
        print(f"Score moyen de pertinence : {score_moyen}%")

        # Évaluation automatique du retrieval (questions in-scope)
        if in_scope:
            in_scope_total += 1
            retrieval_ok = demarche_attendue in sources
            if retrieval_ok:
                retrieval_ok_total += 1
            hallucination = None  # à vérifier manuellement
        else:
            # Hors périmètre : hallucination si le LLM ne répond pas "Je ne sais pas"
            out_scope_total += 1
            retrieval_ok = None
            hallucination = "Je ne dispose pas de cette information" not in answer
          