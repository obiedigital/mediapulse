"""Renders a `BriefData` + `BriefSynthesisResult` into an email-safe HTML
document (table-based layout, inline styles — no external stylesheet,
since mail clients strip `<link>`/`<style>` support is inconsistent) and,
from that HTML, a PDF via WeasyPrint.

Brand color is read from `tenant.brand_config` so the same template serves
any tenant, not just Orange Botswana (falls back to a neutral default if a
tenant hasn't configured one).
"""
from __future__ import annotations

from jinja2 import Template
from weasyprint import HTML

from ..briefs.aggregate import BriefData
from ..ai.brief_synthesis import BriefSynthesisResult

DEFAULT_BRAND_PRIMARY = "#2a78d6"

# Matches the frontend's dataviz status palette so a Risk/Opportunity/Monitor
# tag reads the same color in the emailed brief as it does on the dashboard.
_THREAT_COLORS = {
    "risk": "#d03b3b",
    "opportunity": "#0ca30c",
    "monitor": "#fab219",
}

METHODOLOGY_NOTE = (
    "Share of voice reflects mentions in ingested and classified coverage only "
    "— it is directional, not a full media-monitoring-universe measurement. "
    "Pillar stories are ranked by AI-assessed relevance to the tenant's watchlist."
)

_TEMPLATE = Template("""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{{ tenant_name }} {{ brief_type_label }} Brief — {{ period_label }}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f3;font-family:Arial,Helvetica,sans-serif;color:#151515;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f3;padding:24px 0;">
<tr><td align="center">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;border:1px solid #e5e5e0;">

<tr><td style="background:{{ brand_primary }};padding:20px 32px;">
  <div style="font-size:20px;font-weight:bold;color:#ffffff;">{{ tenant_name }}</div>
  <div style="font-size:13px;color:#ffffff;opacity:0.85;">{{ brief_type_label }} Media Brief — {{ period_label }}</div>
</td></tr>

<tr><td style="padding:24px 32px 8px;">
  <h2 style="font-size:16px;margin:0 0 8px;">Executive Summary</h2>
  <p style="font-size:14px;line-height:1.5;color:#333;margin:0;">{{ exec_summary }}</p>
  <p style="font-size:12px;color:#888;margin:8px 0 0;">{{ total_coverage_count }} items monitored this period.</p>
</td></tr>

{% for pillar in pillars %}
<tr><td style="padding:16px 32px 8px;">
  <h2 style="font-size:15px;margin:0 0 4px;">{{ pillar.name }}
    <span style="font-weight:normal;color:#888;font-size:12px;">({{ pillar.total_count }} stories)</span>
  </h2>
  {% if pillar.commentary %}<p style="font-size:13px;color:#555;margin:4px 0 10px;">{{ pillar.commentary }}</p>{% endif %}
  {% for story in pillar.top_stories %}
  <div style="border-left:3px solid {{ brand_primary }};padding:2px 0 2px 10px;margin-bottom:8px;">
    <div style="font-size:14px;font-weight:bold;">{{ story.title }}</div>
    <div style="font-size:12px;color:#888;">{{ story.publication }} &middot; {{ story.sentiment }} &middot; {{ story.category }}</div>
  </div>
  {% endfor %}
</td></tr>
{% endfor %}

<tr><td style="padding:16px 32px 8px;">
  <h2 style="font-size:15px;margin:0 0 8px;">Share of Voice</h2>
  {% for brand, count in share_of_voice %}
  <div style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0;border-bottom:1px solid #f0f0ee;">
    <span>{{ brand }}</span><span>{{ count }}</span>
  </div>
  {% endfor %}
</td></tr>

<tr><td style="padding:16px 32px 8px;">
  <h2 style="font-size:15px;margin:0 0 8px;">Sentiment Shifts</h2>
  <p style="font-size:13px;color:#555;margin:0;">{{ sentiment_commentary }}</p>
</td></tr>

<tr><td style="padding:16px 32px 8px;">
  <h2 style="font-size:15px;margin:0 0 8px;">Watch List</h2>
  {% for item in watchlist %}
  <div style="padding:8px 0;border-bottom:1px solid #eee;">
    <span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;color:#fff;background:{{ item.color }};">{{ item.tag_label }}</span>
    <div style="font-size:14px;font-weight:bold;margin-top:4px;">{{ item.title }}</div>
    <div style="font-size:13px;color:#555;">{{ item.action }}</div>
  </div>
  {% else %}
  <p style="font-size:13px;color:#888;">No risk or opportunity items flagged this period.</p>
  {% endfor %}
</td></tr>

<tr><td style="padding:16px 32px;background:#fafafa;font-size:11px;color:#999;">
  {{ methodology_note }}
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
""")


def render_brief_html(data: BriefData, synthesis: BriefSynthesisResult) -> str:
    brand_primary = (data.tenant.brand_config or {}).get("primary", DEFAULT_BRAND_PRIMARY)

    pillars = []
    for pillar in data.pillars:
        stories = []
        for story in pillar.top_stories:
            c = story.classification
            stories.append({
                "title": story.title,
                "publication": story.publication,
                "sentiment": c.sentiment_overall.value if c.sentiment_overall else "n/a",
                "category": c.category or "uncategorized",
            })
        pillars.append({
            "name": pillar.name,
            "total_count": pillar.total_count,
            "commentary": synthesis.pillar_commentary.get(pillar.name, ""),
            "top_stories": stories,
        })

    watchlist = []
    for item in data.watchlist:
        watchlist.append({
            "title": item.article.title,
            "tag_label": item.threat_tag.value.upper(),
            "color": _THREAT_COLORS.get(item.threat_tag.value, "#888888"),
            "action": synthesis.watchlist_actions.get(item.article.id, item.rationale),
        })

    period_label = (
        data.period_start.isoformat()
        if data.period_start == data.period_end
        else f"{data.period_start.isoformat()} to {data.period_end.isoformat()}"
    )

    return _TEMPLATE.render(
        tenant_name=data.tenant.name,
        brief_type_label=data.brief_type.value.capitalize(),
        period_label=period_label,
        exec_summary=synthesis.exec_summary,
        total_coverage_count=data.total_coverage_count,
        pillars=pillars,
        share_of_voice=sorted(data.share_of_voice.items(), key=lambda kv: -kv[1]),
        sentiment_commentary=synthesis.sentiment_commentary,
        watchlist=watchlist,
        methodology_note=METHODOLOGY_NOTE,
        brand_primary=brand_primary,
    )


def render_brief_pdf(html: str, output_path: str) -> None:
    HTML(string=html).write_pdf(output_path)
