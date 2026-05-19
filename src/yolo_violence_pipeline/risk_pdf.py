"""Geração de PDF formatado com a avaliação de risco."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _bullet_lines(items: list[Any], style: ParagraphStyle) -> list:
    flow: list = []
    for item in items:
        text = str(item).replace("&", "&amp;").replace("<", "&lt;")
        flow.append(Paragraph(f"• {text}", style))
    return flow


def build_risk_assessment_pdf(
    *,
    output_path: Path,
    source_filename: str,
    model_name: str,
    transcript_excerpt: str,
    analysis: dict[str, Any],
) -> None:
    """Grava PDF individualizado com a avaliação de conteúdo."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=16,
        textColor=colors.HexColor("#1a365d"),
    )
    body = styles["BodyText"]
    body.spaceAfter = 6

    nivel = str(analysis.get("nivel_risco", "n/a")).upper()
    pontuacao = analysis.get("pontuacao", "—")
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    story: list = [
        Paragraph("Avaliação de risco — conteúdo transcrito", title_style),
        Spacer(1, 0.3 * cm),
        Paragraph(f"<b>Arquivo:</b> {source_filename}", body),
        Paragraph(f"<b>Modelo:</b> {model_name}", body),
        Paragraph(f"<b>Gerado em:</b> {now}", body),
        Spacer(1, 0.4 * cm),
    ]

    summary_data = [
        ["Nível de risco", nivel],
        ["Pontuação (0–100)", str(pontuacao)],
        ["Categorias", ", ".join(analysis.get("categorias", [])) or "—"],
    ]
    table = Table(summary_data, colWidths=[5 * cm, 11 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([table, Spacer(1, 0.5 * cm)])

    story.append(Paragraph("<b>Resumo executivo</b>", body))
    story.append(Paragraph(str(analysis.get("resumo_executivo", "")), body))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("<b>Justificativa</b>", body))
    story.append(Paragraph(str(analysis.get("justificativa", "")), body))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("<b>Indicadores identificados</b>", body))
    story.extend(_bullet_lines(analysis.get("indicadores", []), body))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("<b>Recomendações</b>", body))
    story.extend(_bullet_lines(analysis.get("recomendacoes", []), body))
    story.append(Spacer(1, 0.4 * cm))

    excerpt = transcript_excerpt[:2000]
    if len(transcript_excerpt) > 2000:
        excerpt += "\n[... texto truncado no PDF ...]"
    story.append(Paragraph("<b>Trecho da transcrição analisada</b>", body))
    story.append(Paragraph(excerpt.replace("\n", "<br/>"), body))

    doc.build(story)
