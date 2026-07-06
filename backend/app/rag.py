"""
Logique RAG de GuichetIA : chargement de la base vectorielle, du LLM, et
génération de réponses appuyées sur les sources officielles indexées.

Ce module est utilisé par main.py (API FastAPI) et par evaluation/evaluate.py.
"""

import os

import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_groq import ChatGroq

load_dotenv()

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama-3.1-8b-instant"  # rapide et gratuit via Groq
TOP_K = 6

NO_INFO_MESSAGE = (
    "Je ne dispose pas de cette information dans ma base de connaissances. "
    "Je te recommande de contacter directement la structure compétente."
)

SYSTEM_PROMPT = """Tu es GuichetIA, un assistant administratif pour les citoyens du Burkina Faso.
Réponds UNIQUEMENT à partir du contexte fourni ci-dessous, qui provient de sources officielles
(CNIB, passeport, création d'entreprise, casier judiciaire).

Règles ABSOLUES — ne jamais enfreindre :
- Si le contexte ne contient pas l'information demandée, réponds exactement :
  "{no_info}"
- Ne JAMAIS inventer une procédure, un montant ou un délai absent du contexte.
- INTERDIT de citer un site web, une URL, un lien ou une adresse internet dans ta réponse,
  même si tu en connais un. L'interface affiche déjà les sources automatiquement.
- Réponds en français, de façon claire et concise, sans formule d'introduction inutile.

Contexte :
{{context}}
""".format(no_info=NO_INFO_MESSAGE, context="{context}")


class HFInferenceEmbeddings(Embeddings):
    """Embeddings calculés via l'API d'inférence HuggingFace (huggingface_hub),
    sans charger le modèle (+ torch) en mémoire localement (cf. limite RAM Render)."""

    def __init__(self, api_key: str, model_name: str):
        self._client = InferenceClient(model=model_name, token=api_key)

    def embed_documents(self, texts):
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text):
        return self._embed_one(text)

    def _embed_one(self, text):
        vector = np.asarray(self._client.feature_extraction(text))
        if vector.ndim == 2:  # certains modèles renvoient les embeddings par token
            vector = vector.mean(axis=0)
        return vector.tolist()


class RagNotReadyError(RuntimeError):
    """Levée quand la base vectorielle ou la clé API LLM sont manquantes."""


_vectordb = None
_llm = None


def load_vectordb():
    """Charge (une seule fois) la base vectorielle ChromaDB.
    Renvoie None si l'index n'existe pas ou si le token HF est absent."""
    global _vectordb
    if _vectordb is not None:
        return _vectordb
    if not os.path.exists(CHROMA_DIR):
        return None
    hf_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token:
        return None
    embeddings = HFInferenceEmbeddings(api_key=hf_token, model_name=EMBEDDING_MODEL)
    _vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    return _vectordb


def load_retriever():
    """Renvoie un retriever LangChain (pour compatibilité avec evaluate.py)."""
    vdb = load_vectordb()
    if vdb is None:
        return None
    return vdb.as_retriever(search_kwargs={"k": TOP_K})


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


def answer_question(question: str, llm=None) -> dict:
    """Pose une question au pipeline RAG.

    Renvoie :
        {
          "answer": str,
          "sources": [str],          # noms des démarches trouvées
          "scores": [float],         # scores de pertinence 0-100 (un par chunk récupéré)
          "score_moyen": float,      # moyenne des scores de pertinence
        }

    Les scores sont calculés à partir de la distance L2 ChromaDB convertie en
    similarité : score = 1 / (1 + distance_L2) * 100.
    Un score proche de 100 signifie que le chunk est très proche sémantiquement
    de la question. Un score bas indique une faible pertinence.

    Lève RagNotReadyError si l'index ou la clé API ne sont pas disponibles.
    """
    vdb = load_vectordb()
    llm = llm or load_llm()

    if vdb is None:
        raise RagNotReadyError(
            "Base vectorielle indisponible. Vérifie que l'index existe "
            "(`python ingestion/build_index.py`) et que HUGGINGFACEHUB_API_TOKEN est défini."
        )
    if llm is None:
        raise RagNotReadyError(
            "Clé GROQ_API_KEY manquante. Copie .env.example en .env et renseigne ta clé."
        )

    # Recherche avec scores de distance L2
    docs_with_scores = vdb.similarity_search_with_score(question, k=TOP_K)

    if not docs_with_scores:
        return {"answer": NO_INFO_MESSAGE, "sources": [], "scores": [], "score_moyen": 0.0}

    docs = [doc for doc, _ in docs_with_scores]
    # Conversion distance L2 → score de similarité (0-100)
    scores = [round(1 / (1 + float(dist)) * 100, 1) for _, dist in docs_with_scores]
    score_moyen = round(sum(scores) / len(scores), 1)

    context = build_context(docs)
    messages = [
        ("system", SYSTEM_PROMPT.format(context=context)),
        ("human", question),
    ]
    response = llm.invoke(messages)
    sources = sorted({doc.metadata.get("demarche", "") for doc in docs})

    return {
        "answer": response.content,
        "sources": sources,
        "scores": scores,
        "score_moyen": score_moyen,
    }
