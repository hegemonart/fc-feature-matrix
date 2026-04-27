"""Tests for scanner.capture.credentials.

Covers the full contract per plan 02-01 Task 1:

    1. Present env var → value returned.
    2. Missing env var → None (not an exception — callers decide per D-15).
    3. Case folding — caller's club / field casing is normalized to UPPER.
    4. Invalid field ("bogus") raises ValueError (Literal["user", "pass"] guard).
    5. Custom area parameter ("ticket") routes to MANCITY_TICKET_USER.
    6. MissingCredentialError message references env var NAME, never a value.
    7. Module imports cleanly even when .env.local is absent (dotenv tolerates it).

All env manipulation goes through monkeypatch — never reads real .env.local.
"""
from __future__ import annotations

import importlib

import pytest


# ---------------------------------------------------------------------------
# Test 1 — happy path
# ---------------------------------------------------------------------------
def test_get_credential_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """When MANCITY_HOSPITALITY_USER is set, get_credential returns its value."""
    from scanner.capture.credentials import get_credential

    monkeypatch.setenv("MANCITY_HOSPITALITY_USER", "alice@test")
    assert get_credential("mancity", "user") == "alice@test"


# ---------------------------------------------------------------------------
# Test 2 — absent env var → None, not exception
# ---------------------------------------------------------------------------
def test_get_credential_missing_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset env var returns None — caller decides whether to raise or skip."""
    from scanner.capture.credentials import get_credential

    monkeypatch.delenv("MANCITY_HOSPITALITY_USER", raising=False)
    assert get_credential("mancity", "user") is None


# ---------------------------------------------------------------------------
# Test 3 — case folding (club + field) normalizes to upper
# ---------------------------------------------------------------------------
def test_case_folding(monkeypatch: pytest.MonkeyPatch) -> None:
    """MANCITY / mancity and USER / user resolve to the same env key."""
    from scanner.capture.credentials import get_credential

    monkeypatch.setenv("MANCITY_HOSPITALITY_USER", "bob@test")
    assert get_credential("mancity", "user") == "bob@test"
    # Uppercase club still resolves
    assert get_credential("MANCITY", "user") == "bob@test"
    # Mixed case
    assert get_credential("ManCity", "user") == "bob@test"


# ---------------------------------------------------------------------------
# Test 4 — invalid field → ValueError (Literal guard at runtime)
# ---------------------------------------------------------------------------
def test_invalid_field_raises_value_error() -> None:
    """Field outside ('user', 'pass') raises ValueError."""
    from scanner.capture.credentials import get_credential

    with pytest.raises(ValueError, match="field"):
        get_credential("mancity", "bogus")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Test 5 — custom area parameter
# ---------------------------------------------------------------------------
def test_custom_area(monkeypatch: pytest.MonkeyPatch) -> None:
    """area='ticket' routes to MANCITY_TICKET_USER, not the default HOSPITALITY."""
    from scanner.capture.credentials import get_credential

    monkeypatch.setenv("MANCITY_TICKET_USER", "carol@test")
    # Default hospitality must not resolve to this
    monkeypatch.delenv("MANCITY_HOSPITALITY_USER", raising=False)

    assert get_credential("mancity", "user", area="ticket") == "carol@test"
    assert get_credential("mancity", "user") is None  # default area differs


# ---------------------------------------------------------------------------
# Test 6 — MissingCredentialError message references env var NAME, never value
# ---------------------------------------------------------------------------
def test_missing_credential_error_message_includes_env_var_name() -> None:
    """Error formats the env var name + .env.local instruction; no values."""
    from scanner.capture.credentials import MissingCredentialError

    err = MissingCredentialError(
        club="mancity",
        field="user",
        area="hospitality",
        env_var_name="MANCITY_HOSPITALITY_USER",
    )
    msg = str(err)
    assert "MANCITY_HOSPITALITY_USER" in msg
    assert ".env.local" in msg
    # Attributes preserved for programmatic handlers
    assert err.club == "mancity"
    assert err.field == "user"
    assert err.area == "hospitality"
    assert err.env_var_name == "MANCITY_HOSPITALITY_USER"

    # Security guard: constructor must NOT accept a value kwarg
    with pytest.raises(TypeError):
        MissingCredentialError(  # type: ignore[call-arg]
            club="mancity",
            field="user",
            area="hospitality",
            env_var_name="MANCITY_HOSPITALITY_USER",
            value="secret-that-must-not-leak",
        )


# ---------------------------------------------------------------------------
# Test 7 — module import is safe when .env.local is absent
# ---------------------------------------------------------------------------
def test_load_dotenv_safe_when_file_absent() -> None:
    """Re-importing the module when .env.local is missing raises nothing.

    python-dotenv's load_dotenv() is a silent no-op when the path doesn't
    exist, so a fresh import (simulating a clean dev env) must succeed.
    """
    import scanner.capture.credentials as cred

    # Re-import to prove idempotency (covers the load_dotenv-called-again path)
    importlib.reload(cred)
    assert hasattr(cred, "get_credential")
    assert hasattr(cred, "MissingCredentialError")


# ---------------------------------------------------------------------------
# Plan 02-08 — find_dotenv tree-walk regression tests
# ---------------------------------------------------------------------------
#
# Module-reload caveat: load_dotenv runs at module import. To exercise the
# new find_dotenv(usecwd=True) tree-walk we must `monkeypatch.chdir(...)`
# BEFORE re-importing the module so the discovery happens against the
# fake repo tree, not the real filesystem. importlib.reload bypasses the
# import cache.


def test_get_credential_resolves_env_local_from_sibling_subdirectory(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan 02-08 Test 1: when invoked from a sibling temp dir whose ancestor
    contains a .env.local, the helper must walk up and find it.

    Failing case (pre-08): load_dotenv(_REPO_ROOT/'.env.local') silently
    misses because tmp_path is outside _REPO_ROOT and there's no .env.local
    at _REPO_ROOT in test envs.
    """
    # Build a fake repo tree: tmp_path/repo/.env.local + a sibling cwd.
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    (fake_repo / ".env.local").write_text(
        "MANCITY_HOSPITALITY_USER=ci+test@example.com\n",
        encoding="utf-8",
    )
    sibling = fake_repo / "scanner" / "sub"
    sibling.mkdir(parents=True)

    # Important: chdir BEFORE re-importing so find_dotenv(usecwd=True)
    # walks up from `sibling` and discovers fake_repo/.env.local.
    monkeypatch.chdir(sibling)

    # Clean any stale env from earlier tests (we want to prove the file path
    # is consulted, not a leaked env var).
    monkeypatch.delenv("MANCITY_HOSPITALITY_USER", raising=False)

    import scanner.capture.credentials as cred
    importlib.reload(cred)

    assert cred.get_credential("mancity", "user") == "ci+test@example.com"


