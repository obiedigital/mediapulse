import datetime as dt

from mediapulse.ingestion.dedupe import assign_story_cluster, title_similarity
from mediapulse.models import Article, Topic, TopicKind


def _make_article(session, tenant, topic, title, *, published_at, content_hash):
    article = Article(
        tenant_id=tenant.id,
        topic_id=topic.id,
        publication="Outlet",
        title=title,
        published_at=published_at,
        fetched_at=published_at,
        content_hash=content_hash,
        raw_text="body",
    )
    session.add(article)
    session.flush()
    return article


def test_similar_titles_across_outlets_join_same_cluster(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()

    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    a1 = _make_article(session, tenant, topic, "Orange Botswana launches new data bundle", published_at=day, content_hash="h1")
    a2 = _make_article(
        session, tenant, topic,
        "Orange Botswana Launches New Data Bundle for customers",
        published_at=day + dt.timedelta(hours=3), content_hash="h2",
    )

    c1 = assign_story_cluster(session, a1)
    c2 = assign_story_cluster(session, a2)

    assert c1.id == c2.id
    assert c2.pickup_count == 2


def test_unrelated_titles_get_separate_clusters(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="BOCRA & regulation", kind=TopicKind.regulator)
    session.add(topic)
    session.flush()

    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    a1 = _make_article(session, tenant, topic, "BOCRA fines telecom operator", published_at=day, content_hash="h3")
    a2 = _make_article(session, tenant, topic, "Batanani Walk Targets Child Protection", published_at=day, content_hash="h4")

    c1 = assign_story_cluster(session, a1)
    c2 = assign_story_cluster(session, a2)

    assert c1.id != c2.id
    assert c1.pickup_count == 1
    assert c2.pickup_count == 1


def test_similarity_is_order_and_case_insensitive():
    a = "Mascom announces network upgrade"
    b = "NETWORK UPGRADE ANNOUNCED BY MASCOM"
    assert title_similarity(a, b) > 60


def test_clusters_outside_window_are_not_merged(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()

    old_day = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    new_day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    a1 = _make_article(session, tenant, topic, "Orange Botswana launches new data bundle", published_at=old_day, content_hash="h5")
    a2 = _make_article(session, tenant, topic, "Orange Botswana launches new data bundle", published_at=new_day, content_hash="h6")

    c1 = assign_story_cluster(session, a1, window_days=5)
    c2 = assign_story_cluster(session, a2, window_days=5)

    assert c1.id != c2.id
