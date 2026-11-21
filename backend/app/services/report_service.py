import io
import csv
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.all_models import Job, MatchingAnalysis


def _sanitize_csv_cell(val: Any) -> Any:
    """Neutralize formula injection by prefixing formula triggers with a single quote."""
    if isinstance(val, str) and val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{val}"
    return val


class ReportService:
    @staticmethod
    def export_csv(job: Job, analyses: List[MatchingAnalysis]) -> io.StringIO:
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Rank",
            "Candidate Name",
            "Email",
            "Total Experience (Years)",
            "Overall Score (100)",
            "Technical Score (40)",
            "Semantic Score (30)",
            "Experience Score (20)",
            "Education Score (10)",
            "Matched Skills Count",
            "Missing Skills Count",
            "Matched Skills",
            "Missing Skills"
        ])

        for rank, a in enumerate(analyses, 1):
            cand = a.candidate
            matched_str = "; ".join([m.get("skill", "") for m in a.matched_skills])
            missing_str = "; ".join(a.missing_skills)

            row = [
                rank,
                cand.name if cand else "Unknown",
                cand.email if cand else "",
                cand.total_experience_years if cand else 0.0,
                a.overall_score,
                a.technical_score,
                a.semantic_score,
                a.experience_score,
                a.education_score,
                len(a.matched_skills),
                len(a.missing_skills),
                matched_str,
                missing_str
            ]
            writer.writerow([_sanitize_csv_cell(cell) for cell in row])

        output.seek(0)
        return output

    @staticmethod
    def export_excel(job: Job, analyses: List[MatchingAnalysis]) -> io.BytesIO:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Candidate Rankings"

        # Title styling
        ws.merge_cells("A1:K1")
        title_cell = ws["A1"]
        title_cell.value = f"TalentMatch AI — Candidate Ranking Report: {job.title} ({job.company})"
        title_cell.font = Font(name="Arial", size=14, bold=True, color="1E3A8A")
        title_cell.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 30

        headers = [
            "Rank", "Candidate Name", "Email", "Exp (Yrs)",
            "Overall Score", "Tech (40)", "Semantic (30)",
            "Exp (20)", "Edu (10)", "Matched Skills", "Missing Skills"
        ]
        ws.append([])  # blank row 2
        ws.append(headers)

        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=3, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[3].height = 24

        for rank, a in enumerate(analyses, 1):
            cand = a.candidate
            matched_str = ", ".join([m.get("skill", "") for m in a.matched_skills[:8]])
            missing_str = ", ".join(a.missing_skills[:5])

            ws.append([
                rank,
                cand.name if cand else "Unknown",
                cand.email if cand else "",
                cand.total_experience_years if cand else 0.0,
                f"{a.overall_score}%",
                a.technical_score,
                a.semantic_score,
                a.experience_score,
                a.education_score,
                matched_str,
                missing_str
            ])

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(40, max(12, max_len + 3))

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def export_pdf(job: Job, analyses: List[MatchingAnalysis]) -> io.BytesIO:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1E3A8A")
        )
        elements.append(Paragraph(f"TalentMatch AI — Candidate Ranking Report", title_style))
        elements.append(Spacer(1, 4))

        sub_style = ParagraphStyle(
            "DocSub",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#475569")
        )
        elements.append(Paragraph(f"<b>Job Title:</b> {job.title} | <b>Company:</b> {job.company} | <b>Min Exp:</b> {job.min_experience} yrs", sub_style))
        elements.append(Spacer(1, 14))

        # Table data
        table_data = [[
            "Rank", "Candidate Name", "Exp", "Overall", "Tech", "Semantic", "Status"
        ]]

        for rank, a in enumerate(analyses[:30], 1):
            cand = a.candidate
            status = cand.status.capitalize() if cand else "New"
            table_data.append([
                str(rank),
                cand.name[:22] if cand else "Candidate",
                f"{cand.total_experience_years}y" if cand else "0y",
                f"{a.overall_score}%",
                f"{a.technical_score}/40",
                f"{a.semantic_score}/30",
                status
            ])

        t = Table(table_data, colWidths=[35, 160, 45, 60, 60, 65, 80])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
        ]))

        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer
