"""
Report Generation Service.
Generates structured JSON and clean, styled HTML analysis reports
including plain-language limitations, model version, and exact scoring breakdowns.
"""

from typing import Dict, Any
from backend.app.models.detection import CheckResponse


def generate_json_report(check: CheckResponse, title: str = "AI Content Analysis Report") -> Dict[str, Any]:
    return {
        "title": title,
        "analysis_id": check.analysis_id,
        "document_id": check.document_id,
        "synthetic_pattern_confidence": check.synthetic_pattern_confidence,
        "label": check.label,
        "classification_band": check.classification_band,
        "uncertainty_interval": check.uncertainty_interval.model_dump(),
        "abstain_band_thresholds": check.abstain_band_thresholds,
        "reliability_flag": check.reliability_flag,
        "length_warning": check.length_warning,
        "stats": check.stats,
        "top_contributing_signals": [s.model_dump() for s in check.top_contributing_signals],
        "paragraphs": [p.model_dump() for p in check.paragraphs],
        "limitations": check.limitations.model_dump(),
    }


def generate_html_report(check: CheckResponse, title: str = "AI Content Analysis Report") -> str:
    # Build signals table rows
    signals_rows = ""
    for s in check.top_contributing_signals:
        direction_badge = (
            '<span style="color: #b91c1c; font-weight: 600;">Synthetic Indicative</span>'
            if s.direction == "synthetic_indicative"
            else '<span style="color: #047857; font-weight: 600;">Human Indicative</span>'
        )
        signals_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; font-weight: 500;">{s.display_name}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; font-family: monospace;">{s.measured_value}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{direction_badge}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #4b5563;">{s.explanation}</td>
        </tr>
        """

    # Build paragraph and sentence breakdowns
    paragraphs_html = ""
    for p in check.paragraphs:
        score_text = f"{p.synthetic_pattern_confidence:.2f}" if p.synthetic_pattern_confidence is not None else "N/A"
        paragraphs_html += f"""
        <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #e5e7eb; border-radius: 6px; background-color: #f9fafb;">
            <div style="font-weight: 600; margin-bottom: 8px; color: #111827;">
                Paragraph {p.index + 1} — Score: {score_text} ({p.classification_band})
            </div>
            <div style="line-height: 1.6; color: #374151;">
        """
        for s in p.sentences:
            if s.is_elevated_homogeneity:
                paragraphs_html += f'<span style="background-color: #fee2e2; border-bottom: 2px solid #ef4444; padding: 2px 4px; border-radius: 2px;" title="Local indicator: {s.indicator_score}">{s.text} </span>'
            else:
                paragraphs_html += f'<span>{s.text} </span>'
        paragraphs_html += "</div></div>"

    # Limitations items
    limitations_items = "".join(
        f'<li style="margin-bottom: 6px;">{lim}</li>'
        for lim in check.limitations.plain_language_limitations
    )

    badge_color = "#2563eb"
    if check.classification_band == "SYNTHETIC_INDICATIVE":
        badge_color = "#dc2626"
    elif check.classification_band == "HUMAN_TYPICAL":
        badge_color = "#16a34a"
    elif check.classification_band == "INCONCLUSIVE":
        badge_color = "#d97706"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1f2937;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
            line-height: 1.5;
        }}
        h1, h2, h3 {{ color: #111827; }}
        .header {{ border-bottom: 2px solid #e5e7eb; padding-bottom: 16px; margin-bottom: 24px; }}
        .summary-card {{
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 28px;
        }}
        .score-badge {{
            display: inline-block;
            background-color: {badge_color};
            color: white;
            font-size: 16px;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 9999px;
            text-transform: uppercase;
        }}
        .limitations-box {{
            background-color: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 16px;
            border-radius: 4px;
            margin-top: 32px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div style="color: #6b7280; font-size: 14px;">
            Analysis ID: {check.analysis_id} &bull; Model Version: {check.limitations.model_version} &bull; Integrity Hash: {check.limitations.model_hash[:16]}...
        </div>
    </div>

    <div class="summary-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <div>
                <span style="font-size: 24px; font-weight: 800; color: #111827;">{check.synthetic_pattern_confidence:.2f}</span>
                <span style="color: #6b7280; font-size: 14px;"> / 1.00 Calibrated Synthetic Confidence</span>
            </div>
            <div>
                <span class="score-badge">{check.label}</span>
            </div>
        </div>
        <p style="margin: 0; color: #4b5563; font-size: 14px;">
            Classification: <strong>{check.classification_band}</strong> (Abstain Band: {check.abstain_band_thresholds['lower']:.2f} &ndash; {check.abstain_band_thresholds['upper']:.2f}) &bull;
            95% Confidence Interval: [{check.uncertainty_interval.lower:.2f}, {check.uncertainty_interval.upper:.2f}] &bull;
            Words: {check.stats['word_count']}
        </p>
        {"<p style='color: #b45309; font-weight: 600; margin-top: 10px;'>" + check.length_warning + "</p>" if check.length_warning else ""}
    </div>

    <h2>Top Contributing Signals</h2>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
        <thead>
            <tr style="background: #f1f5f9; text-align: left; font-size: 13px; color: #475569;">
                <th style="padding: 10px;">Signal</th>
                <th style="padding: 10px;">Value</th>
                <th style="padding: 10px;">Direction</th>
                <th style="padding: 10px;">Scientific Explanation</th>
            </tr>
        </thead>
        <tbody>
            {signals_rows}
        </tbody>
    </table>

    <h2>Content & Sentence Indicators</h2>
    {paragraphs_html}

    <div class="limitations-box">
        <h3 style="margin-top: 0; color: #92400e;">Scientific Limitations & Disclaimer</h3>
        <p style="font-size: 14px; color: #78350f;">{check.limitations.disclaimer}</p>
        <ul style="font-size: 13px; color: #78350f; padding-left: 20px;">
            {limitations_items}
        </ul>
    </div>
</body>
</html>
"""
    return html_content
