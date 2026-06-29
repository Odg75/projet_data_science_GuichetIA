"""
Extrait le texte des PDFs sources (data/pdfs/) avec PyMuPDF.

Chaque PDF correspond à une démarche (cnib.pdf -> demarche="cnib", etc.).
Le texte extrait est renvoyé sous forme de documents LangChain, prêts à être
découpés (chunking) puis indexés par build_index.py.

Usage (test rapide) :
    python ingestion/extract_pdf.py
"""

import os
import glob

import fitz  # PyMuPDF
from langchain_core.documents import Document

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")


def extract_text_from_pdf(filepath: str) -> str:
    """Concatène le texte de toutes les pages d'un PDF."""
    text_parts = []
    with fitz.open(filepath) as pdf:
        for page in pdf:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def load_documents() -> list[Document]:
    """Charge tous les PDFs de data/pdfs/ et renvoie un Document LangChain par PDF.

    Le nom de la démarche (cnib, passeport, creation_entreprise) est déduit du
    nom de fichier (sans extension) et stocké dans doc.metadata["demarche"].
    """
    pattern = os.path.join(PDF_DIR, "*.pdf")
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"Aucun PDF trouvé dans {PDF_DIR}. "
            "Lance d'abord `python data/generate_source_pdfs.py`."
        )

    docs = []
    for filepath in files:
        filename = os.path.basename(filepath)
        demarche = os.path.splitext(filename)[0]

        text = extract_text_from_pdf(filepath)
        if len(text.strip()) < 50:
            print(f"  [ATTENTION] Texte très court extrait de {filename} "
                  f"({len(text)} caractères) - vérifie le PDF.")

        doc = Document(
            page_content=text,
            metadata={"demarche": demarche, "filename": filename},
        )
        docs.append(doc)
        print(f"  OK -> {filename} ({len(text)} caractères extraits, démarche={demarche})")

    return docs


if __name__ == "__main__":
    print(f"Extraction des PDFs depuis {PDF_DIR}...")
    documents = load_documents()
    print(f"\n{len(documents)} document(s) extrait(s).")
