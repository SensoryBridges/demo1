"""
Report Generation Module.

Produces legally defensible reports in Excel and Word formats
with full analysis, charts, evidence citations, and methodology documentation.
"""

import os
from datetime import datetime

import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


class ExcelReportGenerator:
    """Generates comprehensive Excel workbook reports."""

    HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    ALERT_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    GOOD_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    WARN_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    CRITICAL_FILL = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
    CRITICAL_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    HIGH_FILL = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
    MODERATE_FILL = PatternFill(start_color="FFD93D", end_color="FFD93D", fill_type="solid")
    LOW_FILL = PatternFill(start_color="A8E6CF", end_color="A8E6CF", fill_type="solid")
    SUBHEADER_FILL = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
    SUBHEADER_FONT = Font(name="Calibri", size=11, bold=True, color="1F4E79")
    BORDER = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    def __init__(self, output_path="output/analysis_report.xlsx"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        self.wb = openpyxl.Workbook()
        self.wb.remove(self.wb.active)

    def _add_sheet(self, name, df=None, title=None):
        """Add a formatted sheet with optional DataFrame data."""
        ws = self.wb.create_sheet(title=name[:31])

        row_offset = 1
        if title:
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(len(df.columns) if df is not None else 5, 5))
            cell = ws.cell(row=1, column=1, value=title)
            cell.font = Font(name="Calibri", size=14, bold=True, color="1F4E79")
            cell.alignment = Alignment(horizontal="center")
            row_offset = 3

        if df is not None and not df.empty:
            # Headers
            for col_idx, col_name in enumerate(df.columns, 1):
                cell = ws.cell(row=row_offset, column=col_idx, value=str(col_name).replace("_", " ").title())
                cell.fill = self.HEADER_FILL
                cell.font = self.HEADER_FONT
                cell.alignment = Alignment(horizontal="center", wrap_text=True)
                cell.border = self.BORDER

            # Data
            for row_idx, row_data in enumerate(df.itertuples(index=False), row_offset + 1):
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    if isinstance(value, (np.integer,)):
                        cell.value = int(value)
                    elif isinstance(value, (np.floating,)):
                        cell.value = round(float(value), 3)
                    elif pd.isna(value):
                        cell.value = ""
                    else:
                        cell.value = str(value) if not isinstance(value, (int, float, datetime)) else value
                    cell.border = self.BORDER
                    cell.alignment = Alignment(wrap_text=True, vertical="top")

            # Auto-width columns
            for col_idx in range(1, len(df.columns) + 1):
                max_len = max(
                    len(str(ws.cell(row=r, column=col_idx).value or ""))
                    for r in range(row_offset, min(row_offset + len(df) + 1, row_offset + 50))
                )
                ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = min(50, max(12, max_len + 2))

        return ws

    def _add_dict_sheet(self, name, data_dict, title=None):
        """Add a sheet from a dictionary."""
        rows = []
        self._flatten_dict(data_dict, rows)
        df = pd.DataFrame(rows, columns=["Field", "Value"])
        return self._add_sheet(name, df, title)

    def _flatten_dict(self, d, rows, prefix=""):
        """Flatten nested dict into rows."""
        for key, value in d.items():
            label = f"{prefix}{key}".replace("_", " ").title()
            if isinstance(value, dict):
                rows.append([label, "---"])
                self._flatten_dict(value, rows, prefix=f"  ")
            elif isinstance(value, list):
                rows.append([label, f"({len(value)} items)"])
                for i, item in enumerate(value[:50]):
                    if isinstance(item, dict):
                        for k, v in item.items():
                            rows.append([f"    [{i + 1}] {k}", str(v)[:500]])
                    else:
                        rows.append([f"    [{i + 1}]", str(item)[:500]])
            else:
                rows.append([label, str(value)[:500]])

    def add_executive_summary(self, summary_data):
        """Add executive summary sheet."""
        self._add_dict_sheet("Executive Summary", summary_data,
                             "CASE ANALYSIS — EXECUTIVE SUMMARY")

    def add_abuse_analysis(self, classified_df):
        """Add abuse classification results."""
        self._add_sheet("Abuse Analysis", classified_df,
                        "POST-SEPARATION ABUSE ANALYSIS")

    def add_cycle_predictions(self, predictions_data):
        """Add cycle prediction results."""
        if "predictions" in predictions_data:
            pred_df = pd.DataFrame(predictions_data["predictions"])
            self._add_sheet("Cycle Predictions", pred_df,
                            "ABUSE CYCLE PREDICTIONS")
        if "analysis_summary" in predictions_data:
            self._add_dict_sheet("Pattern Analysis", predictions_data["analysis_summary"],
                                 "PATTERN ANALYSIS DETAILS")

    def add_court_timeline(self, timeline_data):
        """Add court case timeline."""
        if isinstance(timeline_data, list):
            df = pd.DataFrame(timeline_data)
        else:
            df = timeline_data
        self._add_sheet("Court Timeline", df, "COURT CASE TIMELINE")

    def add_officials_analysis(self, officials_df, earnings_data=None):
        """Add court officials analysis."""
        self._add_sheet("Officials", officials_df, "COURT OFFICIALS ANALYSIS")
        if earnings_data:
            earn_df = pd.DataFrame.from_dict(earnings_data, orient="index")
            self._add_sheet("Official Earnings", earn_df.reset_index().rename(columns={"index": "name"}),
                            "ESTIMATED OFFICIAL EARNINGS")

    def add_violations(self, violations):
        """Add procedural violations sheet."""
        if violations:
            df = pd.DataFrame(violations)
            ws = self._add_sheet("Violations", df, "PROCEDURAL VIOLATIONS IDENTIFIED")
            # Highlight severity
            if "severity" in df.columns:
                sev_col = list(df.columns).index("severity") + 1
                for row_idx in range(4, 4 + len(df)):
                    cell = ws.cell(row=row_idx, column=sev_col)
                    if "HIGH" in str(cell.value) or "CRITICAL" in str(cell.value):
                        cell.fill = self.ALERT_FILL
                    elif "MODERATE" in str(cell.value):
                        cell.fill = self.WARN_FILL

    def add_financial_analysis(self, costs_data):
        """Add financial analysis sheet."""
        self._add_dict_sheet("Financial Analysis", costs_data,
                             "FINANCIAL ANALYSIS")

    def add_connections(self, connections):
        """Add connections analysis."""
        if connections:
            df = pd.DataFrame(connections)
            self._add_sheet("Connections", df, "OFFICIAL CONNECTIONS ANALYSIS")

    def add_scorecards(self, scorecards_df):
        """Add official scorecards."""
        ws = self._add_sheet("Scorecards", scorecards_df, "COURT OFFICIAL SCORECARDS")
        # Highlight grades
        if not scorecards_df.empty and "overall_score" in scorecards_df.columns:
            score_col = list(scorecards_df.columns).index("overall_score") + 1
            for row_idx in range(4, 4 + len(scorecards_df)):
                cell = ws.cell(row=row_idx, column=score_col)
                try:
                    val = float(cell.value)
                    if val < 50:
                        cell.fill = self.ALERT_FILL
                    elif val < 70:
                        cell.fill = self.WARN_FILL
                    else:
                        cell.fill = self.GOOD_FILL
                except (ValueError, TypeError):
                    pass

    def add_document_comparison(self, comparison_result):
        """Add document comparison side-by-side view."""
        sbs = comparison_result.get("side_by_side", [])
        if sbs:
            df = pd.DataFrame(sbs)
            ws = self._add_sheet("Doc Comparison", df,
                                 "DOCUMENT COMPARISON — SIDE BY SIDE")
            # Highlight differences
            if "flag" in df.columns:
                flag_col = list(df.columns).index("flag") + 1
                for row_idx in range(4, 4 + len(df)):
                    cell = ws.cell(row=row_idx, column=flag_col)
                    if cell.value == "DIFFERENT":
                        cell.fill = self.ALERT_FILL
                    elif cell.value == "SIMILAR":
                        cell.fill = self.WARN_FILL
                    elif cell.value == "MATCH":
                        cell.fill = self.GOOD_FILL

        # Contradictions
        contras = comparison_result.get("contradictions", [])
        if contras:
            df2 = pd.DataFrame(contras)
            self._add_sheet("Contradictions", df2, "DOCUMENT CONTRADICTIONS")

    def add_formula_documentation(self, formula_doc):
        """Add CASI formula documentation."""
        self._add_dict_sheet("CASI Formula", formula_doc,
                             "COMPOSITE ABUSE SEVERITY INDEX (CASI) — FORMULA DOCUMENTATION")

    def add_case_outcome_prediction(self, prediction_data):
        """Add outcome prediction results."""
        self._add_dict_sheet("Outcome Prediction", prediction_data,
                             "CASE OUTCOME PREDICTION")

    def add_methodology(self):
        """Add methodology documentation sheet for legal defensibility."""
        methodology = {
            "Report Purpose": "Forensic analysis of post-separation abuse patterns and court case proceedings",
            "Methodology": {
                "Data Collection": "All data sourced from court records, documented communications, and official filings",
                "Classification System": "Incidents classified using standardized abuse taxonomy aligned with VAWA definitions",
                "Statistical Methods": "Time-series analysis, correlation testing, linear regression, peak detection",
                "Prediction Model": "Composite Abuse Severity Index (CASI) — see formula documentation sheet",
                "Validation": "All statistical findings include p-values and confidence intervals",
            },
            "Legal Standards": {
                "Evidence Standard": "Analysis based on documented evidence only — no conjecture",
                "Statistical Significance": "Findings marked significant at p < 0.05 level",
                "Reproducibility": "All calculations are deterministic and reproducible from source data",
                "Limitations": "Predictions are probabilistic projections, not certainties. "
                              "Analysis quality depends on completeness of input data.",
            },
            "Disclaimers": {
                "Not Legal Advice": "This report is an analytical tool and does not constitute legal advice",
                "Professional Review": "Findings should be reviewed by qualified legal and mental health professionals",
                "Data Dependency": "Conclusions are only as reliable as the underlying data",
            },
            "Report Generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Tool Version": "Abuse Court Analyzer v1.0.0",
        }
        self._add_dict_sheet("Methodology", methodology,
                             "METHODOLOGY & LEGAL DEFENSIBILITY")

    def add_charts_sheet(self, chart_paths):
        """Add a sheet with embedded chart images."""
        ws = self.wb.create_sheet(title="Charts")
        ws.merge_cells("A1:F1")
        cell = ws.cell(row=1, column=1, value="VISUAL ANALYSIS")
        cell.font = Font(name="Calibri", size=14, bold=True, color="1F4E79")

        row = 3
        for path in chart_paths:
            if os.path.exists(path):
                try:
                    img = openpyxl.drawing.image.Image(path)
                    img.width = 800
                    img.height = 400
                    ws.add_image(img, f"A{row}")
                    row += 22  # Space for next image
                except Exception:
                    ws.cell(row=row, column=1, value=f"[Chart: {os.path.basename(path)}]")
                    row += 2

    def save(self):
        """Save the workbook."""
        self.wb.save(self.output_path)
        return self.output_path


