"""
Local vector database for RAG, backed by Chroma (persisted to disk) with
sentence-transformers embeddings (all-MiniLM-L6-v2) — everything runs on
your machine, no external API calls.
"""

import uuid

import chromadb
from chromadb.utils import embedding_functions


class VectorStore:
    def __init__(self, persist_dir="data/chroma_db", collection_name="kaggle_rag"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=self.embedder
        )

    def add_documents(self, docs, batch_size=100):
        """docs: list of {"text": str, "source": str, "type": str}"""
        for i in range(0, len(docs), batch_size):
            batch = docs[i : i + batch_size]
            ids = [str(uuid.uuid4()) for _ in batch]
            texts = [d["text"] for d in batch]
            metadatas = [{"source": d["source"], "type": d["type"]} for d in batch]
            self.collection.add(ids=ids, documents=texts, metadatas=metadatas)

    def query(self, question: str, n_results: int = 5):
        count = self.collection.count()
        if count == 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        return self.collection.query(
            query_texts=[question],
            n_results=min(n_results, count),
            include=["documents", "metadatas", "distances"],
        )

    def reset(self):
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name, embedding_function=self.embedder
        )