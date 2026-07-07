from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .tenant import Tenant


class TopicKind(str, enum.Enum):
    brand_watch = "brand_watch"
    competitor = "competitor"
    regulator = "regulator"
    sector = "sector"
    custom = "custom"


class Topic(Base, TimestampMixin):
    """A tenant's watchlist entry, e.g. 'Orange Botswana (brand watch)'.

    `keywords` drives naive pre-filtering during ingestion; the AI layer
    does the real relevance/topic-mapping call using this row's label and
    keywords injected into the tenant-aware prompt.
    """

    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)

    label: Mapped[str] = mapped_column(String(255))
    kind: Mapped[TopicKind] = mapped_column(Enum(TopicKind), default=TopicKind.custom)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(default=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="topics")

    def __repr__(self) -> str:
        return f"Topic(label={self.label!r}, kind={self.kind!r})"
