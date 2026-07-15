"""
Orchestrates the full RAG pipeline:
  1. search Kaggle for datasets relevant to the question
  2. download + chunk any new ones
  3. embed & store chunks in the local vector DB
  4. retrieve the most relevant chunks for the question
  5. ask the local Ollama model to answer using that context
"""

from kaggle_client import search_datasets, download_dataset
from document_loader import load_folder_as_documents
from vector_store import VectorStore
from llm_ollama import generate_answer, generate_chitchat_reply

# Common conversational remarks that aren't real data questions — no point
# forcing these through Kaggle search + retrieval, which just drags in
# irrelevant dataset chunks and produces a confused answer.
CHITCHAT_PHRASES = {
    "thanks", "thank you", "thanks a lot", "thank you so much", "thanks so much",
    "ty", "tysm", "ok", "okay", "cool", "got it", "nice", "great", "awesome",
    "perfect", "sounds good", "noted", "alright", "bye", "goodbye", "see you",
    "hi", "hello", "hey", "yo", "sup", "good morning", "good evening", "good night",
    "np", "no problem", "you're welcome", "youre welcome", "cheers",
}


def is_chitchat(message: str) -> bool:
    normalized = message.strip().lower().strip("!.,?")
    return normalized in CHITCHAT_PHRASES


class RAGEngine:
    def __init__(self, model: str = "llama3.1"):
        self.store = VectorStore()
        self.model = model
        self.indexed_datasets = set()

    def build_retrieval_query(self, question: str, history=None) -> str:
        """
        Fold the previous user turn into the retrieval query so follow-ups like
        "tell me the highest one" still retrieve chunks about the actual topic
        (e.g. "Dubai rent prices") instead of searching on those vague words alone.
        """
        if history:
            last_user = next(
                (m["content"] for m in reversed(history) if m["role"] == "user"), None
            )
            if last_user and last_user.strip().lower() != question.strip().lower():
                return f"{last_user} {question}"
        return question

    def has_local_context(self, retrieval_query: str, distance_threshold: float = 1.1) -> bool:
        """
        Check whether we already have a good enough match in the vector store
        for this query, so we can skip firing off a fresh (and possibly
        irrelevant) Kaggle search on every single follow-up question.
        Lower distance = closer match. Threshold is a rough heuristic —
        tune it down if irrelevant old data gets reused too eagerly, or up
        if it re-searches Kaggle too often on obvious follow-ups.
        """
        results = self.store.query(retrieval_query, n_results=1)
        distances = results.get("distances", [[]])
        distances = distances[0] if distances else []
        if not distances:
            return False
        return distances[0] <= distance_threshold

    def find_and_index_datasets(self, query: str, top_k: int = 2, log=print):
        """Search Kaggle, download new datasets, chunk + embed them. Returns the search results."""
        results = search_datasets(query, max_results=top_k)

        for ds in results:
            if ds["ref"] in self.indexed_datasets:
                continue
            log(f"Downloading dataset: {ds['title']} ({ds['ref']})")
            folder = download_dataset(ds["ref"])
            log(f"Chunking files from {ds['ref']}...")
            docs = load_folder_as_documents(folder, ds["ref"])
            if docs:
                self.store.add_documents(docs)
                self.indexed_datasets.add(ds["ref"])
            else:
                log(f"No usable files found in {ds['ref']} (unsupported format?)")

        return results

    def ask(self, question: str, n_context: int = 5, history=None):
        retrieval_query = self.build_retrieval_query(question, history)
        results = self.store.query(retrieval_query, n_results=n_context)
        chunks = results["documents"][0] if results["documents"] else []
        sources = (
            [m["source"] for m in results["metadatas"][0]] if results["metadatas"] else []
        )
        answer = generate_answer(question, chunks, model=self.model, history=history)
        return answer, sources

    def reply_chitchat(self, message: str, history=None):
        """Handle casual remarks without touching Kaggle or the vector store at all."""
        answer = generate_chitchat_reply(message, model=self.model, history=history)
        return answer, []

    def is_chitchat(self, message: str) -> bool:
        return is_chitchat(message)