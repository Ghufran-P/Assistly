"""
Talks to a locally running Ollama server to generate answers grounded in
retrieved context. Requires Ollama installed and running (`ollama serve`,
usually started automatically) with a model pulled, e.g.:
    ollama pull llama3.1
"""

import ollama

SYSTEM_PROMPT = (
    "You are a helpful assistant paired with a local database of Kaggle "
    "datasets. You will be given some retrieved context alongside the "
    "user's question.\n\n"
    "- If the context is relevant to the question (e.g. it's a lookup, "
    "comparison, or analysis question about the data), answer using that "
    "context and mention which file the information came from.\n"
    "- If the question is a general knowledge question, definition, or "
    "explanation of a term (e.g. 'what is DDR5 RAM?'), and the context "
    "doesn't actually help answer it, ignore the context and just answer "
    "normally using your own knowledge — don't force an answer out of "
    "irrelevant data, and don't say you lack information you actually have.\n"
    "- If a question genuinely needs data you don't have in the context, "
    "say so clearly instead of guessing."
)

CHITCHAT_SYSTEM_PROMPT = (
    "You are a friendly, concise assistant for a local data-analysis chatbot. "
    "The user just sent a casual conversational remark (like a greeting or "
    "thanks), not a question about data. Reply naturally and briefly — do "
    "not mention datasets, context, or files, since none are relevant here."
)


def generate_answer(question: str, context_chunks, model: str = "llama3.1", history=None):
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else "(no relevant context found)"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }
    )

    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]


def generate_chitchat_reply(message: str, model: str = "llama3.1", history=None):
    """For casual remarks (thanks, hi, ok, etc.) that don't need any dataset context."""
    messages = [{"role": "system", "content": CHITCHAT_SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]