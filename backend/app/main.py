"""
API FastAPI de GuichetIA.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import rag

app = FastAPI(
    title="GuichetIA API",
    description="Assistant administratif RAG - Burkina Faso",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


class ChunkInfo(BaseModel):
    text: str
    demarche: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    scores: list[float]
    score_moyen: float
    chunks: list[ChunkInfo] = []
    search_time_ms: int = 0
    gen_time_ms: int = 0
    top_k: int = 6
    llm_model: str = ""
    suggested_questions: list[str] = []


@app.on_event("startup")
def startup():
    try:
        rag.load_vectordb()
        rag.load_llm()
    except Exception:
        pass


@app.get("/health")
def health():
    vdb_ready = rag.load_vectordb() is not None
    llm_ready = rag.load_llm() is not None
    status = "ok" if (vdb_ready and llm_ready) else "degraded"
    return {
        "status": status,
        "index_ready": vdb_ready,
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
    return AskResponse(
        answer=result["answer"],
        sources=result["sources"],
        scores=result["scores"],
        score_moyen=result["score_moyen"],
        chunks=[ChunkInfo(**c) for c in result.get("chunks", [])],
        search_time_ms=result.get("search_time_ms", 0),
        gen_time_ms=result.get("gen_time_ms", 0),
        top_k=result.get("top_k", 6),
        llm_model=result.get("llm_model", ""),
        suggested_questions=result.get("suggested_questions", []),
    )
