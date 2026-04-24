"""areas.json loader — resolves paths relative to repo root.

Per D-04 / FLOW-02 the scanner is area-agnostic: every subcommand reads
``scanner/config/areas.json`` for its I/O paths instead of hard-coding
``analysis/hospitality/`` anywhere in the package. The loader resolves
relative paths against ``SCANNER_REPO_ROOT`` (env override — used by
the test suite to point at a synthetic tmp-path repo) or against the
package's walkup default.

See:

- `.planning/phases/01-flow-automation-layer/01-CONTEXT.md` D-04, D-10, D-25
- `.planning/phases/01-flow-automation-layer/01-RESEARCH.md` §6 (areas
  schema + Phase-1 seed)
"""
from __future__ import annotations

import os
from pathlib import Path

from scanner.config.schema import AreaEntry, AreasConfig

# Repo root: scanner/config/loader.py -> scanner -> repo
DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    override = os.environ.get("SCANNER_REPO_ROOT")
    return Path(override) if override else DEFAULT_REPO_ROOT


REPO_ROOT = _repo_root()


def _areas_json_path() -> Path:
    return _repo_root() / "scanner" / "config" / "areas.json"


def load_areas() -> AreasConfig:
    """Parse ``scanner/config/areas.json`` and return the typed config."""
    raw = _areas_json_path().read_text(encoding="utf-8")
    return AreasConfig.model_validate_json(raw)


def load_area(name: str) -> AreaEntry:
    """Return the ``AreaEntry`` for ``name`` or raise ``KeyError``.

    The error message points users at ``scanner/config/areas.json`` so
    the fix is discoverable without reading source.
    """
    cfg = load_areas()
    try:
        return cfg.get(name)
    except KeyError as e:
        known = sorted(cfg.root.keys())
        raise KeyError(
            f"Unknown area: {name}. Known: {known}. "
            f"Add it to scanner/config/areas.json."
        ) from e


__all__ = ["load_areas", "load_area", "REPO_ROOT"]
