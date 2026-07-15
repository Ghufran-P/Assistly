"""
Streamlit UI for Assistly, the local Kaggle RAG chatbot.

Run with:
    streamlit run app.py
"""

import streamlit as st

import ui
from rag_engine import RAGEngine

st.set_page_config(page_title="Assistly", page_icon="🧠", layout="wide")
st.markdown(ui.inject_css(), unsafe_allow_html=True)
st.markdown(ui.render_background(), unsafe_allow_html=True)

if "engine" not in st.session_state:
    st.session_state.engine = RAGEngine(model="llama3.1")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "indexed" not in st.session_state:
    st.session_state.indexed = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

st.markdown(
    ui.render_header(dataset_count=len(st.session_state.indexed), model=st.session_state.engine.model),
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<p class="krc-sidebar-title">&#9881;&#65039; Control panel</p>', unsafe_allow_html=True)
    model = st.text_input("Ollama model", value=st.session_state.engine.model)
    st.session_state.engine.model = model
    st.markdown(ui.render_model_status(model), unsafe_allow_html=True)

    top_k = st.slider("Datasets to fetch per question", 1, 5, 2)

    st.markdown("---")
    st.markdown("### Indexed datasets")
    if st.session_state.indexed:
        for ds in st.session_state.indexed:
            st.markdown(ui.render_dataset_chip(ds), unsafe_allow_html=True)
    else:
        st.markdown(
            '<p class="krc-empty-note">Nothing indexed yet &mdash; ask a question to get started.</p>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.button("🗑️ Reset vector database", use_container_width=True):
        st.session_state.engine.store.reset()
        st.session_state.engine.indexed_datasets.clear()
        st.session_state.indexed = []
        st.session_state.chat_history = []
        st.rerun()

# ---------- empty state with example prompts ----------
if not st.session_state.chat_history:
    st.markdown(ui.render_empty_state(), unsafe_allow_html=True)
    examples = [
        "Best laptops for gaming",
        "What factors affect house prices?",
        "Compare EV sales by country",
        "Top rated movies of all time",
    ]
    cols = st.columns(2)
    for i, example in enumerate(examples):
        if cols[i % 2].button(example, use_container_width=True, key=f"example_{i}"):
            st.session_state.pending_question = example
            st.rerun()

# ---------- replay chat history ----------
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🧠"):
        st.write(msg["content"])
        if msg.get("sources"):
            st.markdown(ui.render_sources(msg["sources"]), unsafe_allow_html=True)

# ---------- handle new input (typed or example chip) ----------
typed_question = st.chat_input("Ask a question...")
question = st.session_state.pending_question or typed_question
st.session_state.pending_question = None

if question:
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑"):
        st.write(question)

    with st.chat_message("assistant", avatar="🧠"):
        engine = st.session_state.engine
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chat_history[:-1][-6:]
        ]

        if engine.is_chitchat(question):
            with st.spinner("..."):
                answer, sources = engine.reply_chitchat(question, history=history)
            st.write(answer)
        else:
            pipeline_ph = st.empty()
            pipeline_ph.markdown(ui.render_pipeline(0, "Checking what's already indexed..."), unsafe_allow_html=True)

            retrieval_query = engine.build_retrieval_query(question, history)

            def log(message: str):
                if message.startswith("Downloading"):
                    stage = 1
                elif message.startswith("Chunking"):
                    stage = 2
                else:
                    stage = 0
                pipeline_ph.markdown(ui.render_pipeline(stage, message), unsafe_allow_html=True)

            new_datasets = []
            if engine.has_local_context(retrieval_query):
                pipeline_ph.markdown(
                    ui.render_pipeline(2, "Already have relevant data indexed — skipping a new Kaggle search."),
                    unsafe_allow_html=True,
                )
            else:
                try:
                    new_datasets = engine.find_and_index_datasets(question, top_k=top_k, log=log)
                except Exception as e:
                    pipeline_ph.markdown(
                        ui.render_pipeline(0, f"Kaggle search/download failed: {e}", error=True),
                        unsafe_allow_html=True,
                    )
                    st.caption("Check that ~/.kaggle/kaggle.json (or access_token) is set up correctly.")

            for ds in new_datasets:
                if ds["ref"] not in st.session_state.indexed:
                    st.session_state.indexed.append(ds["ref"])

            pipeline_ph.markdown(ui.render_pipeline(3, "Retrieving the most relevant chunks..."), unsafe_allow_html=True)

            try:
                pipeline_ph.markdown(
                    ui.render_pipeline(4, f"Asking {model} to generate an answer..."), unsafe_allow_html=True
                )
                answer, sources = engine.ask(question, history=history)
                pipeline_ph.empty()
            except Exception as e:
                pipeline_ph.markdown(
                    ui.render_pipeline(4, f"Couldn't reach Ollama: {e}", error=True),
                    unsafe_allow_html=True,
                )
                st.caption(f"Make sure Ollama is running and the model is pulled: `ollama pull {model}`")
                answer, sources = (
                    "I couldn't generate an answer because the local model isn't reachable right now.",
                    [],
                )

            st.write(answer)
            if sources:
                st.markdown(ui.render_sources(sources), unsafe_allow_html=True)

    st.session_state.chat_history.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
    st.rerun()