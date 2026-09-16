import csv
import html
import io
import json
import os
import re
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file, session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from ..extensions import db
from ..helpers import parse_date
from ..timezone import ph_now, ph_today
from ..models import BlotterRecord, GeneratedReport, Incident, MlRun, Settlement
from ..permissions import json_error, login_required, permission_required

bp = Blueprint("reports", __name__)

REPORTS_DIR = os.path.join("/tmp", "generated_reports") if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "..", "..", "generated_reports")
try:
    os.makedirs(REPORTS_DIR, exist_ok=True)
except OSError:
    pass

BC_GREEN = colors.HexColor("#1e3a2b")
BC_GREEN_DARK = colors.HexColor("#1e3a2b")
BC_GREEN_HEADER = colors.HexColor("#1e3a2b")
BC_GREEN_PALE = colors.HexColor("#f0f9f2")

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@bp.route("/api/reports.php", methods=["GET", "POST"])
@login_required
@permission_required("generate_reports")
def reports_router():
    action = request.args.get("action", "")
    if action == "list":
        return _list()
    if action == "generate" and request.method == "POST":
        return _generate()
    if action == "download":
        return _download()
    return json_error("Unknown action", 404)


def _list():
    rows = GeneratedReport.query.order_by(GeneratedReport.id.desc()).limit(20).all()
    return jsonify([{
        "id": r.id, "report_type": r.report_type, "generated_by": r.generated_by,
        "period_from": r.period_from.isoformat() if r.period_from else None,
        "period_to": r.period_to.isoformat() if r.period_to else None,
        "format": r.format, "file_path": r.file_path,
        # period_from/period_to are plain Date columns (no time-of-day, so
        # no ambiguity); created_at is a naive-UTC DateTime and needs "Z".
        "created_at": (r.created_at.isoformat() + "Z") if r.created_at else None,
    } for r in rows])


# ---------------- PDF builder helpers (ReportLab) ----------------
def _header_footer(canvas, doc, subtitle):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 16)
    canvas.setFillColor(BC_GREEN_DARK)
    canvas.drawString(15 * mm, 283 * mm, "BlotterCast")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.Color(90 / 255, 110 / 255, 90 / 255))
    canvas.drawString(15 * mm, 277 * mm, "Barangay Mapulang Lupa, Pandi, Bulacan")
    if subtitle:
        canvas.drawString(15 * mm, 272 * mm, subtitle)
    canvas.setStrokeColor(BC_GREEN)
    canvas.setLineWidth(0.6 * mm / 2)
    canvas.line(15 * mm, 266 * mm, 195 * mm, 266 * mm)

    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(colors.Color(140 / 255, 140 / 255, 140 / 255))
    footer_text = f"Generated {datetime.now().strftime('%B %d, %Y %I:%M %p')}  |  Page {doc.page}"
    canvas.drawCentredString(105 * mm, 10 * mm, footer_text)
    canvas.restoreState()


def _new_pdf_buffer(subtitle):
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, topMargin=38 * mm, bottomMargin=20 * mm, leftMargin=15 * mm, rightMargin=15 * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    template = PageTemplate(id="main", frames=[frame], onPage=lambda c, d: _header_footer(c, d, subtitle))
    doc.addPageTemplates([template])
    return buf, doc


def _heading_style():
    return ParagraphStyle("Heading", fontName="Helvetica-Bold", fontSize=12, textColor=BC_GREEN_DARK, spaceAfter=4)


def _kv_style():
    return ParagraphStyle("KV", fontName="Helvetica", fontSize=9.5, spaceAfter=2)


def _kv_line(label, value):
    return Paragraph(f"<b>{label}</b> {value}", _kv_style())


