"""Canonical event model and adapters for public clickstream datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


VALID_EVENT_TYPES = {"view", "cart", "remove_from_cart", "purchase"}


def _parse_datetime(value: str | int | float) -> datetime:
    """Parse ISO/REES46 timestamps or Unix timestamps into an aware datetime."""
    if isinstance(value, (int, float)) or str(value).strip().isdigit():
        numeric = float(value)
        if numeric > 10_000_000_000:
            numeric /= 1000
        return datetime.fromtimestamp(numeric, tz=timezone.utc)

    text = str(value).strip().replace(" UTC", "+00:00").replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalise_event_type(value: str) -> str:
    aliases = {
        "addtocart": "cart",
        "add_to_cart": "cart",
        "cart": "cart",
        "removefromcart": "remove_from_cart",
        "remove_from_cart": "remove_from_cart",
        "transaction": "purchase",
        "purchase": "purchase",
        "view": "view",
    }
    result = aliases.get(value.strip().lower())
    if result is None:
        raise ValueError(f"Unsupported event type: {value!r}")
    return result


@dataclass(frozen=True, slots=True)
class ClickEvent:
    """Dataset-independent representation used throughout the pipeline."""

    event_time: datetime
    event_type: str
    product_id: str
    user_id: str
    session_id: str
    category_id: str = ""
    category_code: str = ""
    brand: str = ""
    price: float | None = None
    source_event_time: datetime | None = None

    def __post_init__(self) -> None:
        if self.event_type not in VALID_EVENT_TYPES:
            raise ValueError(f"Unsupported event type: {self.event_type!r}")
        if not self.product_id:
            raise ValueError("product_id is required")
        if not self.session_id:
            raise ValueError("session_id is required")
        if self.event_time.tzinfo is None:
            raise ValueError("event_time must include a timezone")

    @classmethod
    def from_rees46(cls, row: Mapping[str, Any]) -> "ClickEvent":
        """Create an event from the REES46 multi-category CSV schema."""
        event_time = _parse_datetime(row["event_time"])
        price_value = row.get("price")
        return cls(
            event_time=event_time,
            source_event_time=event_time,
            event_type=_normalise_event_type(str(row["event_type"])),
            product_id=str(row["product_id"]),
            user_id=str(row.get("user_id", "")),
            session_id=str(row.get("user_session") or row.get("session_id") or ""),
            category_id=str(row.get("category_id", "") or ""),
            category_code=str(row.get("category_code", "") or ""),
            brand=str(row.get("brand", "") or ""),
            price=float(price_value) if price_value not in (None, "") else None,
        )

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "ClickEvent":
        """Create an event from the canonical JSON representation."""
        source_time = row.get("source_event_time")
        return cls(
            event_time=_parse_datetime(row["event_time"]),
            source_event_time=_parse_datetime(source_time) if source_time else None,
            event_type=_normalise_event_type(str(row["event_type"])),
            product_id=str(row["product_id"]),
            user_id=str(row.get("user_id", "")),
            session_id=str(row["session_id"]),
            category_id=str(row.get("category_id", "") or ""),
            category_code=str(row.get("category_code", "") or ""),
            brand=str(row.get("brand", "") or ""),
            price=float(row["price"]) if row.get("price") not in (None, "") else None,
        )

    def rebased(self, event_time: datetime) -> "ClickEvent":
        """Move an historical event onto the replay clock while retaining its source time."""
        values = asdict(self)
        values["event_time"] = event_time
        values["source_event_time"] = self.source_event_time or self.event_time
        return ClickEvent(**values)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["event_time"] = self.event_time.isoformat()
        if self.source_event_time is not None:
            result["source_event_time"] = self.source_event_time.isoformat()
        return result
