"""Credential lookup for login-gated flows (Phase 2).

Reads per-(club, area, field) env vars from .env.local via python-dotenv.
Returns None when unset — callers decide whether to skip the step (D-15)
or raise MissingCredentialError.

Env-var convention (D-14, user decision 1):
    {CLUB_UPPER}_{AREA_UPPER}_{FIELD_UPPER}
    e.g. MANCITY_HOSPITALITY_USER, TOTTENHAM_HOSPITALITY_PASS

Security invariants (T-02-01-01 / T-02-01-02):
    - Never logs the resolved value (no print, no logger calls anywhere).
    - MissingCredentialError formats only the env var NAME and the user
      instruction — it does NOT accept a `value=` kwarg; any attempt to
      pass one raises TypeError.

Override semantics (T-02-01-05, accepted):
    load_dotenv is called with override=False so an explicit shell export
    wins over the file. This is intended for CI where the file is absent
    and credentials arrive via secret-store injection.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import find_dotenv, load_dotenv

# Repo root: scanner/capture/credentials.py → parents[2] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# Plan 02-08 fix: previously this loaded `_REPO_ROOT / ".env.local"`, which
# silently misses when the helper is invoked from a CWD outside the package
# tree (orchestrator scripts, ad-hoc REPLs, CI runners that chdir). The
# tree-walk via find_dotenv(usecwd=True) ascends from the current working
# directory until it locates a `.env.local`. Falls back to the historical
# repo-root path so module import does not start raising in environments
# that never had find_dotenv-discoverable credentials (e.g. site-packages).
#
# Idempotent: load_dotenv silently no-ops when the file is absent, and
# repeated calls do not re-parse unless the file changes. override=False
# keeps shell env authoritative over file contents (T-02-01-05).
_DOTENV_LOCAL = find_dotenv(".env.local", usecwd=True)
if _DOTENV_LOCAL:
    load_dotenv(_DOTENV_LOCAL, override=False)
else:
    load_dotenv(_REPO_ROOT / ".env.local", override=False)

_ALLOWED_FIELDS: tuple[str, ...] = ("user", "pass")


class MissingCredentialError(RuntimeError):
    """Raised when a required credential env var is not set.

    The error message references the env var NAME (the thing the user
    must set) and points them at .env.local. It does NOT accept, store,
    or format any credential value — by construction.
    """

    def __init__(
        self,
        club: str,
        field: str,
        area: str,
        env_var_name: str,
    ) -> None:
        self.club = club
        self.field = field
        self.area = area
        self.env_var_name = env_var_name
        super().__init__(
            f"Credential not set for club={club!r} area={area!r} "
            f"field={field!r}. Set env var {env_var_name} in .env.local "
            f"at repo root."
        )


def _build_env_key(club: str, area: str, field: str) -> str:
    """Compose the canonical env-var key (all-caps, underscore-joined)."""
    return f"{club.upper()}_{area.upper()}_{field.upper()}"


def get_credential(
    club: str,
    field: Literal["user", "pass"],
    area: str = "hospitality",
) -> str | None:
    """Return env-var value for (club, area, field), or None if unset.

    Args:
        club:  Club slug (e.g. "mancity", "tottenham"). Case-insensitive.
        field: "user" or "pass" — any other value raises ValueError.
        area:  Area slug (default "hospitality"). Case-insensitive.

    Returns:
        The env-var value as a str, or None when the env var is unset.
        Callers decide whether None means "skip this step" (per D-15) or
        "raise MissingCredentialError".
    """
    if field not in _ALLOWED_FIELDS:
        raise ValueError(
            f"field must be one of {_ALLOWED_FIELDS!r}, got {field!r}"
        )
    key = _build_env_key(club, area, field)
    return os.environ.get(key)


__all__ = ["get_credential", "MissingCredentialError"]
