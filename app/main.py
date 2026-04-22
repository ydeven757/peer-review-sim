"""Streamlit app for Peer Review Simulator."""
from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from app.llm_client import get_ollama_model_choices
from app.config import VENUES, PERSONAS, DIMENSIONS
from app.paper_loader import load_paper
from app.reviewer_engine import generate_review
from app.meta_review import synthesize_meta_review, compute_average_scores
from app.export.pdf_export import export_pdf

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Peer Review Simulator",
    page_icon="🔍",
    layout="wide",
)

# ── Session state init ──────────────────────────────────────────────
def _init_state():
    defaults = {
        "paper_text": "",
        "venue": "ICLR",
        "selected_personas": ["prolific", "methodology", "constructive"],
        "reviews": None,
        "meta_review": None,
        "avg_scores": None,
        "paper_title": "Research Paper",
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)

_init_state()

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")

    venue = st.selectbox(
        "Target Venue",
        list(VENUES.keys()),
        index=list(VENUES.keys()).index(st.session_state.venue),
    )
    st.session_state.venue = venue
    st.caption(f"_{VENUES[venue]['description']}_")

    st.divider()
    st.subheader("Reviewer Personas")

    selected_personas = st.multiselect(
        "Select reviewers to simulate",
        list(PERSONAS.keys()),
        default=st.session_state.selected_personas,
        format_func=lambda k: PERSONAS[k]["name"],
    )
    st.session_state.selected_personas = selected_personas

    st.divider()
    st.subheader("Dimension Weights")
    for dim in DIMENSIONS:
        st.text(f"• {dim['label']}: {dim['weight']:.0%}")

    st.divider()
    st.subheader("🤖 LLM Configuration")

    # Initialise test result in session state if not present
    st.session_state.setdefault("llm_test_result", None)

    # ── Build env_overrides from current sidebar values ──────────────
    # (widget values below will be read after they render; start with empty)
    _initial_env_overrides: dict = {}

    # ── Active provider badge ────────────────────────────────────────
    provider_label = {
        "ollama": "🐑 Ollama (local)",
        "anthropic": "🤖 Anthropic",
        "openai": "🤖 OpenAI",
    }.get(st.session_state.get("selected_llm_provider", "ollama"), "ollama")
    st.success(f"Active: {provider_label}")

# ── LLM Provider Selection ──────────────────────────────────────
    st.session_state.setdefault("selected_llm_provider", "ollama")

    # Get current index for the radio to maintain state across reruns
    provider_options = ["ollama", "anthropic", "openai"]
    current_index = provider_options.index(st.session_state.get("selected_llm_provider", "ollama"))

    selected_provider = st.radio(
        "Select LLM Provider",
        options=provider_options,
        index=current_index,
        format_func=lambda x: {
            "ollama": "🐑 Ollama (local)",
            "anthropic": "🤖 Anthropic",
            "openai": "🤖 OpenAI",
        }[x],
        horizontal=True,
        help="Choose which LLM to use for generating reviews",
        key="llm_provider_radio",
    )
    st.session_state.selected_llm_provider = selected_provider

    # ── Provider-specific input ─────────────────────────────────────
    env_overrides: dict = {}

    if selected_provider == "ollama":
        from app.llm_client import get_ollama_model_choices
        ollama_choices = get_ollama_model_choices()

        # Get current selection to maintain state
        current_model = st.session_state.get("selected_ollama_model", ollama_choices[0] if ollama_choices else "")
        current_idx = ollama_choices.index(current_model) if current_model in ollama_choices else 0

        selected_ollama_model = st.selectbox(
            "Ollama Model",
            options=ollama_choices,
            index=current_idx,
            key="ollama_model_select",
            help="Models available on your local Ollama server",
        )
        st.session_state.selected_ollama_model = selected_ollama_model
        if selected_ollama_model:
            env_overrides["ollama_model"] = selected_ollama_model

    elif selected_provider == "anthropic":
        anthropic_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Enter your Anthropic API key",
        )
        if anthropic_key:
            env_overrides["anthropic_api_key"] = anthropic_key

    elif selected_provider == "openai":
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Enter your OpenAI API key",
        )
        if openai_key:
            env_overrides["openai_api_key"] = openai_key

    # ── Test connection button ────────────────────────────────────────
    from app.llm_client import test_connection

    col_test, col_clear = st.columns([1, 1])
    with col_test:
        test_btn = st.button(
            "🔗 Test Connection",
            use_container_width=True,
            help="Send a minimal prompt to validate LLM connectivity",
        )
    with col_clear:
        clear_btn = st.button(
            "Clear",
            use_container_width=True,
            help="Clear the test result",
        )

    if clear_btn:
        st.session_state.llm_test_result = None
        st.rerun()

    if test_btn:
        with st.spinner("Testing connection..."):
            result = test_connection(env_overrides)
            st.session_state.llm_test_result = result
        st.rerun()

    # ── Display persisted test result ─────────────────────────────────
    result = st.session_state.get("llm_test_result")
    if result is not None:
        if result.get("ok"):
            latency = result.get("latency_ms", "?")
            model = result.get("model", "?")
            provider = result.get("provider", "?")
            st.success(
                f"✅ Connected — **{provider}** ({model}) — {latency}ms"
            )
        else:
            st.error(f"❌ Connection failed: {result.get('error', 'Unknown error')}")

