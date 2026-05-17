# app.py
import streamlit as st
import time
import uuid                                           # ── CHANGE: for thread_id
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchMind · AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ────────────────────────────────────────────────────────
for key, default in [
    ("results", {}), ("running", False), ("done", False),
    ("errors", {}), ("history", []), ("prefill", ""),
    ("dark_mode", True),
    # ── CHANGE: each browser session gets its own memory thread ───────────────
    ("thread_id", str(uuid.uuid4())),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── CHANGE: config dict passed to every agent .invoke() call ─────────────────
#    This scopes memory to the current user session
AGENT_CONFIG = {"configurable": {"thread_id": st.session_state.thread_id}}

# ── Theme variables ───────────────────────────────────────────────────────────
if st.session_state.dark_mode:
    T = {
        "app_bg":         "#0a0a0f",
        "app_grad1":      "rgba(255,140,50,0.12)",
        "app_grad2":      "rgba(255,80,30,0.08)",
        "text_primary":   "#f0ebe0",
        "text_secondary": "#a09890",
        "text_muted":     "#605850",
        "text_mono":      "#a09890",
        "card_bg":        "rgba(255,255,255,0.03)",
        "card_border":    "rgba(255,255,255,0.07)",
        "input_bg":       "rgba(255,255,255,0.05)",
        "input_border":   "rgba(255,140,50,0.25)",
        "input_color":    "#f0ebe0",
        "step_bg":        "rgba(255,255,255,0.03)",
        "step_border":    "rgba(255,255,255,0.07)",
        "result_bg":      "rgba(255,255,255,0.025)",
        "result_border":  "rgba(255,255,255,0.07)",
        "result_color":   "#cdc8bf",
        "report_bg":      "rgba(255,255,255,0.025)",
        "feedback_bg":    "rgba(255,255,255,0.025)",
        "score_bg":       "rgba(255,255,255,0.03)",
        "score_border":   "rgba(255,255,255,0.07)",
        "score_track":    "rgba(255,255,255,0.08)",
        "pill_bg":        "rgba(255,255,255,0.04)",
        "pill_border":    "rgba(255,255,255,0.07)",
        "pill_color":     "#a09890",
        "hist_bg":        "rgba(255,255,255,0.03)",
        "hist_border":    "rgba(255,255,255,0.07)",
        "hist_topic":     "#e8e4dc",
        "hist_time":      "#555",
        "notice_color":   "#605850",
        "desc_color":     "#706860",
        "status_wait":    "#555",
        "error_bg":       "rgba(255,80,80,0.06)",
        "error_border":   "rgba(255,80,80,0.3)",
        "error_color":    "#ff8080",
        "score_slash":    "#555",
        "score_label":    "#555",
        "section_color":  "#f0ebe0",
    }
else:
    T = {
        "app_bg":         "#f5f3ef",
        "app_grad1":      "rgba(255,140,50,0.06)",
        "app_grad2":      "rgba(255,80,30,0.04)",
        "text_primary":   "#1a1612",
        "text_secondary": "#6b5e52",
        "text_muted":     "#9a8878",
        "text_mono":      "#6b5e52",
        "card_bg":        "rgba(255,255,255,0.85)",
        "card_border":    "rgba(0,0,0,0.08)",
        "input_bg":       "#ffffff",
        "input_border":   "rgba(255,140,50,0.4)",
        "input_color":    "#1a1612",
        "step_bg":        "rgba(255,255,255,0.7)",
        "step_border":    "rgba(0,0,0,0.08)",
        "result_bg":      "rgba(255,255,255,0.7)",
        "result_border":  "rgba(0,0,0,0.08)",
        "result_color":   "#4a3f35",
        "report_bg":      "rgba(255,255,255,0.85)",
        "feedback_bg":    "rgba(255,255,255,0.85)",
        "score_bg":       "rgba(255,255,255,0.85)",
        "score_border":   "rgba(0,0,0,0.08)",
        "score_track":    "rgba(0,0,0,0.08)",
        "pill_bg":        "rgba(0,0,0,0.04)",
        "pill_border":    "rgba(0,0,0,0.08)",
        "pill_color":     "#6b5e52",
        "hist_bg":        "rgba(255,255,255,0.7)",
        "hist_border":    "rgba(0,0,0,0.08)",
        "hist_topic":     "#1a1612",
        "hist_time":      "#9a8878",
        "notice_color":   "#9a8878",
        "desc_color":     "#9a8878",
        "status_wait":    "#bbb",
        "error_bg":       "rgba(255,80,80,0.05)",
        "error_border":   "rgba(255,80,80,0.25)",
        "error_color":    "#cc3333",
        "score_slash":    "#aaa",
        "score_label":    "#9a8878",
        "section_color":  "#1a1612",
    }

# ── CSS (unchanged from original) ────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}

.stApp {{
    background: {T["app_bg"]};
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, {T["app_grad1"]} 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, {T["app_grad2"]} 0%, transparent 55%);
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 2rem 3rem 4rem; max-width: 1200px; }}

