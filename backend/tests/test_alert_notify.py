from mediapulse.config import Settings
from mediapulse.models import Alert, AlertType
from mediapulse.notify.alerts import render_alert_digest_html, send_alert_digest


class FakeSmtpConnection:
    def __init__(self):
        self.sent_messages = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        pass

    def send_message(self, msg):
        self.sent_messages.append(msg)


def _settings(**overrides):
    defaults = dict(smtp_host="smtp.example.bw", smtp_port=587, smtp_user="", smtp_password="",
                     smtp_from="alerts@mediapulse.bw", smtp_use_tls=False)
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def _make_alert(tenant_id, alert_type, message):
    return Alert(tenant_id=tenant_id, article_id=None, alert_type=alert_type, message=message)


def test_render_alert_digest_includes_all_alerts():
    alerts = [
        _make_alert("t1", AlertType.negative_sentiment, "Negative story about Orange."),
        _make_alert("t1", AlertType.regulator_announcement, "BOCRA news."),
    ]
    html = render_alert_digest_html("Orange Botswana", alerts)

    assert "Orange Botswana" in html
    assert "Negative story about Orange." in html
    assert "BOCRA news." in html
    assert "Negative Coverage" in html
    assert "Regulator Announcement" in html


def test_send_alert_digest_sends_one_email_for_all_alerts():
    connection = FakeSmtpConnection()
    alerts = [
        _make_alert("t1", AlertType.negative_sentiment, "Negative story."),
        _make_alert("t1", AlertType.volume_spike, "Spike detected."),
    ]

    send_alert_digest(tenant_name="Orange Botswana", alerts=alerts, to="admin@orange.bw",
                       settings=_settings(), smtp_factory=lambda: connection)

    assert len(connection.sent_messages) == 1
    msg = connection.sent_messages[0]
    assert msg["To"] == "admin@orange.bw"
    assert "(2)" in msg["Subject"]


def test_send_alert_digest_skips_send_when_no_alerts():
    connection = FakeSmtpConnection()
    send_alert_digest(tenant_name="Orange Botswana", alerts=[], to="admin@orange.bw",
                       settings=_settings(), smtp_factory=lambda: connection)
    assert connection.sent_messages == []
