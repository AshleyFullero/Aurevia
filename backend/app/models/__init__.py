"""ORM models package — import all models here to register them with Base.metadata."""

from app.models import contact as _contact          # noqa: F401
from app.models import favorite as _favorite        # noqa: F401
from app.models import property as _property        # noqa: F401
from app.models import waitlist as _waitlist        # noqa: F401

__all__ = ["_contact", "_favorite", "_property", "_waitlist"]