class WordReportGenerator:
    """Generates a formal Word document report."""

    def __init__(self, output_path="output/analysis_report.docx"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        self.doc = Document()
        self._setup_styles()

    def _setup_styles(self):
        """Configure document styles."""
        style = self.doc.styles["Normal"]
        style.font.name = "Times New Roman"
        style.font.size = Pt(12)
        style.paragraph_format.space_after = Pt(6)

    def add_title_page(self, case_name="", case_number="", state="", county=""):
        """Add a formal title page."""
        for _ in range(6):
            self.doc.add_paragraph()

        title = self.doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run("FORENSIC ANALYSIS REPORT")
        run.font.size = Pt(24)
        run.bold = True

        subtitle = self.doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = subtitle.add_run("Post-Separation Abuse Pattern Analysis\n& Court Case Review")
        run.font.size = Pt(16)

        self.doc.add_paragraph()

        if case_name:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(f"Case: {case_name}")
            run.font.size = Pt(14)

        if case_number:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(f"Case Number: {case_number}").font.size = Pt(12)

        if state or county:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            location = ", ".join(filter(None, [county, state]))
            p.add_run(f"Jurisdiction: {location}").font.size = Pt(12)

        self.doc.add_paragraph()
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"Report Date: {datetime.now().strftime('%B %d, %Y')}").font.size = Pt(12)

        self.doc.add_paragraph()
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("CONFIDENTIAL — ATTORNEY-CLIENT PRIVILEGED")
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(192, 0, 0)

        self.doc.add_page_break()

    def add_table_of_contents(self):
        """Add table of contents placeholder."""
        self.doc.add_heading("Table of Contents", level=1)
        p = self.doc.add_paragraph(
            "[This table of contents should be updated after final report generation. "
            "Right-click and select 'Update Field' in Microsoft Word.]"
        )
        p.italic = True
        self.doc.add_page_break()

    def add_executive_summary(self, summary_data):
        """Add executive summary section."""
        self.doc.add_heading("1. Executive Summary", level=1)

        if isinstance(summary_data, dict):
            for key, value in summary_data.items():
                if isinstance(value, dict):
                    self.doc.add_heading(key.replace("_", " ").title(), level=3)
                    for k2, v2 in value.items():
                        p = self.doc.add_paragraph()
                        run = p.add_run(f"{k2.replace('_', ' ').title()}: ")
                        run.bold = True
                        p.add_run(str(v2))
                elif isinstance(value, list):
                    self.doc.add_heading(key.replace("_", " ").title(), level=3)
                    for item in value:
                        self.doc.add_paragraph(str(item), style="List Bullet")
                else:
                    p = self.doc.add_paragraph()
                    run = p.add_run(f"{key.replace('_', ' ').title()}: ")
                    run.bold = True
                    p.add_run(str(value))
        else:
            self.doc.add_paragraph(str(summary_data))

    def add_abuse_analysis_section(self, classified_df, formula_doc=None):
        """Add abuse analysis section."""
        self.doc.add_heading("2. Post-Separation Abuse Analysis", level=1)

        self.doc.add_heading("2.1 Classification Methodology", level=2)
        self.doc.add_paragraph(
            "Incidents were classified using a standardized taxonomy of post-separation "
            "abuse categories, each with defined behavioral traits and severity weights. "
            "The classification system is aligned with definitions from the Violence Against "
            "Women Act (VAWA) and established domestic violence research."
        )

        if formula_doc:
            self.doc.add_heading("2.2 Composite Abuse Severity Index (CASI)", level=2)
            self.doc.add_paragraph(f"Formula: {formula_doc.get('formula', 'N/A')}")
            components = formula_doc.get("components", {})
            for comp_id, comp_info in components.items():
                p = self.doc.add_paragraph()
                run = p.add_run(f"{comp_id} — {comp_info.get('name', '')}: ")
                run.bold = True
                p.add_run(comp_info.get("description", ""))

        if classified_df is not None and not classified_df.empty:
            self.doc.add_heading("2.3 Incident Classification Results", level=2)
            self._add_dataframe_table(classified_df.head(50))

    def add_cycle_prediction_section(self, predictions_data):
        """Add cycle prediction section."""
        self.doc.add_heading("3. Abuse Cycle Prediction", level=1)

        if "model_info" in predictions_data:
            info = predictions_data["model_info"]
            self.doc.add_paragraph(f"Data points analyzed: {info.get('data_points', 'N/A')}")
            self.doc.add_paragraph(f"Date range: {info.get('date_range', 'N/A')}")
            self.doc.add_paragraph(f"Method: {info.get('method', 'N/A')}")

        if "predictions" in predictions_data:
            self.doc.add_heading("3.1 Predicted Cycles", level=2)
            pred_df = pd.DataFrame(predictions_data["predictions"])
            self._add_dataframe_table(pred_df)

        # Disclaimer
        p = self.doc.add_paragraph()
        run = p.add_run("Disclaimer: ")
        run.bold = True
        run.font.color.rgb = RGBColor(192, 0, 0)
        p.add_run(predictions_data.get("model_info", {}).get("disclaimer",
                  "Predictions are statistical projections only."))

    def add_court_analysis_section(self, duration_data, filing_patterns, timeline):
        """Add court case analysis section."""
        self.doc.add_heading("4. Court Case Analysis", level=1)

        if duration_data and "error" not in duration_data:
            self.doc.add_heading("4.1 Case Duration", level=2)
            for key, value in duration_data.items():
                p = self.doc.add_paragraph()
                run = p.add_run(f"{key.replace('_', ' ').title()}: ")
                run.bold = True
                p.add_run(str(value))

        if filing_patterns:
            self.doc.add_heading("4.2 Filing Patterns", level=2)
            for key, value in filing_patterns.items():
                p = self.doc.add_paragraph()
                run = p.add_run(f"{key.replace('_', ' ').title()}: ")
                run.bold = True
                if isinstance(value, dict):
                    p.add_run(str(value))
                else:
                    p.add_run(str(value))

    def add_officials_section(self, officials_df, earnings, scorecards_df):
        """Add court officials analysis section."""
        self.doc.add_heading("5. Court Officials Analysis", level=1)

        if officials_df is not None and not officials_df.empty:
            self.doc.add_heading("5.1 Officials Involved", level=2)
            self._add_dataframe_table(officials_df)

        if earnings:
            self.doc.add_heading("5.2 Estimated Earnings from Case", level=2)
            earn_df = pd.DataFrame.from_dict(earnings, orient="index").reset_index()
            earn_df = earn_df.rename(columns={"index": "name"})
            self._add_dataframe_table(earn_df)

        if scorecards_df is not None and not scorecards_df.empty:
            self.doc.add_heading("5.3 Official Scorecards", level=2)
            for _, row in scorecards_df.iterrows():
                self.doc.add_heading(
                    f"{row.get('name', 'Unknown')} — {row.get('role', '')} "
                    f"(Grade: {row.get('overall_grade', 'N/A')})", level=3
                )
                self.doc.add_paragraph(str(row.get("summary", "")))
                if row.get("flags"):
                    self.doc.add_paragraph("Flags:", style="List Bullet")
                    for flag in str(row.get("flags", "")).split("; "):
                        if flag.strip():
                            self.doc.add_paragraph(flag.strip(), style="List Bullet 2")

    def add_violations_section(self, violations):
        """Add procedural violations section."""
        self.doc.add_heading("6. Procedural Violations", level=1)

        if not violations:
            self.doc.add_paragraph("No procedural violations detected in the available data.")
            return

        self.doc.add_paragraph(f"Total violations identified: {len(violations)}")

        for i, v in enumerate(violations, 1):
            self.doc.add_heading(
                f"Violation #{i}: {v.get('type', 'Unknown')}", level=2
            )
            p = self.doc.add_paragraph()
            run = p.add_run("Description: ")
            run.bold = True
            p.add_run(str(v.get("description", "")))

            p = self.doc.add_paragraph()
            run = p.add_run("Applicable Law: ")
            run.bold = True
            p.add_run(str(v.get("law", "")))

            p = self.doc.add_paragraph()
            run = p.add_run("Citation: ")
            run.bold = True
            p.add_run(str(v.get("citation", "")))

            p = self.doc.add_paragraph()
            run = p.add_run("Severity: ")
            run.bold = True
            severity = str(v.get("severity", ""))
            sev_run = p.add_run(severity)
            if "HIGH" in severity or "CRITICAL" in severity:
                sev_run.font.color.rgb = RGBColor(192, 0, 0)
                sev_run.bold = True

    def add_financial_section(self, costs_data):
        """Add financial analysis section."""
        self.doc.add_heading("7. Financial Analysis", level=1)

        if costs_data.get("total_actual"):
            self.doc.add_paragraph(f"Total documented costs: ${costs_data['total_actual']:,.2f}")
        if costs_data.get("total_estimated"):
            self.doc.add_paragraph(f"Total estimated costs: ${costs_data['total_estimated']:,.0f}")

        if costs_data.get("per_party"):
            self.doc.add_heading("7.1 Costs by Party", level=2)
            for party, amount in costs_data["per_party"].items():
                self.doc.add_paragraph(f"{party}: ${amount:,.2f}", style="List Bullet")

        if costs_data.get("per_official"):
            self.doc.add_heading("7.2 Payments to Officials", level=2)
            for official, amount in costs_data["per_official"].items():
                self.doc.add_paragraph(f"{official}: ${amount:,.2f}", style="List Bullet")

    def add_connections_section(self, connections):
        """Add connections analysis section."""
        self.doc.add_heading("8. Official Connections Analysis", level=1)

        if not connections:
            self.doc.add_paragraph("No connections identified from available data.")
            return

        for c in connections:
            p = self.doc.add_paragraph()
            run = p.add_run(f"{c['person_1']} ({c['role_1']}) ")
            run.bold = True
            p.add_run(f"↔ ")
            run = p.add_run(f"{c['person_2']} ({c['role_2']})")
            run.bold = True
            self.doc.add_paragraph(
                f"  Connection: {c['connection_type']} — {c.get('details', '')}",
                style="List Bullet"
            )

    def add_outcome_prediction_section(self, prediction_data):
        """Add case outcome prediction section."""
        self.doc.add_heading("9. Case Outcome Prediction", level=1)

        if isinstance(prediction_data, dict):
            for key, value in prediction_data.items():
                if key == "disclaimer":
                    p = self.doc.add_paragraph()
                    run = p.add_run("Disclaimer: ")
                    run.bold = True
                    p.add_run(str(value))
                elif isinstance(value, dict):
                    self.doc.add_heading(key.replace("_", " ").title(), level=2)
                    for k2, v2 in value.items():
                        self.doc.add_paragraph(
                            f"{k2.replace('_', ' ').title()}: {v2}",
                            style="List Bullet"
                        )
                else:
                    p = self.doc.add_paragraph()
                    run = p.add_run(f"{key.replace('_', ' ').title()}: ")
                    run.bold = True
                    p.add_run(str(value))

    def add_document_comparison_section(self, comparison_result):
        """Add document comparison section."""
        self.doc.add_heading("10. Document Comparison Analysis", level=1)

        self.doc.add_paragraph(
            f"Similarity Score: {comparison_result.get('similarity_score', 'N/A')}"
        )

        contras = comparison_result.get("contradictions", [])
        if contras:
            self.doc.add_heading("10.1 Contradictions Found", level=2)
            for c in contras:
                self.doc.add_paragraph(
                    f"Type: {c.get('type', '')} — "
                    f"Doc A: \"{c.get('doc_a_statement', c.get('doc_a_value', ''))[:100]}\" vs "
                    f"Doc B: \"{c.get('doc_b_statement', c.get('doc_b_value', ''))[:100]}\"",
                    style="List Bullet"
                )

    def add_charts(self, chart_paths):
        """Embed chart images in the document."""
        self.doc.add_heading("Appendix A: Visual Analysis", level=1)

        for path in chart_paths:
            if os.path.exists(path):
                try:
                    self.doc.add_picture(path, width=Inches(6))
                    self.doc.add_paragraph()
                except Exception:
                    self.doc.add_paragraph(f"[Chart: {os.path.basename(path)}]")

    def add_methodology_section(self):
        """Add methodology section for legal defensibility."""
        self.doc.add_heading("Appendix B: Methodology", level=1)

        self.doc.add_heading("Data Collection", level=2)
        self.doc.add_paragraph(
            "All data analyzed in this report was sourced from court records, "
            "documented communications, official filings, and evidence provided "
            "by the submitting party. No data was fabricated or assumed."
        )

        self.doc.add_heading("Classification Methodology", level=2)
        self.doc.add_paragraph(
            "Abuse incidents were classified using a standardized taxonomy of "
            "post-separation abuse categories. Each category includes defined "
            "behavioral traits with pre-assigned severity weights. Classification "
            "is performed by matching documented behaviors against trait definitions."
        )

        self.doc.add_heading("Statistical Methods", level=2)
        methods = [
            "Time-series analysis for temporal pattern identification",
            "Pearson correlation testing for variable relationships",
            "Linear regression for trend analysis and escalation detection",
            "Peak detection algorithms for cycle identification",
            "ANOVA testing for categorical variable significance",
        ]
        for m in methods:
            self.doc.add_paragraph(m, style="List Bullet")

        self.doc.add_heading("Limitations", level=2)
        self.doc.add_paragraph(
            "This analysis is limited by the completeness and accuracy of the "
            "source data. Statistical predictions are probabilistic in nature and "
            "should not be treated as certainties. This report does not constitute "
            "legal advice and should be reviewed by qualified professionals."
        )

        self.doc.add_heading("Reproducibility", level=2)
        self.doc.add_paragraph(
            "All calculations in this report are deterministic and fully reproducible "
            "from the source data using the documented methodology. The analysis "
            "software version and parameters are recorded for verification purposes."
        )

    def _add_dataframe_table(self, df, max_rows=50):
        """Add a DataFrame as a formatted Word table."""
        if df.empty:
            return

        df = df.head(max_rows)
        table = self.doc.add_table(rows=1, cols=len(df.columns), style="Light Shading Accent 1")
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Headers
        for i, col in enumerate(df.columns):
            cell = table.rows[0].cells[i]
            cell.text = str(col).replace("_", " ").title()
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(9)

        # Data
        for _, row_data in df.iterrows():
            row = table.add_row()
            for i, value in enumerate(row_data):
                cell = row.cells[i]
                if pd.isna(value):
                    cell.text = ""
                else:
                    cell.text = str(value)[:200]
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(9)

    def save(self):
        """Save the Word document."""
        self.doc.save(self.output_path)
        return self.output_path
