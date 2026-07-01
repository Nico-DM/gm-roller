from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gm_roller.dice.conditions import matches
from gm_roller.dice.context import RollContext
from gm_roller.dice.results import ComponentRoll
from gm_roller.dice.spec import DieTerm, ExpressionSpec


class PreRollEffect(Protocol):
    def applies(self, ctx: RollContext) -> bool: ...
    def transform(self, ctx: RollContext, spec: ExpressionSpec) -> ExpressionSpec: ...


class PostRollEffect(Protocol):
    def applies(self, ctx: RollContext) -> bool: ...
    def transform(self, ctx: RollContext, roll: ComponentRoll) -> ComponentRoll: ...


def _tags_match(target_tags: frozenset[str] | None, ctx: RollContext) -> bool:
    if target_tags is None:
        return True
    return bool(target_tags & ctx.component_tags)


@dataclass(frozen=True)
class PreRollWhen:
    condition: str
    inner: PreRollEffect

    def applies(self, ctx: RollContext) -> bool:
        return matches(self.condition, ctx)

    def transform(self, ctx: RollContext, spec: ExpressionSpec) -> ExpressionSpec:
        return self.inner.transform(ctx, spec)


@dataclass(frozen=True)
class PostRollWhen:
    condition: str
    inner: PostRollEffect

    def applies(self, ctx: RollContext) -> bool:
        return matches(self.condition, ctx)

    def transform(self, ctx: RollContext, roll: ComponentRoll) -> ComponentRoll:
        return self.inner.transform(ctx, roll)


@dataclass(frozen=True)
class DoubleDice:
    """Double all dice in the component (standard 5e crit on damage dice)."""

    target_tags: frozenset[str] | None = None

    def applies(self, ctx: RollContext) -> bool:
        return _tags_match(self.target_tags, ctx)

    def transform(self, ctx: RollContext, spec: ExpressionSpec) -> ExpressionSpec:
        if not self.applies(ctx):
            return spec
        new_dice = [DieTerm(d.count * 2, d.sides, d.ops) for d in spec.dice]
        return spec.with_dice(new_dice)


@dataclass(frozen=True)
class AddDice:
    dice: tuple[DieTerm, ...]
    target_tags: frozenset[str] | None = None

    def applies(self, ctx: RollContext) -> bool:
        return _tags_match(self.target_tags, ctx)

    def transform(self, ctx: RollContext, spec: ExpressionSpec) -> ExpressionSpec:
        if not self.applies(ctx):
            return spec
        return spec.with_dice([*spec.dice, *self.dice])


@dataclass(frozen=True)
class ChangeDieSides:
    from_sides: int
    to_sides: int
    target_tags: frozenset[str] | None = None

    def applies(self, ctx: RollContext) -> bool:
        return _tags_match(self.target_tags, ctx)

    def transform(self, ctx: RollContext, spec: ExpressionSpec) -> ExpressionSpec:
        if not self.applies(ctx):
            return spec
        new_dice = [
            DieTerm(d.count, self.to_sides if d.sides == self.from_sides else d.sides, d.ops)
            for d in spec.dice
        ]
        return spec.with_dice(new_dice)


@dataclass(frozen=True)
class AppendDieOps:
    ops: str
    target_tags: frozenset[str] | None = None

    def applies(self, ctx: RollContext) -> bool:
        return _tags_match(self.target_tags, ctx)

    def transform(self, ctx: RollContext, spec: ExpressionSpec) -> ExpressionSpec:
        if not self.applies(ctx):
            return spec
        new_dice = [DieTerm(d.count, d.sides, d.ops + self.ops) for d in spec.dice]
        return spec.with_dice(new_dice)


@dataclass(frozen=True)
class MultiplyTotal:
    factor: int
    note: str = ""
    target_tags: frozenset[str] | None = None

    def applies(self, ctx: RollContext) -> bool:
        return _tags_match(self.target_tags, ctx)

    def transform(self, ctx: RollContext, roll: ComponentRoll) -> ComponentRoll:
        if not self.applies(ctx):
            return roll
        label = self.note or f"×{self.factor}"
        return roll.with_total(roll.total * self.factor, detail_suffix=f" ({label})")


@dataclass(frozen=True)
class SetMinimumTotal:
    minimum: int
    target_tags: frozenset[str] | None = None

    def applies(self, ctx: RollContext) -> bool:
        return _tags_match(self.target_tags, ctx)

    def transform(self, ctx: RollContext, roll: ComponentRoll) -> ComponentRoll:
        if not self.applies(ctx):
            return roll
        if roll.total < self.minimum:
            return roll.with_total(self.minimum, detail_suffix=f" (min {self.minimum})")
        return roll


@dataclass(frozen=True)
class AddFlatBonus:
    bonus: int
    target_tags: frozenset[str] | None = None

    def applies(self, ctx: RollContext) -> bool:
        return _tags_match(self.target_tags, ctx)

    def transform(self, ctx: RollContext, roll: ComponentRoll) -> ComponentRoll:
        if not self.applies(ctx):
            return roll
        sign = f"+{self.bonus}" if self.bonus >= 0 else str(self.bonus)
        return roll.with_total(roll.total + self.bonus, detail_suffix=f" ({sign})")


DEFAULT_PRE_ROLL_EFFECTS: tuple[PreRollWhen, ...] = (
    PreRollWhen("crit", DoubleDice()),
)
