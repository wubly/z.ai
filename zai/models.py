from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ZaiResponse:
    text: str
    thinking: str | None = None
    thinking_seconds: float | None = None
    message_id: str | None = None
    raw_html: str | None = field(default=None, repr=False)
