"""
UI layer for Assistly: a dark animated theme built around one idea -- make
the RAG pipeline visible. Instead of a spinner, the person sees each stage
(search -> fetch -> index -> retrieve -> generate) light up in order.

Deliberately kept simple/robust: no backdrop-filter (GPU-dependent blur
that can silently render as nothing on some systems with zero console
error), no complex multi-layer animated backgrounds. Just solid colors,
simple gradients, and well-supported CSS.
"""

PIPELINE_STAGES = [
    ("🔍", "Search Kaggle"),
    ("📦", "Fetch dataset"),
    ("🧩", "Index locally"),
    ("🎯", "Retrieve context"),
    ("🧠", "Generate answer"),
]


def inject_css():
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --bg: #0B0F17;
    --surface: #131A26;
    --surface-2: #1A2230;
    --border: #232D3F;
    --border-strong: #303C52;
    --text-primary: #EDF1FA;
    --text-secondary: #8B95AC;
    --text-tertiary: #56607A;
    --accent: #45D9C4;
    --accent-dim: rgba(69, 217, 196, 0.14);
    --accent-strong: #2FBFA9;
    --user-accent: #8AA0F2;
    --gold: #F2B84B;
    --success: #4ADE80;
    --danger: #F0625F;
}

html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; color: var(--text-primary); }
h1, h2, h3 { font-family: 'Space Grotesk', 'Inter', sans-serif; }
code, .krc-mono { font-family: 'IBM Plex Mono', monospace; }

.stApp {
    background-color: var(--bg);
    background-image:
        radial-gradient(circle at 15% 0%, rgba(69,217,196,0.10), transparent 45%),
        radial-gradient(circle at 90% 15%, rgba(138,160,242,0.08), transparent 40%),
        radial-gradient(circle at 40% 100%, rgba(242,184,75,0.06), transparent 40%);
    background-attachment: fixed;
}

section[data-testid="stSidebar"] {
    background-color: var(--surface);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text-primary); }

.block-container {
    max-width: 900px;
    padding-top: 2rem;
}

/* ---------- hero / header ---------- */
.krc-hero { display: flex; align-items: center; gap: 16px; padding: 4px 0; }
.krc-hero-icon {
    width: 54px; height: 54px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center; font-size: 26px;
    background: var(--accent-dim);
    border: 1px solid var(--border-strong);
    flex-shrink: 0;
}
.krc-hero-title {
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 30px; margin: 0;
    color: var(--text-primary);
}
.krc-hero-sub { color: var(--text-secondary); font-size: 14px; margin-top: 3px; }

.krc-trust-row { display: flex; gap: 8px; margin: 14px 0 4px 0; flex-wrap: wrap; }
.krc-badge {
    display: inline-flex; align-items: center; gap: 7px; padding: 6px 12px; border-radius: 999px;
    font-size: 12.5px; font-weight: 500; border: 1px solid var(--border-strong);
    background: var(--surface); color: var(--text-secondary);
}
.krc-badge-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); }
.krc-stat-badge {
    display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px;
    font-size: 12.5px; font-family: 'IBM Plex Mono', monospace;
    background: var(--accent-dim); color: var(--accent); border: 1px solid rgba(69,217,196,0.3);
}

hr.krc-divider { border: none; border-top: 1px solid var(--border); margin: 18px 0; }

/* ---------- empty state ---------- */
.krc-empty { text-align: center; padding: 30px 20px 14px 20px; }
.krc-empty-icon { font-size: 32px; margin-bottom: 8px; }
.krc-empty-title { font-family: 'Space Grotesk', sans-serif; font-size: 18px; font-weight: 600; margin-bottom: 4px; }
.krc-empty-sub { color: var(--text-secondary); font-size: 13.5px; margin-bottom: 16px; }