# ── Main content ────────────────────────────────────────────────────
st.title("🔍 Peer Review Simulator")
st.markdown(
    "Simulate structured peer review feedback for ML/AI research papers — "
    "ICLR, NeurIPS, ICML, EMNLP, ACL, AAAI."
)

# Paper input tabs
tab_paste, tab_upload = st.tabs(["📝 Paste Text", "📄 Upload File"])

paper_text = st.session_state.paper_text

with tab_paste:
    new_text = st.text_area(
        "Paste your paper text here",
        value=paper_text,
        height=400,
        placeholder=(
            "Paste the full paper text, or at minimum: abstract + introduction "
            "+ method + experiments + conclusion..."
        ),
        label_visibility="collapsed",
    )
    if new_text != paper_text:
        st.session_state.paper_text = new_text
        st.session_state.reviews = None  # Reset on new text
        st.session_state.meta_review = None

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a paper",
        type=["pdf", "docx"],
        help="Upload a PDF or Word document",
    )
    if uploaded_file:
        suffix = "." + uploaded_file.name.rsplit(".", 1)[-1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(uploaded_file.getbuffer())
            path = f.name
        fmt = uploaded_file.name.rsplit(".", 1)[-1]
        try:
            extracted = load_paper(path, fmt)
            st.session_state.paper_text = extracted
            st.session_state.reviews = None
            st.session_state.meta_review = None
            st.success(
                f"Loaded **{uploaded_file.name}** — {len(extracted):,} characters extracted."
            )
        except Exception as e:
            st.error(f"Failed to load file: {e}")

paper_text = st.session_state.paper_text
char_count = len(paper_text)
st.caption(f"_{char_count:,} characters loaded_")

# ── Generate button ──────────────────────────────────────────────────
col_btn, col_title = st.columns([1, 3])
with col_btn:
    generate = st.button(
        "🚀 Generate Reviews",
        type="primary",
        use_container_width=True,
        disabled=not paper_text or not st.session_state.selected_personas,
    )
with col_title:
    paper_title = st.text_input(
        "Paper title for the report",
        value=st.session_state.paper_title,
        placeholder="e.g. Responsiveness-Reasoning Tradeoff",
    )
    st.session_state.paper_title = paper_title

if generate and not paper_text:
    st.warning("Please load a paper first.")
    st.stop()

if generate and paper_text and not st.session_state.selected_personas:
    st.warning("Please select at least one reviewer persona.")
    st.stop()

if generate and paper_text and st.session_state.selected_personas:
    # ── Generate reviews ──────────────────────────────────────────
    st.divider()
    st.markdown("## 📋 Generating Reviews...")

    reviews = []
    progress_bar = st.progress(0)
    status = st.empty()

    for i, persona_key in enumerate(st.session_state.selected_personas):
        status.markdown(
            f"Generating **{PERSONAS[persona_key]['name']}** review..."
        )
        try:
            result = generate_review(
                paper_text=paper_text,
                venue=st.session_state.venue,
                venue_info=VENUES[st.session_state.venue],
                persona_key=persona_key,
                persona_info=PERSONAS[persona_key],
                env_overrides=env_overrides,
            )
            reviews.append(result)
        except Exception as e:
            st.error(
                f"Error generating {PERSONAS[persona_key]['name']} review: {e}"
            )
        progress_bar.progress((i + 1) / len(st.session_state.selected_personas))

    progress_bar.empty()
    status.empty()

    if reviews:
        st.session_state.reviews = reviews
        st.session_state.avg_scores = compute_average_scores(reviews)

        # ── Synthesize meta-review ────────────────────────────────
        meta_status = st.empty()
        meta_status.markdown("**Synthesizing meta-review...**")
        try:
            meta = synthesize_meta_review(
                reviews,
                venue=st.session_state.venue,
                paper_title=st.session_state.paper_title,
                env_overrides=env_overrides,
            )
            st.session_state.meta_review = meta
        except Exception as e:
            st.session_state.meta_review = {
                "error": str(e),
                "consensus_strengths": [],
                "consensus_weaknesses": [],
                "final_recommendation": "Error",
                "recommendation_reasoning": f"Meta-review generation failed: {e}",
            }
        meta_status.empty()

        st.success("Reviews generated!")
        st.rerun()

# ── Display results ──────────────────────────────────────────────────
reviews = st.session_state.reviews
meta_review = st.session_state.meta_review
avg_scores = st.session_state.avg_scores

if reviews and avg_scores:
    st.divider()
    st.markdown("## 📊 Review Results")

    DIM_KEYS = ["novelty", "technical", "clarity", "experiments", "related_work"]
    DIM_LABELS = [d["label"] for d in DIMENSIONS]

    # Score cards
    score_cols = st.columns(5)
    for col, key, label in zip(score_cols, DIM_KEYS, DIM_LABELS):
        score = avg_scores.get(key, 0)
        with col:
            st.metric(label, f"{score}/10")

    # Verdict row
    st.markdown("### Reviewer Verdicts")
    vcols = st.columns(len(reviews))
    for col, r in zip(vcols, reviews):
        color_map = {"Accept": "green", "Borderline": "orange", "Reject": "red"}
        color = color_map.get(r.recommendation, "gray")
        with col:
            st.markdown(f"**{r.persona}**")
            st.markdown(f":{color}[**{r.recommendation}**]")
            st.caption(f"Confidence: {r.confidence}/10")

    # ── Meta-review ────────────────────────────────────────────────
    if meta_review and "error" not in meta_review:
        st.markdown("### 🏛️ Meta-Review")

        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.markdown("**Consensus Strengths**")
            for s in meta_review.get("consensus_strengths", []):
                st.markdown(f"• {s}")
        with mcol2:
            st.markdown("**Consensus Weaknesses**")
            for w in meta_review.get("consensus_weaknesses", []):
                st.markdown(f"• {w}")

        rec = meta_review.get("final_recommendation", "?")
        rec_color = "green" if "Accept" in rec else ("orange" if "Borderline" in rec else "red")
        st.markdown(f"**Final Recommendation:** :{rec_color}[**{rec}**]")
        st.markdown(meta_review.get("recommendation_reasoning", ""))
    elif meta_review and "error" in meta_review:
        st.warning(f"Meta-review generation failed: {meta_review['error']}")

    # ── Individual reviews ──────────────────────────────────────────
    st.markdown("### 📄 Individual Reviews")
    for r in reviews:
        with st.expander(
            f"**{r.persona} Review** — {r.recommendation}",
            expanded=False,
        ):
            st.markdown(f"*{r.summary}*")

            # Dimension scores
            scols = st.columns(5)
            for col, key, label in zip(scols, DIM_KEYS, DIM_LABELS):
                sdata = r.scores.get(key, {})
                score_val = sdata.get("score", "?")
                with col:
                    st.caption(label)
                    st.markdown(f"**{score_val}/10**")
                    comment = sdata.get("comment", "")
                    if comment:
                        st.caption(comment[:100] + ("..." if len(comment) > 100 else ""))

            st.divider()

            if r.strengths:
                st.markdown("**Strengths**")
                for s in r.strengths:
                    st.markdown(f"• {s}")

            if r.weaknesses:
                st.markdown("**Weaknesses**")
                for w in r.weaknesses:
                    st.markdown(f"• {w}")

            if r.questions:
                st.markdown("**Questions for Authors**")
                for q in r.questions:
                    st.markdown(f"• {q}")

            if r.suggestions:
                st.markdown("**Suggestions for Improvement**")
                for s in r.suggestions:
                    st.markdown(f"• {s}")

            if r.minor_issues:
                st.markdown(f"*Minor issues: {'; '.join(r.minor_issues)}*")

    # ── PDF Export ──────────────────────────────────────────────────
    if reviews and meta_review:
        st.divider()
        st.markdown("### 📥 Export to PDF")

        export_col1, export_col2 = st.columns([1, 3])
        with export_col1:
            title_for_pdf = st.text_input(
                "Paper title for PDF",
                value=st.session_state.paper_title or "Research Paper",
                key="pdf_title_input",
            )
        with export_col2:
            export_btn = st.button(
                "📥 Generate & Download PDF",
                type="secondary",
                use_container_width=True,
            )

        if export_btn:
            with st.spinner("Generating PDF..."):
                try:
                    output_dir = Path(tempfile.gettempdir())
                    pdf_path = output_dir / "peer_review_report.pdf"

                    export_pdf(
                        output_path=str(pdf_path),
                        paper_title=title_for_pdf or "Research Paper",
                        venue=st.session_state.venue,
                        reviews=reviews,
                        meta_review=meta_review,
                        avg_scores=avg_scores,
                        config={
                            "date": datetime.now().strftime("%B %Y"),
                            "report_id": (
                                f"PR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            ),
                        },
                    )

                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download PDF Report",
                            data=f.read(),
                            file_name=(
                                f"peer_review_"
                                f"{title_for_pdf[:30].replace(' ', '_')}.pdf"
                            ),
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    st.success("PDF generated!")
                except Exception as e:
                    st.error(f"PDF export failed: {e}")