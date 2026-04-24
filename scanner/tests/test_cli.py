"""CLI smoke tests — owner Plan 07.

Uses Click's ``CliRunner`` so tests stay in-process (no subprocess
overhead, no dependency on the ``scanner`` console script). Each test
exercises one surface of :mod:`scanner.cli`:

1. ``--help`` lists all six top-level subcommands.
2. ``vision --help`` shows ``--api-mode`` with default ``subscription`` (D-28).
3. ``capture --help`` shows ``--headless / --no-headless`` with headed default.
4. ``flow validate --help`` exits 0 (nested group discoverable).
5. ``flow discover --help`` exits 0.
6. ``score --help`` exits 0.
7. Unknown subcommand exits non-zero (Click's ``UsageError`` path).

Per D-03, D-04, D-27, D-28 and FLOW-01 / FLOW-02.
"""
from __future__ import annotations

from click.testing import CliRunner

from scanner.cli import cli


def test_help_lists_all_subcommands() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    for sub in ("capture", "vision", "slice", "report", "score", "flow"):
        assert sub in result.output, f"missing subcommand {sub!r} in help:\n{result.output}"


def test_vision_help_defaults_to_subscription() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["vision", "--help"])
    assert result.exit_code == 0, result.output
    assert "--api-mode" in result.output
    assert "subscription" in result.output
    # `--api-mode` shows the default flagged in Click's default-note.
    # Click renders it as `[default: subscription]` when show_default=True.
    assert "default: subscription" in result.output


def test_capture_help_shows_headless_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["capture", "--help"])
    assert result.exit_code == 0, result.output
    assert "--headless" in result.output
    # Headed by default (user decision 2) — Click renders this as
    # `[default: no-headless]` for a boolean flag.
    assert "no-headless" in result.output


def test_flow_validate_help_exits_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["flow", "validate", "--help"])
    assert result.exit_code == 0, result.output
    assert "PATH" in result.output


def test_flow_discover_help_exits_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["flow", "discover", "--help"])
    assert result.exit_code == 0, result.output
    assert "ENTRY_URL" in result.output


def test_score_help_exits_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["score", "--help"])
    assert result.exit_code == 0, result.output
    assert "--area" in result.output


def test_unknown_subcommand_exits_non_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["nonsense-command"])
    # Click returns 2 for usage errors by default.
    assert result.exit_code != 0
