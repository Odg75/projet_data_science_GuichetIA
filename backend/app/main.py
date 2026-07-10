"""
API FastAPI de GuichetIA.
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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


@app.get("/health")
def health():
    # Lightweight check: no heavy imports, just verify files and env vars exist.
    # Keeps the port binding instant and the health check always fast.
    vdb_ready = os.path.isdir(rag.CHROMA_DIR)
    llm_ready = bool(os.environ.get("GROQ_API_KEY"))
    status = "ok" if (vdb_ready and llm_ready) else "degraded"
    return {
        "status": status,
        "index_ready": vdb_ready,
        "llm_ready": llm_ready,
    }


@app.get("/pdfs/{demarche}")
def get_pdf(demarche: str):
    """Sert le PDF source officiel d'une demarche administrative."""
    safe = demarche.replace("/", "").replace("..", "").strip()
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs", f"{safe}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF non trouve")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{safe}.pdf")


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
        suggested_questions=result.get("suggested_