"""
Logique RAG de GuichetIA : chargement de la base vectorielle, du LLM, et
génération de réponses appuyées sur les sources officielles indexées.

Ce module est utilisé par main.py (API FastAPI) et par evaluation/evaluate.py.
"""

import os

from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq

load_dotenv()

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama-3.1-8b-instant"  # rapide et gratuit via Groq
TOP_K = 4

NO_INFO_MESSAGE = (
    "Je ne dispose pas de cette information dans ma base de connaissances. "
    "Je te recommande de contacter directement la structure compétente."
)

SYSTEM_PROMPT = """Tu es GuichetIA, un assistant administratif pour les citoyens du Burkina Faso.
Réponds UNIQUEMENT à partir du contexte fourni ci-dessous, qui provient de sources officielles
(CNIB, passeport, création d'entreprise).

Règles strictes :
- Si le contexte ne contient pas l'information demandée, réponds explicitement :
  "{no_info}"
- Ne JAMAIS inventer une procédure, un montant, ou un délai qui n'est pas dans le contexte.
- Cite la source (URL) à la fin de ta réponse.
- Réponds en français, de façon claire et concise.

Contexte :
{{context}}
""".format(no_info=NO_INFO_MESSAGE, context="{context}")


class RagNotReadyError(RuntimeError):
    """Levée quand la base vectorielle ou la clé API LLM sont manquantes."""


_retriever = None
_llm = None


def load_retriever():
    """Charge (une seule fois) le retriever ChromaDB. Renvoie None si l'index n'existe pas."""
    global _retriever
    if _retriever is not None:
        return _retriever
    if not os.path.exists(CHROMA_DIR):
        return None
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    _retriever = vectordb.as_retriever(search_kwargs={"k": TOP_K})
    return _retriever


def load_llm():
    """Charge (une seule fois) le client Groq. Renvoie None si la clé API est absente."""
    global _llm
    if _llm is not None:
        return _llm
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    _llm = ChatGroq(model=LLM_MODEL, api_key=api_key, temperature=0.1)
    return _llm


def build_context(docs) -> str:
    parts = []
    for doc in docs:
        source = doc.metadata.get("source_url") or doc.metadata.get("demarche", "source inconnue")
        parts.append(f"[Source: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def answer_question(question: str, retriever=None, llm=None) -> dict:
    """Pose une question au pipeline RAG. Renvoie {"answer": str, "sources": [str]}.

    Lève RagNotReadyError si l'index ou la clé API ne sont pas disponibles.
    """
    retriever = retriever or load_retriever()
    llm = llm or load_llm()

    if retriever is None:
        raise RagNotReadyError(
            "Base vectorielle introuvable. Lance `python ingestion/build_index.py`."
        )
    if llm is None:
        raise RagNotReadyError(
            "Clé GROQ_API_KEY manquante. Copie .env.example en .env et renseigne ta clé."
        )

    docs = retriever.invoke(question)
    if not docs:
        return {"answer": NO_INFO_MESSAGE, "sources": []}

    context = build_context(docs)
    messages = [
        ("system", SYSTEM_PROMPT.format(context=context)),
        ("human", question),
    ]
    response = llm.invoke(messages)
    sources = sorted({doc.metadata.get("demarche", "") for doc in docs})
    return {"answer": response.content, "sources": sources}
