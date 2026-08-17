"""SQLAlchemy ORM model for saved / favorited properties."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Favorite(Base):
    """Tracks which properties a session has favorited.

    Uses a session_token (sent as X-Session-Token header) rather than a full
    user account — this is the pre-auth MVP approach.  When auth is added,
    replace session_token with a user_id FK.
    """

    __tablename__ = "favorites"

    # Ensure a session can't favorite the same property twice
    __table_args__ = (
        UniqueConstraint("session_token", "property_id", name="uq_session_property"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Client-supplied token (UUID recommended, no PII stored)
    session_token: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    property_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Favorite session={self.session_token[:8]}… property_id={self.property_id}>"
