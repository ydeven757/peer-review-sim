"""Generate a styled PDF review report using reportlab."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Color palette ────────────────────────────────────────────────────
NAVY = HexColor("#1a1a2e")
BLUE = HexColor("#4361ee")
GREEN = HexColor("#16a34a")
RED = HexColor("#dc2626")
ORANGE = HexColor("#d97706")
GRAY = HexColor("#64748b")
LIGHT_BG = HexColor("#f8f9fc")
BORDER = HexColor("#e2e8f0")
LIGHT_GREEN_BG = HexColor("#f0fdf4")
LIGHT_RED_BG = HexColor("#fef2f2")
STRENGTH_BORDER = HexColor("#bbf7d0")
WEAKNESS_BORDER = HexColor("#fecaca")


def _score_color(score: float) -> HexColor:
    if score >= 7:
        return GREEN
    if score >= 5:
        return ORANGE
    return RED


def _build_styles():
    styles = getSampleStyleSheet()
    s = styles["Normal"]

    styles.add(ParagraphStyle("CoverBadge", parent=s,
        fontSize=8, leading=10, textColor=HexColor("#a8d8ff"),
        fontName="Helvetica", spaceAfter=6))
    styles.add(ParagraphStyle("CoverTitle", parent=s,
        fontSize=22, leading=28, textColor=white,
        fontName="Helvetica-Bold", spaceAfter=8))
    styles.add(ParagraphStyle("CoverSub", parent=s,
        fontSize=10, leading=14, textColor=HexColor("#a8d8ff"),
        fontName="Helvetica"))
    styles.add(ParagraphStyle("SectionTitle", parent=s,
        fontSize=13, leading=18, textColor=NAVY,
        fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle("TableHeader", parent=s,
        fontSize=8, leading=10, textColor=white,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("Body", parent=s,
        fontSize=10, leading=14, textColor=HexColor("#374151")))
    styles.add(ParagraphStyle("BulletItem", parent=s,
        fontSize=10, leading=14, textColor=HexColor("#374151"),
        leftIndent=8))
    styles.add(ParagraphStyle("SubHeader", parent=s,
        fontSize=8, leading=10, textColor=GRAY,
        fontName="Helvetica", spaceAfter=2))
    styles.add(ParagraphStyle("DimLabel", parent=s,
        fontSize=9, leading=12, textColor=GRAY,
        fontName="Helvetica"))
    styles.add(ParagraphStyle("ScoreNum", parent=s,
        fontSize=18, leading=22, textColor=NAVY,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("MetaKey", parent=s,
        fontSize=8, leading=10, textColor=GRAY,
        fontName="Helvetica"))
    styles.add(ParagraphStyle("MetaVal", parent=s,
        fontSize=10, leading=14, textColor=HexColor("#a8d8ff"),
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("ReviewerName", parent=s,
        fontSize=11, leading=14, textColor=NAVY,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("Footer", parent=s,
        fontSize=8, leading=10, textColor=GRAY,
        alignment=TA_CENTER))
    return styles


# ── Helper builders ─────────────────────────────────────────────────

def _build_cover(paper_title: str, venue: str, config: dict, S) -> list:
    """Build the cover page elements."""
    elems = []

    # Title block
    title_data = [[Paragraph("PEER REVIEW SIMULATION REPORT", S["CoverBadge"])]]
    t = Table(title_data, colWidths=[17 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 24),
        ("RIGHTPADDING", (0, 0), (-1, -1), 24),
    ]))
    elems.append(t)

    title_data2 = [[Paragraph(f"<b>{paper_title}</b>", S["CoverTitle"])]]
    t2 = Table(title_data2, colWidths=[17 * cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 24),
        ("RIGHTPADDING", (0, 0), (-1, -1), 24),
    ]))
    elems.append(t2)

    meta_data = [
        [Paragraph("Venue", S["MetaKey"]),
         Paragraph("Date", S["MetaKey"]),
         Paragraph("Report ID", S["MetaKey"])],
        [Paragraph(venue, S["MetaVal"]),
         Paragraph(config.get("date", "April 2026"), S["MetaVal"]),
         Paragraph(config.get("report_id", "PR-2026-0421"), S["MetaVal"])],
    ]
    meta_table = Table(meta_data, colWidths=[5.6 * cm] * 3)
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 20),
        ("LEFTPADDING", (0, 0), (-1, -1), 24),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(meta_table)
    elems.append(Spacer(1, 0.4 * cm))
    return elems


def _build_score_cards(avg_scores: dict, S) -> list:
    """Build the dimension score cards section."""
    elems = []
    elems.append(Paragraph("Dimension Scores", S["SectionTitle"]))
    elems.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8))

    DIM_LABELS = {
        "novelty": "Novelty &\nSignificance",
        "technical": "Technical\nSoundness",
        "clarity": "Clarity &\nPresentation",
        "experiments": "Experiments &\nBaselines",
        "related_work": "Related Work &\nMotivation",
    }
    cells = []
    for dim, label in DIM_LABELS.items():
        s = avg_scores.get(dim, 0)
        cells.append([
            Paragraph(label, S["SubHeader"]),
            Paragraph(f"<b>{s}</b>/10", S["ScoreNum"]),
        ])

    t = Table(cells, colWidths=[12 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 0.4 * cm))
    return elems


def _build_verdicts(reviews: list, S) -> list:
    """Build the reviewer verdict row."""
    elems = []
    elems.append(Paragraph("Reviewer Verdicts", S["SectionTitle"]))
    elems.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8))

    verdict_data = []
    for r in reviews:
        rec = r.recommendation
        color = GREEN if rec == "Accept" else (ORANGE if rec == "Borderline" else RED)
        verdict_data.append([
            Paragraph(r.persona, S["SubHeader"]),
            Paragraph(rec, ParagraphStyle("Rec", parent=S["Body"],
                textColor=color, fontName="Helvetica-Bold", fontSize=11)),
            Paragraph(f"Confidence: {r.confidence}/10", S["SubHeader"]),
        ])

    col_w = 17 * cm / len(reviews)
    t = Table(verdict_data, colWidths=[col_w] * len(reviews))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 0.4 * cm))
    return elems


def _build_meta_review(meta_review: dict, S) -> list:
    """Build the meta-review synthesis section."""
    elems = []
    elems.append(Paragraph("Meta-Review Synthesis", S["SectionTitle"]))
    elems.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8))

    def section_block(title: str, items: list, bg_color: HexColor, border_color: HexColor) -> Table:
        rows = []
        for item in (items or []):
            rows.append([Paragraph(f"• {item}", S["BulletItem"])])
        t = Table(rows, colWidths=[16 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
        ]))
        return t

    if meta_review.get("consensus_strengths"):
        elems.append(Paragraph("Consensus Strengths", ParagraphStyle(
            "CSH", parent=S["Body"], fontName="Helvetica-Bold",
            textColor=GREEN, spaceAfter=4)))
        elems.append(section_block("Strengths", meta_review["consensus_strengths"],
                                   LIGHT_BG, STRENGTH_BORDER))
        elems.append(Spacer(1, 0.2 * cm))

    if meta_review.get("consensus_weaknesses"):
        elems.append(Paragraph("Consensus Weaknesses", ParagraphStyle(
            "CWH", parent=S["Body"], fontName="Helvetica-Bold",
            textColor=RED, spaceAfter=4)))
        elems.append(section_block("Weaknesses", meta_review["consensus_weaknesses"],
                                  LIGHT_RED_BG, WEAKNESS_BORDER))
        elems.append(Spacer(1, 0.2 * cm))

    # Final recommendation box
    rec = meta_review.get("final_recommendation", "?")
    rec_color = GREEN if "Accept" in rec else (ORANGE if "Borderline" in rec else RED)
    final_data = [
        [Paragraph("FINAL RECOMMENDATION", S["SubHeader"]),
         Paragraph("Reasoning", S["SubHeader"])],
        [Paragraph(rec, ParagraphStyle("FR", parent=S["Body"],
            textColor=rec_color, fontName="Helvetica-Bold", fontSize=12)),
         Paragraph(meta_review.get("recommendation_reasoning", ""), S["Body"])],
    ]
    ft = Table(final_data, colWidths=[4 * cm, 13 * cm])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN_BG),
        ("BOX", (0, 0), (-1, -1), 1, STRENGTH_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(ft)
    elems.append(Spacer(1, 0.4 * cm))
    return elems


def _build_individual_review(r, dim_labels: dict, S) -> list:
    """Build a single reviewer's section."""
    elems = []
    elems.append(Paragraph(f"Review — {r.persona}", S["SectionTitle"]))
    elems.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=8))
    elems.append(Paragraph(r.summary, S["Body"]))
    elems.append(Spacer(1, 0.2 * cm))

    # Score table
    score_rows = [[
        Paragraph("Dimension", S["TableHeader"]),
        Paragraph("Score", S["TableHeader"]),
        Paragraph("Comments", S["TableHeader"]),
    ]]
    for dim, label in dim_labels.items():
        sdata = r.scores.get(dim, {})
        score_val = sdata.get("score", 0)
        score_rows.append([
            Paragraph(label.replace("\n", " "), S["DimLabel"]),
            Paragraph(f"<b>{score_val}/10</b>",
                ParagraphStyle("DS", parent=S["Body"],
                    textColor=_score_color(score_val),
                    fontName="Helvetica-Bold")),
            Paragraph(sdata.get("comment", ""), S["Body"]),
        ])

    st = Table(score_rows, colWidths=[3.5 * cm, 2 * cm, 10.5 * cm])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elems.append(st)
    elems.append(Spacer(1, 0.2 * cm))

    # Strengths / Weaknesses side by side
    def bullet_list(items: list, color: HexColor, bg: HexColor, border: HexColor) -> Table:
        rows = []
        for item in items:
            rows.append([Paragraph(f"• {item}", S["BulletItem"])])
        t = Table(rows, colWidths=[7.5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 0.5, border),
        ]))
        return t

    sw_data = []
    if r.strengths:
        sw_data.append((
            Paragraph("STRENGTHS", ParagraphStyle("SHdr", parent=S["Body"],
                fontName="Helvetica-Bold", textColor=GREEN, spaceAfter=4)),
            bullet_list(r.strengths, GREEN, LIGHT_BG, STRENGTH_BORDER)
        ))
    if r.weaknesses:
        sw_data.append((
            Paragraph("WEAKNESSES", ParagraphStyle("WHdr", parent=S["Body"],
                fontName="Helvetica-Bold", textColor=RED, spaceAfter=4)),
            bullet_list(r.weaknesses, RED, LIGHT_RED_BG, WEAKNESS_BORDER)
        ))

    if sw_data:
        sw_table = Table(
            [[title, bullet] for title, bullet in sw_data],
            colWidths=[7.5 * cm, 7.5 * cm]
        )
        sw_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elems.append(sw_table)
        elems.append(Spacer(1, 0.2 * cm))

    # Questions
    if r.questions:
        elems.append(Paragraph("Questions for Authors", ParagraphStyle(
            "QH", parent=S["Body"], fontName="Helvetica-Bold",
            textColor=BLUE, spaceAfter=4)))
        for q in r.questions:
            elems.append(Paragraph(f"• {q}", S["BulletItem"]))
        elems.append(Spacer(1, 0.15 * cm))

    # Suggestions
    if r.suggestions:
        elems.append(Paragraph("Suggestions for Improvement", ParagraphStyle(
            "Suh", parent=S["Body"], fontName="Helvetica-Bold",
            textColor=BLUE, spaceAfter=4)))
        for s in r.suggestions:
            elems.append(Paragraph(f"• {s}", S["BulletItem"]))
        elems.append(Spacer(1, 0.15 * cm))

    # Minor issues
    if r.minor_issues:
        mi_rows = [
            [Paragraph("Minor Issues", ParagraphStyle(
                "MIH", parent=S["Body"], fontName="Helvetica-Bold",
                textColor=GRAY, spaceAfter=4))],
            [Paragraph("; ".join(r.minor_issues),
                ParagraphStyle("MIP", parent=S["Body"], textColor=GRAY, fontSize=9))],
        ]
        mi_t = Table(mi_rows, colWidths=[15 * cm])
        mi_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elems.append(mi_t)

    elems.append(PageBreak())
    return elems


