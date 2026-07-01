from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from gm_roller.dice.effects import PostRollEffect, PreRollEffect
from gm_roller.dice.registry import build_post_roll_effects, build_pre_roll_effects
from gm_roller.models.attack import Attack


class Hp(BaseModel):
    current: int
    max: int


class Character(BaseModel):
    id: str
    name: str
    ac: int | None = None
    hp: Hp | None = None
    pre_roll_effects: list[dict] = Field(default_factory=list)
    post_roll_effects: list[dict] = Field(default_factory=list)
    attacks: list[Attack] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_attack_ids(self) -> Character:
        seen: set[str] = set()
        for attack in self.attacks:
            if attack.id in seen:
                raise ValueError(f"duplicate attack id: {attack.id!r}")
            seen.add(attack.id)
        return self

    def get_attack(self, attack_id: str) -> Attack:
        for attack in self.attacks:
            if attack.id == attack_id:
                return attack
        raise KeyError(f"attack not found: {attack_id!r}")

    def parsed_pre_roll_effects(self) -> list[PreRollEffect]:
        return build_pre_roll_effects(self.pre_roll_effects)

    def parsed_post_roll_effects(self) -> list[PostRollEffect]:
        return build_post_roll_effects(self.post_roll_effects)
