"""Tenant-aware classification prompt.

The same article means different things to different tenants — a BTC price
cut is a competitor threat for Orange Botswana and just sector news for a
bank. Injecting the tenant's watchlist (its own brand-watch topics,
competitors, regulator, sector topics, each with their keywords) is what
lets one shared classification pipeline produce tenant-specific
`sentiment_by_brand`, `category`, and `threat_tag` judgements instead of a
generic one-size-fits-all summary.
"""
from __future__ import annotations

from ..models import Article, Tenant, Topic

MAX_BODY_CHARS = 8000

SUGGESTED_CATEGORIES = (
    "telco", "banking", "government", "regulator", "mining", "fintech",
    "sport", "csr", "other",
)

_SCHEMA_EXAMPLE = """{
  "relevance_score": 0.0-1.0,
  "category": "telco|banking|government|regulator|mining|fintech|sport|csr|other",
  "sentiment_overall": "positive|neutral|negative",
  "sentiment_by_brand": {"<brand name>": "positive|neutral|negative", "...": "..."},
  "entities": {
    "brands": ["..."], "people": ["..."], "organisations": ["..."],
    "products": ["..."], "events": ["..."], "locations": ["..."]
  },
  "summary_exec": "two-sentence executive summary",
  "key_quotes": ["notable quote from the article", "..."],
  "why_it_matters": "one short paragraph on why this matters to the tenant",
  "threat_tag": "opportunity|monitor|risk",
  "threat_rationale": "one-line rationale for the threat_tag"
}"""


def _format_watchlist(topics: list[Topic]) -> str:
    lines = []
    for topic in topics:
        keywords = ", ".join(topic.keywords) if topic.keywords else "(no keywords configured)"
        lines.append(f"- {topic.label} [{topic.kind.value}]: {keywords}")
    return "\n".join(lines) if lines else "(no watchlist configured)"


def build_classification_prompt(*, tenant: Tenant, topics: list[Topic], article: Article) -> str:
    body = article.raw_text or ""
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS] + "\n[...truncated...]"

    return f"""You are a media intelligence analyst working for {tenant.name}, a PR/communications \
client monitoring Botswana media. Analyze the article below strictly from {tenant.name}'s \
perspective using its watchlist.

{tenant.name}'s watchlist:
{_format_watchlist(topics)}

Sentiment must be reported per brand mentioned (a brand can be positive for one company and \
negative for another in the same article — e.g. a competitor price cut is negative for that \
competitor's rival, not for the competitor itself). Only include brands actually mentioned in \
the article in "sentiment_by_brand". "category" should be one of: {", ".join(SUGGESTED_CATEGORIES)} \
(use "other" if none fit). "threat_tag" is from {tenant.name}'s point of view: "opportunity" if \
this helps {tenant.name}, "risk" if it's a competitive or reputational threat, "monitor" otherwise.

Return ONLY a single JSON object, no other text, matching exactly this shape:
{_SCHEMA_EXAMPLE}

Article:
Publication: {article.publication}
Title: {article.title}
Body:
{body}
"""
