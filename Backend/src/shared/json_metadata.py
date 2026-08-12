"""Shared JSON metadata parser used by audit-log and verification flows."""

import json
from typing import Any, Dict


def parse_json_metadata(metadata: Any) -> Dict[str, Any]:
    """
    Parse metadata that may be either a dict or a JSON string.

    Returns an empty dict for falsy or unparsable inputs.
    """
    if isinstance(metadata, str):
        try:
            return json.loads(metadata)
        except json.JSONDecodeError:
            return {}
    return metadata if metadata else {}