/* ---------- pipeline rail ---------- */
.krc-pipeline {
    padding: 16px 18px; background: var(--surface);
    border: 1px solid var(--border); border-radius: 12px; margin-bottom: 4px;
}
.krc-progress { height: 3px; width: 100%; background: var(--border); border-radius: 4px; overflow: hidden; margin-bottom: 14px; }
.krc-progress-fill { height: 100%; background: var(--accent); transition: width 0.4s ease; }
.krc-stage-row { display: flex; align-items: center; flex-wrap: wrap; row-gap: 8px; }
.krc-stage { display: flex; align-items: center; gap: 6px; }
.krc-stage-label { font-family: 'IBM Plex Mono', monospace; font-size: 12px; white-space: nowrap; }
.krc-stage-pending .krc-stage-label { color: var(--text-tertiary); }
.krc-stage-active .krc-stage-label { color: var(--gold); font-weight: 600; }
.krc-stage-done .krc-stage-label { color: var(--accent); }
.krc-stage-error .krc-stage-label { color: var(--danger); font-weight: 600; }
.krc-connector { flex: 1; min-width: 12px; height: 1px; background: var(--border-strong); margin: 0 8px; }
.krc-connector-done { background: var(--accent); }
.krc-pipeline-note { font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: var(--text-secondary); padding: 8px 2px 0 2px; }
.krc-pipeline-note-error { color: var(--danger); }

/* ---------- chat messages ---------- */
div[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 4px 6px;
}
div[data-testid="stChatMessage"]:nth-of-type(odd) { border-left: 3px solid var(--user-accent); }
div[data-testid="stChatMessage"]:nth-of-type(even) { border-left: 3px solid var(--accent); }

.krc-sources { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.krc-source-pill {
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; padding: 3px 9px; border-radius: 999px;
    background: var(--accent-dim); color: var(--accent); border: 1px solid rgba(69,217,196,0.25);
}

/* ---------- sidebar ---------- */
.krc-sidebar-title {
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 16px;
    margin-bottom: 4px;
}
.krc-card {
    background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 10px; padding: 10px 12px; margin-top: 8px;
}
.krc-dataset-chip {
    display: flex; align-items: center; gap: 8px; padding: 8px 10px;
    background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px;
    margin-bottom: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 11.5px;
    color: var(--text-secondary);
}
.krc-dataset-chip-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
.krc-empty-note { color: var(--text-tertiary); font-size: 13px; font-style: italic; }
.krc-model-status { display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--text-secondary); }

/* ---------- inputs / buttons ---------- */
div[data-testid="stChatInput"] textarea {
    background: var(--surface) !important; border: 1px solid var(--border-strong) !important;
    color: var(--text-primary) !important; border-radius: 12px !important;
}
.stTextInput input {
    background: var(--surface) !important; border: 1px solid var(--border-strong) !important;
    color: var(--text-primary) !important; border-radius: 8px !important; font-family: 'IBM Plex Mono', monospace !important;
}
.stButton > button {
    background: var(--surface) !important; border: 1px solid var(--border-strong) !important;
    color: var(--text-primary) !important; border-radius: 8px !important;
}
.stButton > button:hover { border-color: var(--accent) !important; color: var(--accent) !important; }
.stSlider [role="slider"] { background: var(--accent) !important; }

@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }

