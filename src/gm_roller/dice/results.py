from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class ComponentRoll:
    label: str
    expression: str
    total: int
    detail: str
    tags: frozenset[str]
    d20_result: Any | None = None

    def with_total(self, total: int, *, detail_suffix: str = "") -> ComponentRoll:
        detail = self.detail + detail_suffix if detail_suffix else self.detail
        return replace(self, total=total, detail=detail)


@dataclass(frozen=True)
class DamageResult:
    total: int
    components: tuple[ComponentRoll, ...]