.hero {{ text-align: center; padding: 3.5rem 0 2.5rem; }}
.hero-eyebrow {{
    font-family: 'DM Mono', monospace; font-size: 0.7rem; font-weight: 500;
    letter-spacing: 0.25em; text-transform: uppercase; color: #ff8c32;
    margin-bottom: 1rem; opacity: 0.9;
}}
.hero h1 {{
    font-family: 'Syne', sans-serif; font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 800; line-height: 1.0; letter-spacing: -0.03em;
    color: {T["text_primary"]}; margin: 0 0 1rem;
}}
.hero h1 span {{ color: #ff8c32; }}
.hero-sub {{
    font-size: 1.05rem; font-weight: 300; color: {T["text_secondary"]};
    max-width: 520px; margin: 0 auto; line-height: 1.65;
}}

.divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,140,50,0.3), transparent);
    margin: 2rem 0;
}}

.input-card {{
    background: {T["card_bg"]}; border: 1px solid rgba(255,140,50,0.15);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 2rem;
    backdrop-filter: blur(8px);
}}

.stTextInput > div > div > input {{
    background: {T["input_bg"]} !important;
    border: 1px solid {T["input_border"]} !important;
    border-radius: 10px !important; color: {T["input_color"]} !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #ff8c32 !important;
    box-shadow: 0 0 0 3px rgba(255,140,50,0.12) !important;
}}
.stTextInput > label {{
    font-family: 'DM Mono', monospace !important; font-size: 0.72rem !important;
    letter-spacing: 0.15em !important; text-transform: uppercase !important;
    color: #ff8c32 !important; font-weight: 500 !important;
}}

