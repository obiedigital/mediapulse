"""Email delivery for the Daily Brief — stdlib `smtplib` only, no extra
dependency for something this simple. The SMTP connection is injectable
(`smtp_factory`) so tests exercise message construction and the
TLS/login/send sequence without touching a real server, and the
architecture stays ready for WhatsApp/Slack (a `notify/` package, not a
single `email.py` doing everything) per the product brief's alerting
requirements.
"""
from __future__ import annotations

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Callable

from ..config import Settings, get_settings


class EmailNotConfigured(RuntimeError):
    pass


def _build_message(*, from_addr: str, to: str, subject: str, html_body: str, pdf_path: str | None) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html_body, "html"))
    msg.attach(alt)

    if pdf_path is not None:
        data = Path(pdf_path).read_bytes()
        part = MIMEApplication(data, _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=Path(pdf_path).name)
        msg.attach(part)

    return msg


def send_brief_email(
    *,
    to: str,
    subject: str,
    html_body: str,
    pdf_path: str | None = None,
    settings: Settings | None = None,
    smtp_factory: Callable[[], smtplib.SMTP] | None = None,
) -> None:
    settings = settings or get_settings()
    if not settings.smtp_host:
        raise EmailNotConfigured("SMTP is not configured (MEDIAPULSE_SMTP_HOST is empty).")

    msg = _build_message(from_addr=settings.smtp_from, to=to, subject=subject, html_body=html_body, pdf_path=pdf_path)

    server = smtp_factory() if smtp_factory else smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
    with server as connection:
        if settings.smtp_use_tls:
            connection.starttls()
        if settings.smtp_user:
            connection.login(settings.smtp_user, settings.smtp_password)
        connection.send_message(msg)
