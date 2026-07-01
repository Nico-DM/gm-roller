from __future__ import annotations

from gm_roller.dice.context import RollContext
from gm_roller.dice.effects import PostRollEffect, PreRollEffect
from gm_roller.dice.results import ComponentRoll
from gm_roller.dice.spec import ExpressionSpec


def run_pre_roll(
    spec: ExpressionSpec,
    ctx: RollContext,
    effects: list[PreRollEffect],
) -> ExpressionSpec:
    for effect in effects:
        if effect.applies(ctx):
            spec = effect.transform(ctx, spec)
    return spec


def run_post_roll(
    roll: ComponentRoll,
    ctx: RollContext,
    effects: list[PostRollEffect],
) -> ComponentRoll:
    for effect in effects:
        if effect.applies(ctx):
            roll = effect.transform(ctx, roll)
    return roll


def merge_effects(*effect_lists: list) -> list:
    merged: list = []
    for effects in effect_lists:
        merged.extend(effects)
    return merged
