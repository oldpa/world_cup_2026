from __future__ import annotations

import re


TEAM_ALIASES: dict[str, str] = {
    # Keep a minimal normalization shim for ASCII apostrophe variants.
    "Cote d'Ivoire": "Côte d'Ivoire",
}


def _compact(value: str) -> str:
    value = value.strip()
    value = value.replace("\u2019", "'")
    value = value.replace("\u2018", "'")
    return re.sub(r"\s+", " ", value)


def canonical_team_name(value: str) -> str:
    compact = _compact(value)
    return TEAM_ALIASES.get(compact, compact)
