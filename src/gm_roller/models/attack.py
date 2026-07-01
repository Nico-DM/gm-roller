from __future__ import annotations

from pydantic import BaseModel, Field

from gm_roller.dice.effects import PostRollEffect, PreRollEffect
from gm_roller.dice.registry import build_post_roll_effects, build_pre_roll_effects


class DamageComponent(BaseModel):
    id: str
    label: str
    expr: str
    tags: list[str] = Field(default_factory=list)
    optional: bool = False
    option_id: str | None = None

    @property
    def tag_set(self) -> frozenset[str]:
        return frozenset(self.tags)


class Attack(BaseModel):
    id: str
    to_hit: str
    components: list[DamageComponent]
    pre_roll_effects: list[dict] = Field(default_factory=list)
    post_roll_effects: list[dict] = Field(default_factory=list)

    def active_components(self, enabled_options: frozenset[str]) -> list[DamageComponent]:
        active: list[DamageComponent] = []
        for component in self.components:
            if component.optional:
                if component.option_id and component.option_id in enabled_options:
                    active.append(component)
            else:
                active.append(component)
        return active

    def parsed_pre_roll_effects(self) -> list[PreRollEffect]:
        return build_pre_roll_effects(self.pre_roll_effects)

    def parsed_post_roll_effects(self) -> list[PostRollEffect]:
        return build_post_roll_effects(self.post_roll_effects)
