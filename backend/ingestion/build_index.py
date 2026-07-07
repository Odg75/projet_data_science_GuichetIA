"""
Découpe (chunking) le texte extrait des PDFs sources, le transforme en
embeddings, et l'indexe dans une base vectorielle ChromaDB persistante.

Pipeline : data/pdfs/*.pdf --(extract_pdf)--> Documents
                          --(RecursiveCharacterTextSplitter)--> chunks
                          --(HuggingFaceInferenceAPIEmbeddings)--> vecteurs
                          --(Chroma)--> data/chroma_db/

Les embeddings sont calculés via l'API d'inférence HuggingFace (gratuite) plutôt
qu'en local, pour éviter de charger le modèle (+ torch) en mémoire : ça dépasse
les 512 Mo du plan gratuit Render. Nécessite HUGGINGFACEHUB_API_TOKEN dans .env.

Usage:
    python ingestion/build_index.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings

from extract_pdf import load_documents

load_dotenv()


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
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

# Modèle d'embeddings multilingue, gratuit (HuggingFace / sentence-transformers),
# performant sur le français. Appelé via l'API d'inférence HuggingFace (pas de
# chargement local du modèle).
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def main():
    hf_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token:
        sys.exit(
            "Erreur : HUGGINGFACEHUB_API_TOKEN manquant.\n"
            "Crée un token gratuit sur https://huggingface.co/settings/tokens "
            "et ajoute-le dans backend/.env."
        )

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

    print(f"Connexion à l'API d'embeddings HuggingFace ({EMBEDDING_MODEL})...")
    embeddings = HFInferenceEmbeddings(api_key=hf_token, model_name=EMBEDDING_MODEL)

    print("Indexation dans ChromaDB...")
    if os.path.exists(CHROMA_DIR):
        import shutil
        shutil.rmtree(CHROMA_DIR)

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )
    vectordb.persist()

    print(f"Base vectorielle prête dans {CHROMA_DIR} ({len(chunks)} vecteurs indexés).")


if __name__ == "__main__":
    main()
