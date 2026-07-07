"""Seeds realistic-looking classified articles, sources, and users for the
Orange Botswana demo tenant so the API/dashboard has something to show
without needing a real Anthropic API key or live ingestion run.

Not meant for production use — this is dev/demo fixture data only.
"""
from __future__ import annotations

import datetime as dt
import hashlib

from sqlalchemy.orm import Session

from ..auth import hash_password
from ..ingestion.dedupe import assign_story_cluster
from ..models import (
    Article,
    ArticleStatus,
    Classification,
    ClassificationStatus,
    SentimentLabel,
    Source,
    SourceType,
    Tenant,
    ThreatTag,
    Topic,
    User,
    UserRole,
)

DEMO_USERS = [
    ("admin@orange.bw", UserRole.admin, "Agency Coordinator"),
    ("analyst@orange.bw", UserRole.analyst, "Media Strategist"),
    ("client@orange.bw", UserRole.client_viewer, "Orange CMO"),
]
DEMO_PASSWORD = "demo-password-123"

_STORIES = [
    dict(topic="Orange Botswana (brand watch)", publication="Mmegi Online", byline="By Staff Reporter",
         title="Orange Botswana expands 4G coverage to Ghanzi", category="telco",
         sentiment_overall=SentimentLabel.positive,
         sentiment_by_brand={"Orange Botswana": "positive"}, threat_tag=ThreatTag.opportunity,
         summary="Orange Botswana switched on new 4G towers in Ghanzi district, extending rural coverage.",
         why_it_matters="Positive rural-connectivity story reinforces Orange's network-investment narrative.",
         relevance=0.9),
    dict(topic="Mascom & BTC (competitors)", publication="The Voice", byline="By Business Desk",
         title="BTC cuts data bundle prices by 20%", category="telco",
         sentiment_overall=SentimentLabel.negative,
         sentiment_by_brand={"BTC": "negative", "Orange Botswana": "neutral"}, threat_tag=ThreatTag.risk,
         summary="BTC announced a 20% cut to data bundle prices, intensifying price competition.",
         why_it_matters="A direct value-for-money attack line competitors may use against Orange.",
         relevance=0.85),
    dict(topic="Mascom & BTC (competitors)", publication="Daily News", byline="By Correspondent",
         title="Mascom launches new small business fibre package", category="telco",
         sentiment_overall=SentimentLabel.neutral,
         sentiment_by_brand={"Mascom": "neutral"}, threat_tag=ThreatTag.monitor,
         summary="Mascom introduced a fibre package targeted at small and medium enterprises.",
         why_it_matters="Competitor product launch worth tracking for the SME segment.",
         relevance=0.6),
    dict(topic="BOCRA & regulation", publication="Botswana Gazette", byline="By Business Reporter",
         title="BOCRA proposes new data quality-of-service rules", category="regulator",
         sentiment_overall=SentimentLabel.neutral,
         sentiment_by_brand={}, threat_tag=ThreatTag.monitor,
         summary="The regulator published draft rules on minimum data service quality standards.",
         why_it_matters="New compliance obligations could affect network investment priorities.",
         relevance=0.7),
    dict(topic="Botswana business & fintech", publication="Mmegi Online", byline="By Fintech Desk",
         title="Orange Money crosses one million active users", category="fintech",
         sentiment_overall=SentimentLabel.positive,
         sentiment_by_brand={"Orange Botswana": "positive"}, threat_tag=ThreatTag.opportunity,
         summary="Orange Money reached one million active users, cementing its mobile money lead.",
         why_it_matters="Strong growth milestone reinforcing Orange's fintech leadership position.",
         relevance=0.95),
    dict(topic="Botswana business & fintech", publication="The Voice", byline="By Staff Reporter",
         title="Smega expands merchant network in Francistown", category="fintech",
         sentiment_overall=SentimentLabel.neutral,
         sentiment_by_brand={"BTC": "neutral"}, threat_tag=ThreatTag.monitor,
         summary="BTC's Smega mobile money service added new merchant partners in Francistown.",
         why_it_matters="Competitor mobile-money expansion in a key regional market.",
         relevance=0.55),
    dict(topic="Orange Botswana (brand watch)", publication="Botswana Gazette", byline="By Sports Desk",
         title="Orange Digital Center hosts youth coding bootcamp", category="csr",
         sentiment_overall=SentimentLabel.positive,
         sentiment_by_brand={"Orange Botswana": "positive"}, threat_tag=ThreatTag.opportunity,
         summary="The Orange Digital Center ran a two-week coding bootcamp for young Batswana developers.",
         why_it_matters="Strong CSR/tech-skills story for the brand's community engagement pillar.",
         relevance=0.8),
]


