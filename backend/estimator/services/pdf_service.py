"""Build estimation PDF reports (ReportLab)."""

from __future__ import annotations

import re
from io import BytesIO
from typing import BinaryIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from estimator.models import Project
from estimator.utils.formatters import format_cocomo_mode, format_datetime, format_decimal


def build_project_report_data(project: Project) -> dict:
    """Map a saved Project row to the dict expected by generate_pdf_report."""
    outputs = project.outputs or {}
    inputs = project.inputs or {}
    return {
        "project_name": project.name,
        "ufp": outputs.get("ufp", 0),
        "caf": outputs.get("caf", 0),
        "fp": outputs.get("fp", project.fp),
        "cocomo_mode": inputs.get("cocomo_mode", "organic"),
        "effort_pm": outputs.get("effort_pm", project.effort_pm),
        "tdev_months": outputs.get("tdev_months", project.tdev_months),
        "kloc": outputs.get("kloc"),
        "timestamp": project.updated_at,
    }


def _safe_filename_part(name: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    slug = re.sub(r"[-\s]+", "-", slug).strip("-").lower()
    return (slug[:max_len] or "project").rstrip("-")


def generate_pdf_report(project_data: dict) -> BinaryIO:
    """
    Render a PDF from estimation fields.

    Expected keys: project_name, ufp, caf, fp, cocomo_mode, effort_pm,
    tdev_months, timestamp (datetime or ISO string). Optional: kloc.

    Returns a BytesIO buffer positioned at the start (use with FileResponse).
    """
    required = (
        "project_name",
        "ufp",
        "caf",
        "fp",
        "cocomo_mode",
        "effort_pm",
        "tdev_months",
        "timestamp",
    )
    missing = [k for k in required if k not in project_data]
    if missing:
        raise ValueError(f"project_data missing keys: {', '.join(missing)}")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch * 0.75,
        leftMargin=inch * 0.75,
        topMargin=inch * 0.75,
        bottomMargin=inch * 0.75,
        title="Estimation report",
    )

    styles = getSampleStyleSheet()
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.HexColor("#134e4a"),
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
    )

    name = escape(str(project_data["project_name"]))
    mode_key = project_data["cocomo_mode"]
    mode_label_plain = format_cocomo_mode(mode_key)
    ts = format_datetime(project_data["timestamp"])

    story = []

    # Header band (logo-style)
    header_data = [
        [
            Paragraph(
                '<b><font color="white" size="14">FP + COCOMO</font></b><br/>'
                '<font color="#ccfbf1" size="9">Estimation report</font>',
                ParagraphStyle("hdr", parent=styles["Normal"], alignment=1),
            )
        ]
    ]
    header_table = Table(header_data, colWidths=[6.5 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0d9488")),
                ("BOX", (0, 0), (-1, -1), 0, colors.HexColor("#0f766e")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"Project: <b>{name}</b>", body))
    story.append(Paragraph(f"Generated: {escape(str(ts))}", body))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Function points", section_style))
    fp_rows = [
        ["Metric", "Value"],
        ["Unadjusted function points (UFP)", format_decimal(project_data["ufp"])],
        ["Complexity adjustment factor (CAF)", format_decimal(project_data["caf"])],
        ["Adjusted function points (FP)", format_decimal(project_data["fp"])],
    ]
    kloc = project_data.get("kloc")
    if kloc is not None:
        fp_rows.append(["KLOC (FP ÷ 100)", format_decimal(kloc)])

    fp_table = Table(fp_rows, colWidths=[3.4 * inch, 2.4 * inch])
    fp_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(fp_table)

    story.append(Paragraph("COCOMO (Basic)", section_style))
    coco_rows = [
        ["Field", "Value"],
        ["Mode", mode_label_plain],
        ["Effort (person-months)", format_decimal(project_data["effort_pm"])],
        ["Development time (months)", format_decimal(project_data["tdev_months"])],
    ]
    coco_table = Table(coco_rows, colWidths=[3.4 * inch, 2.4 * inch])
    coco_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ede9fe")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c4b5fd")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf5ff")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(coco_table)
    story.append(Spacer(1, 0.25 * inch))
    story.append(
        Paragraph(
            "<i>Figures use the same rules as the web estimator (IFPUG-style weights, "
            "Basic COCOMO, KLOC = FP ÷ 100).</i>",
            ParagraphStyle("Foot", parent=body, fontSize=8, textColor=colors.HexColor("#64748b")),
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer


def suggested_pdf_filename(project_id: int, project_name: str) -> str:
    part = _safe_filename_part(project_name)
    return f"estimate-{project_id}-{part}.pdf"