def test_get_credential_returns_none_when_no_env_local_anywhere(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plan 02-08 Test 2: when no .env.local exists up the tree AND no shell
    env is set, get_credential cleanly returns None (no exception).

    This proves the find_dotenv branch falls back gracefully and the
    helper still honors its `unset → None` contract. We patch
    ``find_dotenv`` to return empty AND redirect the fallback _REPO_ROOT
    to an isolated tmp dir so neither path picks up a real `.env.local`
    that may exist in the developer's environment.
    """
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    monkeypatch.chdir(isolated)
    # Ensure no leak from previous tests.
    monkeypatch.delenv("MANCITY_HOSPITALITY_USER", raising=False)

    # Stop the dev's real .env.local from leaking via the fallback path.
    # We reload the module under a patched dotenv namespace so both the
    # find_dotenv tree-walk AND the _REPO_ROOT fallback resolve to nothing.
    import scanner.capture.credentials as cred

    monkeypatch.setattr(cred, "_REPO_ROOT", isolated)
    monkeypatch.setattr(cred, "find_dotenv", lambda *a, **kw: "")
    importlib.reload(cred)
    # Reload re-imports from dotenv module — re-patch the freshly loaded
    # symbols so the second pass also sees our stubs.
    monkeypatch.setattr(cred, "_REPO_ROOT", isolated)
    monkeypatch.setattr(cred, "find_dotenv", lambda *a, **kw: "")

    # Belt-and-braces: even if a stray env var leaks past the patches above,
    # the contract is that get_credential returns whatever os.environ has —
    # so an explicit delenv guarantees the None branch.
    monkeypatch.delenv("MANCITY_HOSPITALITY_USER", raising=False)
    assert cred.get_credential("mancity", "user") is None


def test_module_uses_find_dotenv_helper() -> None:
    """Defensive: the module references find_dotenv at import-time. If a
    future refactor reverts to a hard-coded _REPO_ROOT path the test fails.
    """
    import scanner.capture.credentials as cred

    importlib.reload(cred)
    # find_dotenv is imported into the credentials namespace; treat its
    # presence as the structural guarantee.
    assert hasattr(cred, "find_dotenv"), (
        "scanner.capture.credentials must import find_dotenv (Plan 02-08 fix)"
    )