def _data_table(headers, rows, col_widths):
    th_style = ParagraphStyle(
        "ReportTableTh",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0,
        wordWrap="CJK",
    )
    td_style = ParagraphStyle(
        "ReportTableTd",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.Color(30 / 255, 30 / 255, 30 / 255),
        alignment=0,
        wordWrap="CJK",
    )

    def _to_flowable(val, style):
        if isinstance(val, Paragraph):
            return val
        s = html.escape(str(val) if val is not None else "")
        return Paragraph(s, style)

    wrapped_headers = [_to_flowable(h, th_style) for h in headers]
    wrapped_rows = [
        [_to_flowable(cell, td_style) for cell in row]
        for row in rows
    ]
    table_data = [wrapped_headers] + wrapped_rows

    t = Table(table_data, colWidths=[w * mm for w in col_widths], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BC_GREEN_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.Color(200 / 255, 200 / 255, 200 / 255)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), BC_GREEN_PALE))
    t.setStyle(TableStyle(style))
    return t


def _build_incident_summary_pdf(from_date, to_date, zone):
    q = Incident.query.filter(Incident.incident_date.between(parse_date(from_date), parse_date(to_date)))
    if zone:
        q = q.filter(Incident.zone_id == zone)
    rows = q.order_by(Incident.incident_date).all()

    by_category, by_status = {}, {}
    for r in rows:
        by_category[r.category] = by_category.get(r.category, 0) + 1
        by_status[r.status] = by_status.get(r.status, 0) + 1
    by_category = dict(sorted(by_category.items(), key=lambda kv: -kv[1]))

    buf, doc = _new_pdf_buffer("Incident Summary Report")
    story = [
        _kv_line("Period:", f"{from_date} to {to_date}" + (f"   ·   Zone: {zone}" if zone else "   ·   All Zones")),
        _kv_line("Total Incidents:", str(len(rows))),
        Spacer(1, 8),
        Paragraph("Status Breakdown", _heading_style()),
    ]
    for status, c in by_status.items():
        story.append(_kv_line(f"{status}:", str(c)))
    story += [Spacer(1, 8), Paragraph("Category Breakdown", _heading_style())]
    for cat, c in by_category.items():
        story.append(_kv_line(f"{cat}:", str(c)))
    story += [Spacer(1, 8), Paragraph("Incident Log", _heading_style())]
    table_rows = [[r.report_no or "", r.incident_date.isoformat() if r.incident_date else "", r.zone_id or "", r.category or "", r.priority or "", r.status or ""] for r in rows]
    story.append(_data_table(["Report No.", "Date", "Zone", "Category", "Priority", "Status"], table_rows, [30, 24, 18, 45, 22, 41]))

    doc.build(story)
    return buf.getvalue()


def _build_settlement_compliance_pdf():
    rows = Settlement.query.order_by(Settlement.date_filed.desc()).all()
    by_status = {}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    buf, doc = _new_pdf_buffer("Settlement Compliance Report")
    story = [_kv_line("Total Settlement Cases:", str(len(rows))), Spacer(1, 8), Paragraph("Status Breakdown", _heading_style())]
    for s, c in by_status.items():
        story.append(_kv_line(f"{s}:", str(c)))
    story += [Spacer(1, 8), Paragraph("Case Log", _heading_style())]
    table_rows = [[r.case_no or "", r.case_title or "", r.nature or "", r.date_filed.isoformat() if r.date_filed else "", r.status or ""] for r in rows]
    # Proportional column widths across 180mm printable width:
    # Case No.: 15% (27mm), Case Title: 35% (63mm), Nature: 18% (32.4mm), Date Filed: 17% (30.6mm), Status: 15% (27mm)
    story.append(_data_table(["Case No.", "Case Title", "Nature", "Date Filed", "Status"], table_rows, [27, 63, 32.4, 30.6, 27]))

    doc.build(story)
    return buf.getvalue()