.stButton > button {{
    background: linear-gradient(135deg, #ff8c32 0%, #ff5a1a 100%) !important;
    color: #fff !important; font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 0.95rem !important;
    letter-spacing: 0.04em !important; border: none !important;
    border-radius: 10px !important; padding: 0.7rem 2.2rem !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(255,140,50,0.3) !important; width: 100%;
}}
.stButton > button:hover {{
    opacity: 0.92 !important;
    box-shadow: 0 8px 28px rgba(255,140,50,0.4) !important;
}}

.step-card {{
    background: {T["step_bg"]}; border: 1px solid {T["step_border"]};
    border-radius: 14px; padding: 1.5rem 1.8rem; margin-bottom: 1.2rem;
    position: relative; overflow: hidden; transition: border-color 0.3s;
}}
.step-card.active {{ border-color: rgba(255,140,50,0.4); background: rgba(255,140,50,0.04); }}
.step-card.done   {{ border-color: rgba(80,200,120,0.3); background: rgba(80,200,120,0.03); }}
.step-card.error  {{ border-color: rgba(255,80,80,0.4);  background: rgba(255,80,80,0.04); }}
.step-card::before {{
    content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    border-radius: 14px 0 0 14px; background: {T["card_border"]}; transition: background 0.3s;
}}
.step-card.active::before {{ background: #ff8c32; }}
.step-card.done::before   {{ background: #50c878; }}
.step-card.error::before  {{ background: #ff5050; }}

.step-header {{ display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.3rem; }}
.step-num {{ font-family: 'DM Mono', monospace; font-size: 0.68rem; font-weight: 500; letter-spacing: 0.15em; color: #ff8c32; opacity: 0.7; }}
.step-title {{ font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700; color: {T["text_primary"]}; }}
.step-status {{ margin-left: auto; font-family: 'DM Mono', monospace; font-size: 0.68rem; letter-spacing: 0.1em; }}
.status-waiting {{ color: {T["status_wait"]}; }}
.status-running {{ color: #ff8c32; }}
.status-done    {{ color: #50c878; }}
.status-error   {{ color: #ff5050; }}

.result-panel {{
    background: {T["result_bg"]}; border: 1px solid {T["result_border"]};
    border-radius: 14px; padding: 1.8rem 2rem; margin-top: 1rem; margin-bottom: 1.5rem;
}}
.result-panel-title {{
    font-family: 'DM Mono', monospace; font-size: 0.7rem; font-weight: 500;
    letter-spacing: 0.2em; text-transform: uppercase; color: #ff8c32;
    margin-bottom: 1rem; padding-bottom: 0.7rem; border-bottom: 1px solid rgba(255,140,50,0.15);
}}
.result-content {{
    font-size: 0.92rem; line-height: 1.8; color: {T["result_color"]};
    white-space: pre-wrap; font-family: 'DM Sans', sans-serif;
}}

.report-panel {{
    background: {T["report_bg"]}; border: 1px solid rgba(255,140,50,0.2);
    border-radius: 16px; padding: 2rem 2.5rem; margin-top: 1rem;
}}
.feedback-panel {{
    background: {T["feedback_bg"]}; border: 1px solid rgba(80,200,120,0.2);
    border-radius: 16px; padding: 2rem 2.5rem; margin-top: 1rem;
}}
.panel-label {{
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.2em;
    text-transform: uppercase; margin-bottom: 1.2rem; padding-bottom: 0.7rem;
}}
.panel-label.orange {{ color: #ff8c32; border-bottom: 1px solid rgba(255,140,50,0.15); }}
.panel-label.green  {{ color: #50c878; border-bottom: 1px solid rgba(80,200,120,0.15); }}

.score-wrap {{
    display: flex; align-items: center; gap: 1.2rem;
    background: {T["score_bg"]}; border-radius: 12px;
    padding: 1rem 1.5rem; margin-bottom: 1.2rem;
    border: 1px solid {T["score_border"]};
}}
.score-num {{
    font-family: 'Syne', sans-serif; font-size: 2.4rem; font-weight: 800; min-width: 3.5rem; text-align: center;
}}
.score-bar-bg {{ flex: 1; height: 8px; background: {T["score_track"]}; border-radius: 999px; overflow: hidden; }}
.score-bar-fill {{ height: 100%; border-radius: 999px; }}

.stats-strip {{ display: flex; gap: 1.5rem; margin-bottom: 1.2rem; flex-wrap: wrap; }}
.stat-pill {{
    font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.12em;
    color: {T["pill_color"]}; background: {T["pill_bg"]};
    border: 1px solid {T["pill_border"]}; border-radius: 999px; padding: 0.3rem 0.9rem;
}}

.history-item {{
    background: {T["hist_bg"]}; border: 1px solid {T["hist_border"]};
    border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.6rem;
}}
.history-topic {{ font-family: 'DM Sans', sans-serif; font-size: 0.85rem; color: {T["hist_topic"]}; font-weight: 500; }}
.history-time  {{ font-family: 'DM Mono', monospace; font-size: 0.65rem; color: {T["hist_time"]}; margin-top: 0.2rem; letter-spacing: 0.08em; }}

.error-box {{
    background: {T["error_bg"]}; border: 1px solid {T["error_border"]};
    border-radius: 12px; padding: 1rem 1.5rem; margin-top: 1rem;
    font-family: 'DM Mono', monospace; font-size: 0.8rem; color: {T["error_color"]};
}}

.stSpinner > div {{ color: #ff8c32 !important; }}
details summary {{
    font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important;
    color: {T["text_mono"]} !important; letter-spacing: 0.1em !important; cursor: pointer;
}}
.section-heading {{
    font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700;
    color: {T["section_color"]}; margin: 2rem 0 1rem;
}}
.notice {{
    font-family: 'DM Mono', monospace; font-size: 0.72rem; color: {T["notice_color"]};
    text-align: center; margin-top: 3rem; letter-spacing: 0.08em;
}}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def step_card(num, title, state, desc=""):
    status_map = {
        "waiting": ("WAITING",   "status-waiting"),
        "running": ("● RUNNING", "status-running"),
        "done":    ("✓ DONE",    "status-done"),
        "error":   ("✗ ERROR",   "status-error"),
    }
    label, cls = status_map.get(state, ("", ""))
    card_cls = {"running": "active", "done": "done", "error": "error"}.get(state, "")
    st.markdown(f"""
    <div class="step-card {card_cls}">
        <div class="step-header">
            <span class="step-num">{num}</span>
            <span class="step-title">{title}</span>
            <span class="step-status {cls}">{label}</span>
        </div>
        {"<div style='font-size:0.82rem;color:"+T['desc_color']+";margin-top:0.3rem;'>"+desc+"</div>" if desc else ""}
    </div>
    """, unsafe_allow_html=True)


# ── CHANGE: parse_score() removed — critic now returns a typed CriticOutput ──
#    score is accessed as critic_result.score (an int), no regex needed

def score_color(score: int) -> str:
    if score >= 8: return "#50c878"
    if score >= 6: return "#ff8c32"
    return "#ff5050"


def report_stats(text: str) -> dict:
    words = len(text.split())
    return {"words": words, "read_time": max(1, round(words / 200))}


def get_step_state(step, results, running, errors):
    steps = ["search", "reader", "writer", "critic"]
    if step in errors:  return "error"
    if step in results: return "done"
    if running:
        for k in steps:
            if k not in results and k not in errors:
                return "running" if k == step else "waiting"
    return "waiting"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    mode_label = "☀️ Switch to Light Mode" if st.session_state.dark_mode else "🌙 Switch to Dark Mode"
    if st.button(mode_label, use_container_width=True, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown("---")

    st.markdown(f"""
    <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
    color:{T['section_color']};margin-bottom:1rem;">📚 Research History</div>
    """, unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown(f"""
        <div style="font-family:'DM Mono',monospace;font-size:0.72rem;color:{T['hist_time']};
        letter-spacing:0.08em;">No research yet. Run your first query!</div>
        """, unsafe_allow_html=True)
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class="history-item">
                    <div class="history-topic">{item['topic']}</div>
                    <div class="history-time">{item['time']} · {item.get('score','–')}/10</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("↩", key=f"reload_{i}", help="Reload this topic"):
                    st.session_state.prefill = item["topic"]
                    st.rerun()

    st.markdown("---")

    # ── CHANGE: new session reset button clears memory thread ─────────────────
    if st.button("🔄 New Session", use_container_width=True, help="Reset agent memory for a fresh session"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.results = {}
        st.session_state.errors = {}
        st.session_state.done = False
        st.rerun()

    if st.session_state.history and st.button("🗑 Clear History", use_container_width=True):
        st.session_state.history = []
        st.rerun()


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <div class="hero-eyebrow">Multi-Agent AI System</div>
    <h1>Research<span>Mind</span></h1>
    <p class="hero-sub">
        Four specialized AI agents collaborate — searching, scraping, writing,
        and critiquing — to deliver a polished research report on any topic.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ── Layout ────────────────────────────────────────────────────────────────────
col_input, col_spacer, col_pipeline = st.columns([5, 0.5, 4])

with col_input:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    default_val = st.session_state.prefill
    topic = st.text_input(
        "Research Topic",
        value=default_val,
        placeholder="e.g. Quantum computing breakthroughs in 2025",
        key="topic_input",
    )
    if st.session_state.prefill:
        st.session_state.prefill = ""

    run_btn = st.button("⚡  Run Research Pipeline", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-bottom:0.5rem;">
        <span style="font-family:'DM Mono',monospace;font-size:0.68rem;
        color:{T['text_muted']};letter-spacing:0.1em;">TRY AN EXAMPLE →</span>
    </div>
    """, unsafe_allow_html=True)

    examples = ["LLM agents 2025", "CRISPR gene editing", "Fusion energy progress", "Quantum computing 2025"]
    ex_cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        with ex_cols[i]:
            if st.button(ex, key=f"ex_{i}"):
                st.session_state.prefill = ex
                st.rerun()

with col_pipeline:
    st.markdown('<div class="section-heading">Pipeline</div>', unsafe_allow_html=True)
    r = st.session_state.results
    errs = st.session_state.errors
    step_card("01", "Search Agent",  get_step_state("search", r, st.session_state.running, errs), "Gathers recent web information")
    step_card("02", "Reader Agent",  get_step_state("reader", r, st.session_state.running, errs), "Scrapes & extracts deep content")
    step_card("03", "Writer Chain",  get_step_state("writer", r, st.session_state.running, errs), "Drafts the full research report")
    step_card("04", "Critic Chain",  get_step_state("critic", r, st.session_state.running, errs), "Reviews & scores the report")


# ── Trigger pipeline ──────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.results = {}
        st.session_state.errors = {}
        st.session_state.running = True
        st.session_state.done = False
        st.rerun()


# ── Run pipeline ──────────────────────────────────────────────────────────────
if st.session_state.running and not st.session_state.done:
    results = {}
    errors = {}
    topic_val = st.session_state.topic_input

    # ── Step 1: Search agent ──────────────────────────────────────────────────
    with st.spinner("🔍  Search Agent is working…"):
        try:
            search_agent = build_search_agent()
            sr = search_agent.invoke(
                {"messages": [("user", f"Find recent, reliable and detailed information about: {topic_val}")]},
                config=AGENT_CONFIG,              # ── CHANGE: memory config passed here
            )
            results["search"] = sr["messages"][-1].content
        except Exception as e:
            errors["search"] = str(e)
            st.session_state.errors = dict(errors)
        st.session_state.results = dict(results)

    # ── Step 2: Reader agent ──────────────────────────────────────────────────
    if "search" not in errors:
        with st.spinner("📄  Reader Agent is scraping top resources…"):
            try:
                reader_agent = build_reader_agent()
                rr = reader_agent.invoke(
                    {"messages": [("user",
                        f"Based on the following search results about '{topic_val}', "
                        f"pick the most relevant URL and scrape it for deeper content.\n\n"
                        f"Search Results:\n{results['search'][:800]}"
                    )]},
                    config=AGENT_CONFIG,          # ── CHANGE: memory config passed here
                )
                results["reader"] = rr["messages"][-1].content
            except Exception as e:
                errors["reader"] = str(e)
                st.session_state.errors = dict(errors)
            st.session_state.results = dict(results)

    # ── Step 3: Writer chain — CHANGE: streaming output ───────────────────────
    if "search" in results:
        with st.spinner("✍️  Writer is drafting the report…"):
            try:
                research_combined = (
                    f"SEARCH RESULTS:\n{results['search']}\n\n"
                    f"DETAILED SCRAPED CONTENT:\n{results.get('reader', 'Not available')}"
                )
                # ── CHANGE: .stream() instead of .invoke() — text appears live ──
                report_placeholder = st.empty()
                full_report = ""
                for chunk in writer_chain.stream({"topic": topic_val, "research": research_combined}):
                    full_report += chunk
                    report_placeholder.markdown(full_report)   # updates in real time
                report_placeholder.empty()                     # clear preview; final render below
                results["writer"] = full_report
            except Exception as e:
                errors["writer"] = str(e)
                st.session_state.errors = dict(errors)
            st.session_state.results = dict(results)

    # ── Step 4: Critic chain ──────────────────────────────────────────────────
    if "writer" in results:
        with st.spinner("🧐  Critic is reviewing the report…"):
            try:
                # ── CHANGE: critic_chain now returns a CriticOutput object ─────
                critic_result = critic_chain.invoke({"report": results["writer"]})
                results["critic"] = critic_result   # store the object, not a string
            except Exception as e:
                errors["critic"] = str(e)
                st.session_state.errors = dict(errors)
            st.session_state.results = dict(results)

    # ── CHANGE: score comes from critic_result.score (int), not regex ─────────
    score = results["critic"].score if "critic" in results else None

    st.session_state.history.append({
        "topic": topic_val,
        "time": time.strftime("%b %d, %H:%M"),
        "score": score or "–",
        "results": dict(results),
    })

    st.session_state.errors = dict(errors)
    st.session_state.running = False
    st.session_state.done = True
    st.rerun()


# ── Results display ───────────────────────────────────────────────────────────
r = st.session_state.results
errs = st.session_state.errors

if r or errs:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Results</div>', unsafe_allow_html=True)

    for step, err_msg in errs.items():
        st.markdown(f'<div class="error-box">⚠ {step.upper()} AGENT FAILED: {err_msg}</div>', unsafe_allow_html=True)

    if "search" in r:
        with st.expander("🔍 Search Results (raw)", expanded=False):
            st.markdown(f'<div class="result-panel"><div class="result-panel-title">Search Agent Output</div>'
                        f'<div class="result-content">{r["search"]}</div></div>', unsafe_allow_html=True)

    if "reader" in r:
        with st.expander("📄 Scraped Content (raw)", expanded=False):
            st.markdown(f'<div class="result-panel"><div class="result-panel-title">Reader Agent Output</div>'
                        f'<div class="result-content">{r["reader"]}</div></div>', unsafe_allow_html=True)

    if "writer" in r:
        stats = report_stats(r["writer"])
        st.markdown(f"""
        <div class="stats-strip">
            <span class="stat-pill">📄 {stats['words']:,} words</span>
            <span class="stat-pill">⏱ ~{stats['read_time']} min read</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="report-panel">
            <div class="panel-label orange">📝 Final Research Report</div>
        """, unsafe_allow_html=True)
        st.markdown(r["writer"])
        st.markdown("</div>", unsafe_allow_html=True)

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="⬇  Download as Markdown",
                data=r["writer"],
                file_name=f"report_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                label="⬇  Download as TXT",
                data=r["writer"],
                file_name=f"report_{int(time.time())}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    # ── CHANGE: critic display now reads from structured CriticOutput object ──
    if "critic" in r:
        critic = r["critic"]                      # CriticOutput object

        color = score_color(critic.score)
        pct = critic.score * 10
        st.markdown(f"""
        <div class="score-wrap">
            <div class="score-num" style="color:{color}">{critic.score}<span style="font-size:1rem;color:{T['score_slash']}">/10</span></div>
            <div style="flex:1">
                <div style="font-family:'DM Mono',monospace;font-size:0.65rem;
                color:{T['score_label']};letter-spacing:0.1em;margin-bottom:0.4rem;">CRITIC SCORE</div>
                <div class="score-bar-bg">
                    <div class="score-bar-fill" style="width:{pct}%;background:{color};"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="feedback-panel"><div class="panel-label green">🧐 Critic Feedback</div>', unsafe_allow_html=True)

        # ── CHANGE: render structured fields directly instead of raw markdown ─
        st.markdown("**Strengths**")
        for s in critic.strengths:
            st.markdown(f"- {s}")

        st.markdown("**Areas to Improve**")
        for imp in critic.improvements:
            st.markdown(f"- {imp}")

        st.markdown(f"**Verdict:** {critic.verdict}")
        st.markdown("</div>", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="notice">
    ResearchMind · Powered by LangChain multi-agent pipeline · Built with Streamlit
    · {'🌙 Dark' if st.session_state.dark_mode else '☀️ Light'} Mode
    · Session: {st.session_state.thread_id[:8]}…
</div>
""", unsafe_allow_html=True)