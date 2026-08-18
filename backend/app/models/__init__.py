"""ORM models package — import all models here to register them with Base.metadata."""

# ── Existing models ───────────────────────────────────────────────────────────
from app.models import contact as _contact            # noqa: F401
from app.models import favorite as _favorite          # noqa: F401
from app.models import property as _property          # noqa: F401
from app.models import waitlist as _waitlist          # noqa: F401

# ── New domain models ─────────────────────────────────────────────────────────
from app.models import review as _review              # noqa: F401
from app.models import neighborhood as _neighborhood  # noqa: F401
from app.models import price_history as _price_history  # noqa: F401
from app.models import portfolio as _portfolio        # noqa: F401

__all__ = [
    "_contact",
    "_favorite",
    "_property",
    "_waitlist",
    "_review",
    "_neighborhood",
    "_price_history",
    "_portfolio",
]
