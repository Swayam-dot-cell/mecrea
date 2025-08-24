# dynamic_report/build_report.py
import json
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

ROOT = Path(".")
RED = ROOT / "red_report.json"
BLUE = ROOT / "blue_report.json"
LOGS = ROOT / "all_logs.json"
AI = ROOT / "ai_insights.json"
OUT_JSON = ROOT / "final_report.json"
OUT_PDF = ROOT / "final_report.pdf"

def read_json(p: Path):
    if p.exists():
        return json.loads(p.read_text())
    return {}

def build_json_report():
    red = read_json(RED)
    blue = read_json(BLUE)
    logs = read_json(LOGS)
    ai = read_json(AI)

    # aggregate a number of fields (≥ 10)
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "target_url": red.get("target") if red else None,
        "red_team_tool_count": len(red.get("tools", [])) if red else 0,
        "blue_team_action_count": len(blue.get("actions", [])) if blue else 0,
        "total_log_events": len(logs) if isinstance(logs, list) else 0,
        "unique_flagged_ips": ai.get("flagged_ips", []) if ai else [],
        "detected_vectors": ai.get("detected_vectors", []) if ai else [],
        "ai_recommendations": ai.get("recommended_actions", []) if ai else [],
        "attack_summary": ai.get("summary", "") if ai else "",
        "attack_timestamps": [entry.get("timestamp") for entry in logs[:10]] if isinstance(logs, list) else [],
        "red_report": red,
        "blue_report": blue,
        "raw_logs_sample": logs[:20] if isinstance(logs, list) else logs,
        "ai_raw": ai
    }

    OUT_JSON.write_text(json.dumps(report, indent=2))
    print("Wrote final_report.json")
    return report

def build_pdf(report: dict):
    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=60)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("QuantumLock — Assessment Report", styles["Title"]))
    story.append(Spacer(1, 8))
    meta = f"Generated: {report.get('generated_at')} — Target: {report.get('target_url')}"
    story.append(Paragraph(meta, styles["Normal"]))
    story.append(Spacer(1, 12))

    # Attack summary
    story.append(Paragraph("Executive Summary", styles["Heading2"]))
    story.append(Paragraph(report.get("attack_summary", "No summary available."), styles["Normal"]))
    story.append(Spacer(1, 12))

    # Key metrics table
    story.append(Paragraph("Key Metrics", styles["Heading2"]))
    table_data = [
        ["Total Log Events", str(report.get("total_log_events"))],
        ["Red Team Tools Used", str(report.get("red_team_tool_count"))],
        ["Blue Team Actions", str(report.get("blue_team_action_count"))],
        ["Unique Flagged IPs", ", ".join(report.get("unique_flagged_ips")[:5])],
        ["Detected Vectors", ", ".join(report.get("detected_vectors")[:5])]
    ]
    t = Table(table_data, hAlign="LEFT")
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica')
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # AI Recommendations (list)
    recs = report.get("ai_recommendations", [])
    story.append(Paragraph("AI Recommendations", styles["Heading2"]))
    if recs:
        for r in recs:
            action = r.get("action") if isinstance(r, dict) else str(r)
            reason = r.get("reason", "")
            priority = r.get("priority", "")
            story.append(Paragraph(f"- {action} (Priority: {priority})", styles["Normal"]))
            if reason:
                story.append(Paragraph(f"  Reason: {reason}", styles["Italic"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No AI recommendations present.", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Sample logs table (first 10 entries)
    story.append(Paragraph("Sample Log Events", styles["Heading2"]))
    logs = report.get("raw_logs_sample", [])[:10]
    if logs:
        for idx, entry in enumerate(logs, start=1):
            story.append(Paragraph(f"{idx}. {entry.get('timestamp')} — {entry.get('event_type')}: {entry.get('details')}", styles["Normal"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No sample logs available.", styles["Normal"]))

    # Finish
    doc.build(story)
    print("Wrote final_report.pdf")

if __name__ == "__main__":
    report = build_json_report()
    build_pdf(report)