/* === Premium Enhancements === */
@keyframes gradientMove{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.stApp{
background-size:400% 400%!important;
animation:gradientMove 18s ease infinite;
}
.krc-hero-icon{animation:floatY 4s ease-in-out infinite;}
@keyframes floatY{0%{transform:translateY(0)}50%{transform:translateY(-6px)}100%{transform:translateY(0)}}
div[data-testid="stChatMessage"]{
animation:msgIn .45s ease;
transition:.3s;
box-shadow:0 8px 25px rgba(0,0,0,.25);
}
div[data-testid="stChatMessage"]:hover{transform:translateY(-3px)}
@keyframes msgIn{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
.krc-card,.krc-pipeline{
background:rgba(26,34,48,.78)!important;
box-shadow:0 12px 30px rgba(0,0,0,.25);
transition:.3s;
}
.krc-card:hover,.krc-pipeline:hover{transform:translateY(-3px)}
.krc-stage-done{animation:pulseGlow 1.6s infinite}
@keyframes pulseGlow{0%,100%{filter:drop-shadow(0 0 2px #45D9C4)}50%{filter:drop-shadow(0 0 10px #45D9C4)}}
.krc-progress-fill{transition:width .8s cubic-bezier(.17,.84,.44,1)!important}
.krc-source-pill{animation:pop .35s ease}
@keyframes pop{from{opacity:0;transform:scale(.8)}to{opacity:1;transform:scale(1)}}
.stButton>button{
background:linear-gradient(135deg,#45D9C4,#20B8A0)!important;
border:none!important;
}
.stButton>button:hover{
transform:translateY(-2px) scale(1.02);
box-shadow:0 0 20px rgba(69,217,196,.35);
}

</style>
"""


def render_background():
    """
    No-op: background is applied directly via .stApp in inject_css() using
    simple radial-gradient decorations (no backdrop-filter, no complex
    multi-layer animation). Kept as a function so existing app.py calls
    don't need to change.
    """
    return ""


def render_header(dataset_count: int = 0, model: str = "llama3.1"):
    return f"""
<div class="krc-hero">
    <div class="krc-hero-icon">&#129504;</div>
    <div>
        <p class="krc-hero-title">Assistly</p>
        <p class="krc-hero-sub">Ask a question &mdash; it searches Kaggle, indexes real data, and answers with a model running on your machine.</p>
    </div>
</div>
<div class="krc-trust-row">
    <span class="krc-badge"><span class="krc-badge-dot"></span>100% local &middot; nothing leaves this device</span>
    <span class="krc-badge">&#128274; No API keys sent to the cloud</span>
    <span class="krc-stat-badge">&#9889; {model}</span>
    <span class="krc-stat-badge">&#128193; {dataset_count} dataset{'s' if dataset_count != 1 else ''} indexed</span>
</div>
<hr class="krc-divider" />
"""


def render_empty_state():
    return """
<div class="krc-empty">
    <div class="krc-empty-icon">&#10024;</div>
    <p class="krc-empty-title">What do you want to know?</p>
    <p class="krc-empty-sub">Try a topic below, or ask your own &mdash; Assistly will find and index real Kaggle data to answer it.</p>
</div>
"""


def render_pipeline(active_index: int, note: str = "", error: bool = False):
    total = len(PIPELINE_STAGES)
    percent = 100 if active_index >= total else round((active_index / max(total - 1, 1)) * 100)
    parts = []
    for i, (icon, label) in enumerate(PIPELINE_STAGES):
        if error and i == active_index:
            state = "error"
        elif i < active_index:
            state = "done"
        elif i == active_index:
            state = "active"
        else:
            state = "pending"
        parts.append(
            f'<div class="krc-stage krc-stage-{state}">'
            f'<span>{icon}</span>'
            f'<span class="krc-stage-label">{label}</span>'
            f"</div>"
        )
        if i < total - 1:
            conn_state = "done" if i < active_index else ""
            parts.append(f'<div class="krc-connector krc-connector-{conn_state}"></div>')

    note_class = "krc-pipeline-note-error" if error else ""
    note_html = f'<div class="krc-pipeline-note {note_class}">{note}</div>' if note else ""

    return (
        f'<div class="krc-pipeline">'
        f'<div class="krc-progress"><div class="krc-progress-fill" style="width:{percent}%"></div></div>'
        f'<div class="krc-stage-row">{"".join(parts)}</div>'
        f"</div>{note_html}"
    )


def render_sources(sources):
    if not sources:
        return ""
    pills = "".join(f'<span class="krc-source-pill">{s}</span>' for s in sorted(set(sources)))
    return f'<div class="krc-sources">{pills}</div>'


def render_dataset_chip(ref: str):
    return f'<div class="krc-dataset-chip"><span class="krc-dataset-chip-dot"></span>{ref}</div>'


def render_model_status(model: str):
    return (
        f'<div class="krc-card"><div class="krc-model-status">'
        f'<span class="krc-badge-dot"></span><span class="krc-mono">{model}</span>'
        f"&nbsp;running locally via Ollama</div></div>"
    )