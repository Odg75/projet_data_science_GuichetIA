"""
Logique RAG de GuichetIA : chargement de la base vectorielle, du LLM, et
generation de reponses appuyees sur les sources officielles indexees.

Ce module est utilise par main.py (API FastAPI) et par evaluation/evaluate.py.
"""

import os
import time

import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_groq import ChatGroq

load_dotenv()

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL = "llama-3.1-8b-instant"
TOP_K = 6

NO_INFO_MESSAGE = (
    "Je ne dispose pas de cette information dans ma base de connaissances. "
    "Je te recommande de contacter directement la structure competente."
)

SYSTEM_PROMPT = (
    "Tu es GuichetIA, un assistant administratif pour les citoyens du Burkina Faso.\n"
    "Reponds UNIQUEMENT a partir du contexte fourni ci-dessous, qui provient de sources officielles\n"
    "(CNIB, passeport, creation d'entreprise, casier judiciaire).\n\n"
    "Regles ABSOLUES - ne jamais enfreindre :\n"
    "- Si le contexte ne contient pas l'information demandee, reponds exactement :\n"
    '  "Je ne dispose pas de cette information dans ma base de connaissances. '
    'Je te recommande de contacter directement la structure competente."\n'
    "- Ne JAMAIS inventer une procedure, un montant ou un delai absent du contexte.\n"
    "- INTERDIT de citer un site web, une URL, un lien ou une adresse internet dans ta reponse,\n"
    "  meme si tu en connais un. L'interface affiche deja les sources automatiquement.\n"
    "- Reponds en francais, de facon claire et concise, sans formule d'introduction inutile.\n\n"
    "Contexte :\n{context}\n"
)


class HFInferenceEmbeddings(Embeddings):
    """Embeddings calcules via l'API d'inference HuggingFace (huggingface_hub),
    sans charger le modele (+ torch) en memoire localement (cf. limite RAM Render)."""

    def __init__(self, api_key: str, model_name: str):
        self._client = InferenceClient(model=model_name, token=api_key)

    def embed_documents(self, texts):
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text):
        return self._embed_one(text)

    def _embed_one(self, text):
        vector = np.asarray(self._client.feature_extraction(text))
        if vector.ndim == 2:
            vector = vector.mean(axis=0)
        return vector.tolist()


class RagNotReadyError(RuntimeError):
    """Levee quand la base vectorielle ou la cle API LLM sont manquantes."""


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
    """Renvoie un retriever LangChain (pour compatibilite avec evaluate.py)."""
    vdb = load_vectordb()
    if vdb is None:
        return None
    return vdb.as_retriever(search_kwargs={"k": TOP_K})


def load_llm():
    """Charge (une seule fois) le client Groq. Renvoie None si la cle API est absente."""
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
        parts.append("[Source: " + source + "]\n" + doc.page_content)
    return "\n\n---\n\n".join(parts)


def answer_question(question: str, llm=None) -> dict:
    """Pose une question au pipeline RAG et renvoie la reponse avec metadonnees."""
    vdb = load_vectordb()
    llm = llm or load_llm()

    if vdb is None:
        raise RagNotReadyError(
            "Base vectorielle indisponible. Verifie que l'index existe "
            "(`python ingestion/build_index.py`) et que HUGGINGFACEHUB_API_TOKEN est defini."
        )
    if llm is None:
        raise RagNotReadyError(
            "Cle GROQ_API_KEY manquante. Copie .env.example en .env et renseigne ta cle."
        )

    t0 = time.time()
    docs_with_scores = vdb.similarity_search_with_score(question, k=TOP_K)
    search_time_ms = round((time.time() - t0) * 1000)

    if not docs_with_scores:
        return {
            "answer": NO_INFO_MESSAGE,
            "sources": [],
            "scores": [],
            "score_moyen": 0.0,
            "chunks": [],
            "search_time_ms": search_time_ms,
            "gen_time_ms": 0,
            "top_k": TOP_K,
            "llm_model": LLM_MODEL,
        }

    docs = [doc for doc, _ in docs_with_scores]
    scores = [round(1 / (1 + float(dist)) * 100, 1) for _, dist in docs_with_scores]
    score_moyen = round(sum(scores) / len(scores), 1)

    chunks = [
        {
            "text": doc.page_content[:300],
            "demarche": doc.metadata.get("demarche", ""),
            "score": scores[i],
        }
        for i, doc in enumerate(docs)
    ]

    context = build_context(docs)
    messages = [
        ("system", SYSTEM_PROMPT.format(context=context)),
        ("human", question),
    ]
    t1 = time.time()
    response = llm.invoke(messages)
    gen_time_ms = round((time.time() - t1) * 1000)

    sources = sorted({doc.metadata.get("demarche", "") for doc in docs})

    return {
        "answer": response.content,
        "sources": sources,
        "scores": scores,
        "score_moyen": score_moyen,
        "chunks": chunks,
        "search_time_ms": search_time_ms,
        "gen_time_ms": gen_time_ms,
        "top_k": TOP_K,
        "llm_model": LLM_MODEL,
    }
