# Peer Review Simulator — SPEC

## Overview
A Streamlit app that simulates structured peer review feedback for ML/AI research papers.

## Features
1. **Paper Input** — paste text, upload .docx, or upload .pdf
2. **Venue Selection** — ICLR, NeurIPS, ICML, EMNLP, ACL, AAAI
3. **Reviewer Personas** — Prolific, Methodology Expert, Constructive, Critical, Nuanced (multi-select)
4. **Review Generation** — LLM-powered structured reviews per persona
5. **Dimension Scores** — 5 dimensions: Novelty, Technical Soundness, Clarity, Experiments, Related Work
6. **Meta-Review** — synthesis of all reviews into consensus
7. **PDF Export** — downloadable review report

## Venues
Each venue has a weight profile for dimension scoring:
- ICLR: scientific rigor, reproducibility, contribution clarity
- NeurIPS: technical depth + broad impact
- ICML: theoretical grounding, depth over breadth
- EMNLP: NLP-specific, clear writing, motivation
- ACL: linguistic insight, theory papers
- AAAI: broad coverage, applied AI, robustness

## Reviewer Personas
| Persona | Character | Tends To |
|---------|-----------|----------|
| Prolific Reviewer | Seen many papers, focused on novelty | Spotlights overclaimed contributions |
| Methodology Expert | Deep technical reviewer | Catches theoretical flaws |
| Constructive Reviewer | Supportive but rigorous | Actionable suggestions |
| Critical Reviewer | High standards, no mercy | Unambiguous weaknesses |
| Nuanced Reviewer | Balanced, weighs tradeoffs | Fair pros/cons |

## Review Dimensions (each 1-10)
1. Novelty & Significance (25%)
2. Technical Soundness (25%)
3. Clarity & Presentation (15%)
4. Experiments & Baselines (20%)
5. Related Work & Motivation (15%)

## Output Format
Each review contains:
- Summary (2-3 sentences)
- Dimension score table with comments
- Strengths (bullet list)
- Weaknesses (bullet list)
- Questions for Authors
- Suggestions for Improvement
- Minor Issues

## Meta-Review
- Consensus strengths
- Consensus weaknesses
- Disputed aspects
- Final recommendation

## Export
PDF with: cover page, executive summary, score cards, verdict row, meta-review, individual reviewer sections.