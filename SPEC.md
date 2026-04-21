# Peer Review Simulator — Specification

## Overview
A Streamlit app that simulates multi-perspective peer review feedback for ML/AI research papers, generating structured scores, comments, and a downloadable PDF report.

## Target Venues
- ICLR, NeurIPS, ICML, EMNLP, ACL, AAAI

## Reviewer Personas
1. **Prolific Reviewer** — High-volume reviewer, broad knowledge, tests paper against many prior works. Tone: Direct, comparative.
2. **Methodology Expert** — Focuses on technical soundness, mathematical rigor, experimental design. Tone: Precise, probing.
3. **Constructive Reviewer** — Balance of praise and critique, aims to help authors improve. Tone: Encouraging but honest.

## Review Dimensions (5)
1. Novelty & Significance
2. Technical Soundness
3. Clarity & Presentation
4. Experiments & Baselines
5. Related Work & Motivation

## Features
- [x] Paste paper text directly
- [x] Upload DOCX or PDF file
- [x] Select target venue (with emphasis/description shown)
- [x] Select reviewer personas (1-3)
- [x] Generate structured reviews with scores (1-10) per dimension
- [x] Synthesize meta-review from all reviewer perspectives
- [x] Export styled PDF report
- [ ] Real-time streaming (future)
- [ ] Batch review of multiple papers (future)

## Architecture
```
app/
  config.py          # Venues, personas, dimensions
  paper_loader.py    # DOCX/PDF/plaintext extraction
  reviewer_engine.py # LLM call + JSON parsing
  meta_review.py     # Meta-review synthesis + score aggregation
  prompts/
    system_prompt.py
    reviewer_prompts.py
    meta_review_prompt.py
  export/
    pdf_export.py    # reportlab PDF generation
  main.py            # Streamlit UI
```

## LLM Backend
- Primary: Anthropic (claude-sonnet-4-20250514)
- Fallback: OpenAI (gpt-4o)
- Auto-detected from environment variables

## PDF Output Sections
1. Cover page (title, venue, date, report ID)
2. Executive summary
3. Dimension score cards (avg across reviewers)
4. Reviewer verdicts row
5. Meta-review synthesis (consensus strengths/weaknesses, final recommendation)
6. Individual review sections (scores table, strengths, weaknesses, questions, suggestions, minor issues)
