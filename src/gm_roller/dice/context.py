from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RollContext:
    is_crit: bool
    is_nat_20: bool
    enabled_options: frozenset[str]
    component_id: str
    component_tags: frozenset[str]
    attack_id: str


@dataclass(frozen=True)
class AttackRollContext:
    is_crit: bool
    is_nat_20: bool
    enabled_options: frozenset[str]
    attack_id: str

    def for_component(
        self,
        component_id: str,
        component_tags: frozenset[str],
    ) -> RollContext:
        return RollContext(
            is_crit=self.is_crit,
            is_nat_20=self.is_nat_20,
            enabled_options=self.enabled_options,
            component_id=component_id,
            component_tags=component_tags,
            attack_id=self.attack_id,
        )
