"""Digest email for pending `Alert` rows — one email listing every unsent
alert for a tenant, rather than spamming one message per alert.
"""
from __future__ import annotations

from ..config import Settings
from ..models import Alert, AlertType
from .email import send_email

_TYPE_LABELS = {
    AlertType.negative_sentiment: "Negative Coverage",
    AlertType.competitor_launch: "Competitor Launch",
    AlertType.regulator_announcement: "Regulator Announcement",
    AlertType.volume_spike: "Volume Spike",
}


def render_alert_digest_html(tenant_name: str, alerts: list[Alert]) -> str:
    rows = "".join(
        f'<li style="margin-bottom:10px;"><strong>{_TYPE_LABELS.get(alert.alert_type, alert.alert_type.value)}'
        f'</strong><br><span style="color:#555;">{alert.message}</span></li>'
        for alert in alerts
    )
    return f"""<!doctype html>
<html><body style="font-family:Arial,Helvetica,sans-serif;color:#151515;padding:16px;">
<h2 style="font-size:16px;">MediaPulse Alerts &mdash; {tenant_name}</h2>
<ul style="font-size:13px;padding-left:18px;">{rows}</ul>
</body></html>"""


def send_alert_digest(
    *,
    tenant_name: str,
    alerts: list[Alert],
    to: str,
    settings: Settings | None = None,
    smtp_factory=None,
) -> None:
    if not alerts:
        return
    html = render_alert_digest_html(tenant_name, alerts)
    send_email(
        to=to,
        subject=f"MediaPulse Alerts — {tenant_name} ({len(alerts)})",
        html_body=html,
        settings=settings,
        smtp_factory=smtp_factory,
    )
