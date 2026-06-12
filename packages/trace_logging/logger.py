from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from packages.privacy_controls.safe_logging import redact_mapping


def build_trace_event(
    *,
    trace_id: str,
    event_name: str,
    provider: str,
    payload: dict[str, Any] | None = None,
) -> str:
    """Build a JSON trace event that is safe to print.

    Do not put raw prompts, raw customer documents, API keys, or secrets into payload.
    """

    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "trace_id": trace_id,
        "event_name": event_name,
        "provider": provider,
        "payload": redact_mapping(payload or {}),
    }
    return json.dumps(event, sort_keys=True)