def _build_blotter_summary_pdf(from_date, to_date, zone=None):
    q = BlotterRecord.query.filter(BlotterRecord.date_filed.between(parse_date(from_date), parse_date(to_date)))
    if zone:
        q = q.filter(BlotterRecord.zone_id == zone)
    rows = q.order_by(BlotterRecord.date_filed.desc()).all()

    by_status = {}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    buf, doc = _new_pdf_buffer("Blotter Summary Report")
    story = [
        _kv_line("Period:", f"{from_date} to {to_date}" + (f"   ·   Zone: {zone}" if zone else "   ·   All Zones")),
        _kv_line("Total Blotter Records:", str(len(rows))),
        Spacer(1, 8),
        Paragraph("Status Breakdown", _heading_style()),
    ]
    for status, c in by_status.items():
        story.append(_kv_line(f"{status}:", str(c)))
    story += [Spacer(1, 8), Paragraph("Blotter Log", _heading_style())]
    table_rows = [
        [
            r.docket_no or "",
            r.date_filed.isoformat() if r.date_filed else "",
            r.complainant or "",
            r.respondent or "",
            r.nature or "",
            r.status or "",
        ]
        for r in rows
    ]
    story.append(_data_table(["Docket No.", "Date Filed", "Complainant", "Respondent", "Nature", "Status"], table_rows, [28, 22, 38, 38, 30, 24]))

    doc.build(story)
    return buf.getvalue()


def _build_trend_analysis_pdf(year):
    from sqlalchemy import extract, func
    monthly = (
        db.session.query(extract("month", Incident.incident_date).label("m"), func.count().label("c"))
        .filter(extract("year", Incident.incident_date) == year).group_by("m").order_by("m").all()
    )
    cats = (
        db.session.query(Incident.category, func.count().label("c"))
        .filter(extract("year", Incident.incident_date) == year)
        .group_by(Incident.category).order_by(func.count().desc()).all()
    )

    buf, doc = _new_pdf_buffer(f"Trend Analysis Report - {year}")
    story = [Paragraph("Monthly Incident Count", _heading_style())]
    story.append(_data_table(["Month", "Incidents"], [[MONTHS[int(r.m) - 1], str(r.c)] for r in monthly], [90, 90]))
    story += [Spacer(1, 10), Paragraph("Category Breakdown", _heading_style())]
    story.append(_data_table(["Category", "Incidents"], [[r.category, str(r.c)] for r in cats], [90, 90]))

    doc.build(story)
    return buf.getvalue()


def _build_predictive_risk_pdf():
    run = MlRun.query.order_by(MlRun.id.desc()).first()
    buf, doc = _new_pdf_buffer("Predictive Risk Assessment")
    if not run:
        story = [Paragraph(
            "No trained model run found yet. Visit the Predictions page to train a model, "
            "then regenerate this report.", _kv_style()
        )]
        doc.build(story)
        return buf.getvalue()

    hotspots = json.loads(run.hotspots_json)
    metrics = json.loads(run.occurrence_metrics_json)
    active = run.active_occurrence_model

    story = [_kv_line("Active Model:", active.replace("_", " ").title())]
    if active in metrics:
        m = metrics[active]
        story.append(_kv_line(
            "Accuracy / AUC / F1:",
            f"{round(m.get('accuracy', 0) * 100, 1)}%  /  {m.get('auc', '—')}  /  {round(m.get('f1', 0) * 100, 1)}%",
        ))
    story.append(_kv_line("Trained On:", f"{run.record_count} records at {run.trained_at}"))
    story += [Spacer(1, 8), Paragraph("Zone Risk Ranking", _heading_style())]
    table_rows = [
        [h.get("zone", ""), f"{round(h.get('meanDailyProb', 0) * 100, 1)}%", str(h.get("expectedCount7d", "")),
         h.get("topCategory", ""), h.get("peakWindow", "")]
        for h in hotspots
    ]
    story.append(_data_table(["Zone", "Daily Prob.", "Expected/7d", "Top Category", "Peak Window"], table_rows, [25, 25, 25, 55, 50]))

    doc.build(story)
    return buf.getvalue()


def _log_report(report_type, from_date, to_date, fmt, file_path):
    entry = GeneratedReport(
        report_type=report_type, generated_by=session.get("full_name", "System"),
        period_from=parse_date(from_date), period_to=parse_date(to_date), format=fmt, file_path=file_path,
    )
    db.session.add(entry)
    db.session.commit()


