import pytest

from mediapulse.config import Settings
from mediapulse.notify import email as email_module
from mediapulse.notify.email import EmailNotConfigured, send_brief_email, send_email


class FakeSmtpConnection:
    def __init__(self):
        self.started_tls = False
        self.login_calls = []
        self.sent_messages = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user, password):
        self.login_calls.append((user, password))

    def send_message(self, msg):
        self.sent_messages.append(msg)


def _settings(**overrides):
    defaults = dict(
        smtp_host="smtp.example.bw", smtp_port=587, smtp_user="brief@mediapulse.bw",
        smtp_password="secret", smtp_from="brief@mediapulse.bw", smtp_use_tls=True,
    )
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def test_send_brief_email_builds_and_sends_message_with_pdf(tmp_path):
    pdf_path = tmp_path / "brief.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")
    connection = FakeSmtpConnection()

    send_brief_email(
        to="client@orange.bw", subject="Daily Brief", html_body="<p>Hi</p>",
        pdf_path=str(pdf_path), settings=_settings(), smtp_factory=lambda: connection,
    )

    assert connection.started_tls is True
    assert connection.login_calls == [("brief@mediapulse.bw", "secret")]
    assert len(connection.sent_messages) == 1
    msg = connection.sent_messages[0]
    assert msg["To"] == "client@orange.bw"
    assert msg["Subject"] == "Daily Brief"
    attachments = [part for part in msg.walk() if part.get_filename() == "brief.pdf"]
    assert len(attachments) == 1


def test_send_brief_email_without_pdf_attachment():
    connection = FakeSmtpConnection()
    send_brief_email(
        to="client@orange.bw", subject="Daily Brief", html_body="<p>Hi</p>",
        settings=_settings(), smtp_factory=lambda: connection,
    )
    msg = connection.sent_messages[0]
    assert not [p for p in msg.walk() if p.get_filename()]


def test_send_brief_email_skips_login_when_no_smtp_user():
    connection = FakeSmtpConnection()
    send_brief_email(
        to="client@orange.bw", subject="Daily Brief", html_body="<p>Hi</p>",
        settings=_settings(smtp_user=""), smtp_factory=lambda: connection,
    )
    assert connection.login_calls == []


def test_send_brief_email_skips_tls_when_disabled():
    connection = FakeSmtpConnection()
    send_brief_email(
        to="client@orange.bw", subject="Daily Brief", html_body="<p>Hi</p>",
        settings=_settings(smtp_use_tls=False), smtp_factory=lambda: connection,
    )
    assert connection.started_tls is False


def test_send_email_skips_starttls_when_using_implicit_ssl(monkeypatch):
    # Port-465-style host: the connection is already encrypted, calling
    # starttls() on it would be wrong (and most servers reject it).
    connection = FakeSmtpConnection()
    monkeypatch.setattr(email_module.smtplib, "SMTP_SSL", lambda *a, **kw: connection)
    send_email(
        to="client@orange.bw", subject="Alert", html_body="<p>Hi</p>",
        settings=_settings(smtp_port=465, smtp_use_tls=True, smtp_use_ssl=True),
    )
    assert connection.started_tls is False
    assert connection.sent_messages


def test_send_email_uses_smtp_ssl_constructor_when_use_ssl(monkeypatch):
    calls = []

    def fake_smtp_ssl(host, port, timeout=None):
        calls.append((host, port))
        return FakeSmtpConnection()

    def fake_smtp(host, port, timeout=None):
        raise AssertionError("should not use plain SMTP when smtp_use_ssl=True")

    monkeypatch.setattr(email_module.smtplib, "SMTP_SSL", fake_smtp_ssl)
    monkeypatch.setattr(email_module.smtplib, "SMTP", fake_smtp)

    send_email(
        to="client@orange.bw", subject="Alert", html_body="<p>Hi</p>",
        settings=_settings(smtp_host="mail.ebw.co.bw", smtp_port=465, smtp_use_ssl=True),
    )

    assert calls == [("mail.ebw.co.bw", 465)]


def test_send_email_uses_plain_smtp_constructor_by_default(monkeypatch):
    calls = []

    def fake_smtp(host, port, timeout=None):
        calls.append((host, port))
        return FakeSmtpConnection()

    monkeypatch.setattr(email_module.smtplib, "SMTP", fake_smtp)

    send_email(
        to="client@orange.bw", subject="Alert", html_body="<p>Hi</p>",
        settings=_settings(smtp_host="smtp.example.bw", smtp_port=587, smtp_use_ssl=False),
    )

    assert calls == [("smtp.example.bw", 587)]


def test_send_brief_email_raises_when_smtp_not_configured():
    with pytest.raises(EmailNotConfigured):
        send_brief_email(
            to="client@orange.bw", subject="Daily Brief", html_body="<p>Hi</p>",
            settings=_settings(smtp_host=""),
        )