def _content_hash(title: str, publication: str, day: dt.date) -> str:
    return hashlib.sha256(f"{title}|{publication}|{day.isoformat()}".encode()).hexdigest()


def seed_demo_data(session: Session, tenant: Tenant) -> None:
    topics_by_label = {t.label: t for t in session.query(Topic).filter_by(tenant_id=tenant.id).all()}

    # Sources with a mix of healthy/unhealthy states for the Admin page.
    if not session.query(Source).join(Topic).filter(Topic.tenant_id == tenant.id).first():
        now = dt.datetime.now(dt.timezone.utc)
        session.add(Source(
            topic_id=topics_by_label["Orange Botswana (brand watch)"].id,
            name="Mmegi Online", type=SourceType.rss, url="https://mmegi.bw/feed.xml",
            last_fetched_at=now, last_success_at=now, consecutive_error_count=0,
        ))
        session.add(Source(
            topic_id=topics_by_label["Mascom & BTC (competitors)"].id,
            name="Botswana Gazette (PressReader)", type=SourceType.pressreader,
            config={"publication_id": "bw-gazette"},
            last_fetched_at=now, consecutive_error_count=4,
            last_error="PressReader client not configured — set up credentials and pass a "
                       "PressReaderClient implementation (see ingestion/pressreader.py).",
        ))

    # Users for browser login testing.
    for email, role, name in DEMO_USERS:
        if not session.query(User).filter_by(email=email).first():
            session.add(User(
                tenant_id=tenant.id, email=email, name=name, role=role,
                hashed_password=hash_password(DEMO_PASSWORD),
            ))

    today = dt.date.today()
    for day_offset in range(14):
        day = today - dt.timedelta(days=day_offset)
        for story in _STORIES[(day_offset) % len(_STORIES):(day_offset % len(_STORIES)) + 2] or _STORIES[:2]:
            content_hash = _content_hash(story["title"], story["publication"], day)
            if session.query(Article).filter_by(tenant_id=tenant.id, content_hash=content_hash).first():
                continue
            topic = topics_by_label[story["topic"]]
            published_at = dt.datetime.combine(day, dt.time(8, 0), tzinfo=dt.timezone.utc)
            article = Article(
                tenant_id=tenant.id, topic_id=topic.id, publication=story["publication"],
                title=story["title"], byline=story["byline"], published_at=published_at,
                published_at_confidence="high", fetched_at=published_at, content_hash=content_hash,
                raw_text=story["summary"] + " " + story["why_it_matters"],
                status=ArticleStatus.classified,
            )
            session.add(article)
            session.flush()
            assign_story_cluster(session, article)
            session.add(Classification(
                article_id=article.id, tenant_id=tenant.id, status=ClassificationStatus.success,
                model_used="claude-sonnet-4-6", relevance_score=story["relevance"],
                category=story["category"], sentiment_overall=story["sentiment_overall"],
                sentiment_by_brand=story["sentiment_by_brand"],
                entities={"brands": list(story["sentiment_by_brand"].keys()), "people": [],
                          "organisations": [], "products": [], "events": [], "locations": ["Gaborone"]},
                summary_exec=story["summary"], key_quotes=[], why_it_matters=story["why_it_matters"],
                threat_tag=story["threat_tag"], threat_rationale=story["why_it_matters"],
                tokens_in=400, tokens_out=180, cost_usd=0.004, classified_at=published_at,
            ))

    # A couple of pending/error rows so the KPI tiles show something realistic.
    pending_hash = _content_hash("Pending story awaiting classification", "Mmegi Online", today)
    if not session.query(Article).filter_by(tenant_id=tenant.id, content_hash=pending_hash).first():
        now = dt.datetime.now(dt.timezone.utc)
        session.add(Article(
            tenant_id=tenant.id, topic_id=topics_by_label["Orange Botswana (brand watch)"].id,
            publication="Mmegi Online", title="Pending story awaiting classification",
            published_at=now, fetched_at=now, content_hash=pending_hash,
            raw_text="Freshly ingested, not yet classified.", status=ArticleStatus.new,
        ))

    error_hash = _content_hash("Story that failed classification", "The Voice", today)
    if not session.query(Article).filter_by(tenant_id=tenant.id, content_hash=error_hash).first():
        now = dt.datetime.now(dt.timezone.utc)
        article = Article(
            tenant_id=tenant.id, topic_id=topics_by_label["BOCRA & regulation"].id,
            publication="The Voice", title="Story that failed classification",
            published_at=now, fetched_at=now, content_hash=error_hash,
            raw_text="Classification failed after retries.", status=ArticleStatus.error,
        )
        session.add(article)
        session.flush()
        session.add(Classification(
            article_id=article.id, tenant_id=tenant.id, status=ClassificationStatus.failed,
            attempt_count=5, error_message="Could not resolve authentication method.",
        ))
