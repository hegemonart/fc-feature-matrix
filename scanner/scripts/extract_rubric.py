"""TypeScript->JSON rubric extractor — Plan 02-11 Task 1.

Purpose
-------
The ``scanner vision`` CLI (Plan 01-07) takes ``--rubric <json-path>`` whose
shape is ``{"features": [FeatureDef, ...]}``. Area features are authored in
TypeScript at ``<area>/features.ts`` (single source of truth); this script
regex-extracts those ``feat(...)`` calls into a transient JSON consumable by
``scanner vision``.

Approach
--------
A single regex matches every ``feat('id', 'key', 'name', 'desc', 'cat',
'tier', ...)`` call. The first 6 string args are captured; the trailing
numeric weights are not needed for the vision rubric (FeatureDef only
needs ``key``, ``name``, ``yes_criterion``).

The emitted ``yes_criterion`` is the literal ``desc`` string from the
feat() call — that string IS the YES criterion ("the feature is present
iff this is true").

Output is **transient** (gitignored). Re-running overwrites. The script is
area-agnostic: it accepts any features.ts path on the CLI (FLOW-02 invariant).

Usage
-----
::

    python -m scanner.scripts.extract_rubric \\
      --features-ts <path-to-features.ts> \\
      --out <path-to-output.json>

Exit codes
----------
0  successful extraction; count printed to stdout.
2  schema validation failed for at least one feature (shouldn't happen
   with a clean features.ts — fail-fast guard).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import click

from scanner.vision.schema import FeatureDef


# Regex matches a single ``feat('id', 'key', 'name', 'desc', 'cat', 'tier', ...)``
# call across multiline. Six string captures + greedy match for trailing args.
# DOTALL allows ``.`` to span the literal newlines inside multiline feat() calls.
#
# Each string capture supports a single backslash-escaped quote inside the body
# via ``(?:[^'\\]|\\.)*`` — this matches the TypeScript source pattern where
# descriptions occasionally contain ``\'`` (e.g. HP31's "we\\'ll be in touch").
# Post-capture we unescape \\' -> ' before emission.
FEAT_RE = re.compile(
    r"feat\(\s*"
    r"'(?P<id>(?:[^'\\]|\\.)*)'\s*,\s*"
    r"'(?P<key>(?:[^'\\]|\\.)*)'\s*,\s*"
    r"'(?P<name>(?:[^'\\]|\\.)*)'\s*,\s*"
    r"'(?P<desc>(?:[^'\\]|\\.)*)'\s*,\s*"
    r"'(?P<cat>(?:[^'\\]|\\.)*)'\s*,\s*"
    r"'(?P<tier>(?:[^'\\]|\\.)*)'",
    re.MULTILINE | re.DOTALL,
)


def _unescape(s: str) -> str:
    """Unescape backslash-escaped single quotes from TypeScript source."""
    return s.replace("\\'", "'").replace('\\"', '"')


def extract_rubric_to_json(features_ts_path: Path, out_json_path: Path) -> int:
    """Extract feat() calls from features.ts and write a rubric JSON.

    Args:
        features_ts_path: Path to a TypeScript features.ts file containing
            ``feat('id', 'key', 'name', 'desc', 'cat', 'tier', ...)`` calls.
        out_json_path: Destination JSON path. Parent directories are NOT
            auto-created — caller is responsible (idempotent overwrite).

    Returns:
        Number of features extracted.

    Raises:
        SystemExit: If any extracted feature fails ``FeatureDef`` validation
            (exit code 2). This is a fail-fast guard against malformed
            extraction (T-11-05 mitigation).
    """
    text = features_ts_path.read_text(encoding="utf-8")
    matches = list(FEAT_RE.finditer(text))

    features: list[dict] = []
    for m in matches:
        features.append(
            {
                "key": _unescape(m.group("key")),
                "name": _unescape(m.group("name")),
                "yes_criterion": _unescape(m.group("desc")),
            }
        )

    # T-11-05 mitigation: validate every extracted record against the
    # canonical FeatureDef shape before writing. If anything is malformed
    # (e.g. regex mis-captured), surface the error here, not when the
    # vision CLI tries to load the file mid-wave.
    try:
        for f in features:
            FeatureDef(**f)
    except Exception as exc:  # pragma: no cover — defensive
        click.echo(f"Schema validation failed: {exc}", err=True)
        raise SystemExit(2) from exc

    out_json_path.write_text(
        json.dumps(
            {"features": features},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return len(features)


@click.command()
@click.option(
    "--features-ts",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the source features.ts file.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    required=True,
    help="Destination path for the emitted rubric JSON.",
)
def main(features_ts: Path, out_path: Path) -> None:
    """CLI: extract rubric from features.ts and print the count."""
    count = extract_rubric_to_json(features_ts, out_path)
    click.echo(f"Extracted {count} features -> {out_path}")


if __name__ == "__main__":
    main()


__all__ = ["FEAT_RE", "extract_rubric_to_json", "main"]
