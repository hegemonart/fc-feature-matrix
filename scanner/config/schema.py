"""Pydantic schemas for scanner/config/areas.json.

The top-level config is a dict keyed by area name (hospitality, ticket,
sponsorship, ...). Implemented via Pydantic `RootModel[dict[str, AreaEntry]]`
so adding a new area in Phase 3-8 means dropping a new top-level key into the
JSON — no schema migration, no named-field churn.

Per D-10 (status vocabulary) and D-25 (Phase-1 seed = an empty-ish hospitality
entry with rubric_path / features_ts set to null; real paths arrive in Phase
2). See `.planning/phases/01-flow-automation-layer/01-RESEARCH.md` §6.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, RootModel

Status = Literal["pending", "pilot", "full", "deprecated"]


class AreaEntry(BaseModel):
    """A single area's I/O paths, rubric, and lifecycle status."""

    evidence_dir: str
    results_dir: str
    rubric_path: str | None = None   # None for Phase 1 seed (D-25)
    features_ts: str | None = None
    flow_maps_dir: str | None = None
    status: Status = "pending"


class AreasConfig(RootModel[dict[str, AreaEntry]]):
    """Top-level areas.json = `{area_name: AreaEntry, ...}`.

    Access entries via `.get(name)` (raises KeyError with a helpful message
    on miss) or directly through `.root` for dict-style iteration.
    """

    def get(self, area: str) -> AreaEntry:
        try:
            return self.root[area]
        except KeyError as e:
            known = sorted(self.root.keys())
            raise KeyError(f"Unknown area: {area}. Known: {known}") from e


__all__ = ["AreaEntry", "AreasConfig", "Status"]