def _generate():
    d = request.get_json(silent=True) or {}
    report_type = d.get("type") or "Incident Summary Report"
    from_date = d.get("from") or ph_today().replace(day=1).strftime("%Y-%m-%d")
    to_date = d.get("to") or ph_today().strftime("%Y-%m-%d")
    zone = d.get("zone") or None
    fmt = d.get("format") or "pdf"
    year = from_date[:4]

    slug = re.sub(r"[^a-z0-9]+", "-", report_type.lower()).strip("-")
    ext = "csv" if fmt == "excel" else "pdf"
    filename = f"{slug}-{ph_now().strftime('%Y%m%d-%H%M%S')}.{ext}"
    file_path = os.path.join(REPORTS_DIR, filename)

    if fmt == "excel":
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([report_type, "Barangay Mapulang Lupa, Pandi, Bulacan", f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
            w.writerow([])
            if report_type in ("Incident Summary Report", "Predictive Risk Assessment", "Patrol Deployment Plan"):
                q = Incident.query.filter(Incident.incident_date.between(parse_date(from_date), parse_date(to_date)))
                if zone:
                    q = q.filter(Incident.zone_id == zone)
                w.writerow(["Report No.", "Date", "Zone", "Category", "Priority", "Status"])
                for r in q.order_by(Incident.incident_date).all():
                    w.writerow([r.report_no, r.incident_date, r.zone_id, r.category, r.priority, r.status])
            elif report_type == "Settlement Compliance Report":
                w.writerow(["Case No.", "Case Title", "Nature", "Date Filed", "Status"])
                for r in Settlement.query.order_by(Settlement.date_filed.desc()).all():
                    w.writerow([r.case_no, r.case_title, r.nature, r.date_filed, r.status])
            elif report_type in ("Blotter Summary Report", "Blotter Report"):
                q = BlotterRecord.query.filter(BlotterRecord.date_filed.between(parse_date(from_date), parse_date(to_date)))
                if zone:
                    q = q.filter(BlotterRecord.zone_id == zone)
                w.writerow(["Docket No.", "Date Filed", "Complainant", "Respondent", "Nature", "Case Type", "Status"])
                for r in q.order_by(BlotterRecord.date_filed.desc()).all():
                    w.writerow([r.docket_no, r.date_filed, r.complainant, r.respondent, r.nature, r.case_type, r.status])
            elif report_type in ("Trend Analysis Report", "Comparative Period Report"):
                from sqlalchemy import extract, func
                w.writerow(["Month", "Incident Count"])
                monthly = (
                    db.session.query(extract("month", Incident.incident_date).label("m"), func.count().label("c"))
                    .filter(extract("year", Incident.incident_date) == year).group_by("m").order_by("m").all()
                )
                for r in monthly:
                    w.writerow([MONTHS[int(r.m) - 1], r.c])
            else:
                w.writerow(["No data available for this report type yet."])
    else:
        if report_type == "Settlement Compliance Report":
            pdf_bytes = _build_settlement_compliance_pdf()
        elif report_type in ("Blotter Summary Report", "Blotter Report"):
            pdf_bytes = _build_blotter_summary_pdf(from_date, to_date, zone)
        elif report_type in ("Trend Analysis Report", "Comparative Period Report"):
            pdf_bytes = _build_trend_analysis_pdf(year)
        elif report_type in ("Predictive Risk Assessment", "Patrol Deployment Plan"):
            pdf_bytes = _build_predictive_risk_pdf()
        else:
            pdf_bytes = _build_incident_summary_pdf(from_date, to_date, zone)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

    _log_report(report_type, from_date, to_date, "Excel" if fmt == "excel" else "PDF", filename)
    return jsonify({"ok": True, "file": filename, "url": f"api/reports.php?action=download&file={filename}"})


def _download():
    filename = os.path.basename(request.args.get("file", ""))
    path = os.path.join(REPORTS_DIR, filename)
    if not filename or not os.path.isfile(path):
        return "Report not found.", 404
    mimetype = "text/csv" if filename.endswith(".csv") else "application/pdf"
    return send_file(path, mimetype=mimetype, as_attachment=True, download_name=filename)
