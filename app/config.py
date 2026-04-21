"""App configuration: venues, personas, dimension definitions."""

VENUES = {
    "ICLR": {
        "description": "International Conference on Learning Representations",
        "emphasis": (
            "Scientific rigor, reproducibility, clear contribution statement. "
            "Supplementary materials scrutinized. Strong emphasis on contribution clarity."
        ),
        "dimension_weights": {
            "novelty": 0.25,
            "technical": 0.25,
            "clarity": 0.15,
            "experiments": 0.20,
            "related_work": 0.15,
        },
    },
    "NeurIPS": {
        "description": "Conference on Neural Information Processing Systems",
        "emphasis": (
            "Technical depth + broad impact. Known for desk reject if rules violated. "
            "8 pages strict (excluding refs/appendix). Awards-cited papers get attention."
        ),
        "dimension_weights": {
            "novelty": 0.20,
            "technical": 0.25,
            "clarity": 0.15,
            "experiments": 0.25,
            "related_work": 0.15,
        },
    },
    "ICML": {
        "description": "International Conference on Machine Learning",
        "emphasis": (
            "Theoretical grounding, journal-like depth over breadth. "
            "High reproducibility standards. Mathematical rigor valued highly."
        ),
        "dimension_weights": {
            "novelty": 0.25,
            "technical": 0.30,
            "clarity": 0.10,
            "experiments": 0.20,
            "related_work": 0.15,
        },
    },
    "EMNLP": {
        "description": "Empirical Methods in Natural Language Processing",
        "emphasis": (
            "NLP-specific datasets and linguistic analysis. "
            "Strong emphasis on clear writing and motivation. 'Is this an EMNLP paper?' fit matters."
        ),
        "dimension_weights": {
            "novelty": 0.20,
            "technical": 0.20,
            "clarity": 0.20,
            "experiments": 0.20,
            "related_work": 0.20,
        },
    },
    "ACL": {
        "description": "Association for Computational Linguistics",
        "emphasis": (
            "Linguistic insight over benchmark chasing. "
            "Theory papers treated respectfully. Longer related work sections expected."
        ),
        "dimension_weights": {
            "novelty": 0.25,
            "technical": 0.20,
            "clarity": 0.20,
            "experiments": 0.15,
            "related_work": 0.20,
        },
    },
    "AAAI": {
        "description": "Association for the Advancement of Artificial Intelligence",
        "emphasis": (
            "Broad coverage, applied AI welcome. "
            "Robustness and explainability increasingly important. Industry applications valued."
        ),
        "dimension_weights": {
            "novelty": 0.20,
            "technical": 0.20,
            "clarity": 0.15,
            "experiments": 0.25,
            "related_work": 0.20,
        },
    },
}

PERSONAS = {
    "prolific": {
        "name": "Prolific Reviewer",
        "character": (
            "Busy, has seen many papers. Focuses on novelty and significance. "
            "Compares to SOTA fairly but spots overclaimed contributions."
        ),
        "strengths": "Spotlights overclaimed contributions, compares to SOTA fairly",
        "weaknesses": "May miss subtle methodological issues",
        "tone": "direct",
    },
    "methodology": {
        "name": "Methodology Expert",
        "character": (
            "Deep technical reviewer. Focuses on correctness, math, experiments, "
            "statistical rigor, and theoretical foundations."
        ),
        "strengths": "Catches theoretical flaws, statistical issues, missing baselines",
        "weaknesses": "May overlook writing quality and motivation",
        "tone": "technical",
    },
    "constructive": {
        "name": "Constructive Reviewer",
        "character": (
            "Supportive but rigorous. Wants paper to succeed. "
            "Provides actionable suggestions and highlights what's salvageable."
        ),
        "strengths": "Provides actionable suggestions, highlights what's salvageable",
        "weaknesses": "Less likely to recommend reject",
        "tone": "supportive",
    },
    "critical": {
        "name": "Critical Reviewer",
        "character": (
            "High standards, no mercy. Focuses exclusively on weaknesses. "
            "Won't let sloppy work pass. Unambiguous weaknesses list."
        ),
        "strengths": "Unambiguous weaknesses list, won't let sloppy work pass",
        "weaknesses": "Can be overly harsh, may not acknowledge genuine strengths",
        "tone": "harsh",
    },
    "nuanced": {
        "name": "Nuanced Reviewer",
        "character": (
            "Balanced, thoughtful. Weighs tradeoffs carefully. "
            "Acknowledges pros and cons fairly. Considers feasibility and context."
        ),
        "strengths": "Acknowledges pros and cons fairly, considers feasibility",
        "weaknesses": "Less decisive, may hedge too much",
        "tone": "balanced",
    },
}

DIMENSIONS = [
    {
        "key": "novelty",
        "label": "Novelty & Significance",
        "weight": 0.25,
        "prompt_hint": (
            "Is the contribution original? Will it matter? Is it properly positioned "
            "against prior work? Are the claims well-supported?"
        ),
    },
    {
        "key": "technical",
        "label": "Technical Soundness",
        "weight": 0.25,
        "prompt_hint": (
            "Math, methodology, assumptions, proofs, correctness, statistical rigor. "
            "Are the theoretical claims justified?"
        ),
    },
    {
        "key": "clarity",
        "label": "Clarity & Presentation",
        "weight": 0.15,
        "prompt_hint": (
            "Writing, figures, structure, reproducibility, notation consistency. "
            "Can another researcher follow and reproduce the work?"
        ),
    },
    {
        "key": "experiments",
        "label": "Experiments & Baselines",
        "weight": 0.20,
        "prompt_hint": (
            "Baselines fair? Metrics appropriate? Statistical significance? "
            "Hardware-aware evaluation? Ablation studies? Are results reproducible?"
        ),
    },
    {
        "key": "related_work",
        "label": "Related Work & Motivation",
        "weight": 0.15,
        "prompt_hint": (
            "Is the problem well-motivated? Are key references cited? "
            "Gap analysis vs. existing literature? Novelty over prior work?"
        ),
    },
]
