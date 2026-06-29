"""
API FastAPI de GuichetIA.

Expose le pipeline RAG (rag.py) sous forme d'endpoints HTTP, consommés par le
frontend React.

Usage (dev local) :
    uvicorn app.main:app --reload --port 8000

Endpoints :
    GET  /health        -> vérifie que l'API, l'index et la clé Groq sont prêts
    POST /ask            -> {"question": "..."} -> {"answer": "...", "sources": [...]}
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import rag

app = FastAPI(
    title="GuichetIA API",
    description="Assistant administratif RAG : CNIB, passeport, création d'entreprise (Burkina Faso)",
    version="1.0.0",
)

# Le frontend (React, servi depuis un autre domaine - Vercel) doit pouvoir
# appeler cette API. En production, restreindre allow_origins au domaine Vercel.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Question de l'utilisateur")


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


@app.on_event("startup")
def startup():
    # Tentative de préchargement (n'échoue pas le démarrage si l'index/la clé
    # ne sont pas encore prêts : /health et /ask renverront alors une erreur claire).
    try:
        rag.load_retriever()
        rag.load_llm()
    except Exception:
        pass


@app.get("/health")
def health():
    retriever_ready = rag.load_retriever() is not None
    llm_ready = rag.load_llm() is not None
    status = "ok" if (retriever_ready and llm_ready) else "degraded"
    return {
        "status": status,
        "index_ready": retriever_ready,
        "llm_ready": llm_ready,
    }


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    try:
        result = rag.answer_question(payload.question)
    except rag.RagNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {exc}")
    return AskResponse(answer=result["answer"], sources=result["sources"])