# ── Main export function ─────────────────────────────────────────────

def export_pdf(
    output_path: str,
    paper_title: str,
    venue: str,
    reviews: list,
    meta_review: dict,
    avg_scores: dict,
    config: dict,
) -> None:
    """
    Generate a complete PDF review report.

    Args:
        output_path: Where to save the PDF.
        paper_title: Title of the paper.
        venue: Target venue name.
        reviews: List of ReviewResult dataclasses.
        meta_review: Dict from synthesize_meta_review().
        avg_scores: Dict from compute_average_scores().
        config: Dict with 'date' and 'report_id'.
    """
    S = _build_styles()
    story = []

    DIM_LABELS = {
        "novelty": "Novelty &\nSignificance",
        "technical": "Technical\nSoundness",
        "clarity": "Clarity &\nPresentation",
        "experiments": "Experiments &\nBaselines",
        "related_work": "Related Work &\nMotivation",
    }

    # Cover
    story.extend(_build_cover(paper_title, venue, config, S))

    # Executive summary from meta-review
    if meta_review.get("recommendation_reasoning"):
        story.append(Paragraph("Executive Summary", S["SectionTitle"]))
        story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=6))
        story.append(Paragraph(meta_review["recommendation_reasoning"], S["Body"]))
        story.append(Spacer(1, 0.4 * cm))

    # Score cards
    story.extend(_build_score_cards(avg_scores, S))

    # Verdict row
    story.extend(_build_verdicts(reviews, S))

    # Meta-review
    story.extend(_build_meta_review(meta_review, S))

    # Individual reviews
    for r in reviews:
        story.extend(_build_individual_review(r, DIM_LABELS, S))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        "Generated by Peer Review Simulator · Not an official conference review",
        S["Footer"]))

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story)