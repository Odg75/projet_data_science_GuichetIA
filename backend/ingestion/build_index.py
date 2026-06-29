"""
Découpe (chunking) le texte extrait des PDFs sources, le transforme en
embeddings, et l'indexe dans une base vectorielle ChromaDB persistante.

Pipeline : data/pdfs/*.pdf --(extract_pdf)--> Documents
                          --(RecursiveCharacterTextSplitter)--> chunks
                          --(HuggingFaceEmbeddings)--> vecteurs
                          --(Chroma)--> data/chroma_db/

Usage:
    python ingestion/build_index.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from extract_pdf import load_documents

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

# Modèle d'embeddings multilingue, gratuit (HuggingFace / sentence-transformers),
# performant sur le français.
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def main():
    print("Extraction du texte des PDFs sources...")
    docs = load_documents()
    print(f"{len(docs)} document(s) chargé(s).")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"{len(chunks)} segments (chunks) générés.")

    print(f"Chargement du modèle d'embeddings ({EMBEDDING_MODEL})... "
          f"(premier lancement plus long : le modèle est téléchargé puis mis en cache)")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print("Indexation dans ChromaDB...")
    if os.path.exists(CHROMA_DIR):
        import shutil
        shutil.rmtree(CHROMA_DIR)

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )
    vectordb.persist()

    print(f"Base vectorielle prête dans {CHROMA_DIR} ({len(chunks)} vecteurs indexés).")


if __name__ == "__main__":
    main()
