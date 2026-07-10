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
            if not hallucination:
                no_hallucination_total += 1

        results.append({
            "question": question,
            "demarche_attendue": demarche_attendue,
            "in_scope_attendu": in_scope,
            "reponse": answer,
            "sources_recuperees": sources,
            "scores_pertinence": scores,
            "score_moyen": score_moyen,
            "retrieval_pertinent": retrieval_ok,
            "hallucination_detectee": hallucination,
        })

    # Calcul des taux
    taux_retrieval = (retrieval_ok_total / in_scope_total * 100) if in_scope_total else 0
    taux_no_halluc = (no_hallucination_total / out_scope_total * 100) if out_scope_total else 0

    summary = {
        "nb_questions_total": len(results),
        "nb_in_scope": in_scope_total,
        "nb_out_scope": out_scope_total,
        "taux_retrieval_pertinent": f"{taux_retrieval:.0f}%",
        "taux_non_hallucination_hors_perimetre": f"{taux_no_halluc:.0f}%",
        "note": (
            "Le champ 'hallucination_detectee' pour les questions in-scope "
            "est à compléter manuellement après relecture des réponses."
        ),
    }

    output = {"summary": summary, "results": results}

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"  {len(results)} questions évaluées")
    print(f"  Taux de retrieval pertinent    : {taux_retrieval:.0f}%  ({retrieval_ok_total}/{in_scope_total})")
    print(f"  Taux de non-hallucination      : {taux_no_halluc:.0f}%  ({no_hallucination_total}/{out_scope_total})")
    print(f"  Résultats complets             : {RESULTS_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
