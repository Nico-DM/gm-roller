from __future__ import annotations

from gm_roller.dice.effects import (
    AddDice,
    AddFlatBonus,
    AppendDieOps,
    ChangeDieSides,
    DoubleDice,
    MultiplyTotal,
    PostRollEffect,
    PostRollWhen,
    PreRollEffect,
    PreRollWhen,
    SetMinimumTotal,
)
from gm_roller.dice.spec import die_terms_from_dicts


def _parse_tags(tags: list[str] | None) -> frozenset[str] | None:
    if tags is None:
        return None
    return frozenset(tags)


def build_pre_roll_effect(data: dict) -> PreRollEffect:
    effect_type = data["type"]
    if effect_type == "when":
        return PreRollWhen(
            condition=data["condition"],
            inner=build_pre_roll_effect(data["effect"]),
        )
    if effect_type == "double_dice":
        return DoubleDice(target_tags=_parse_tags(data.get("target_tags")))
    if effect_type == "add_dice":
        return AddDice(
            dice=tuple(die_terms_from_dicts(data["dice"])),
            target_tags=_parse_tags(data.get("target_tags")),
        )
    if effect_type == "change_die_sides":
        return ChangeDieSides(
            from_sides=data["from_sides"],
            to_sides=data["to_sides"],
            target_tags=_parse_tags(data.get("target_tags")),
        )
    if effect_type == "append_die_ops":
        return AppendDieOps(
            ops=data["ops"],
            target_tags=_parse_tags(data.get("target_tags")),
        )
    raise ValueError(f"unknown pre-roll effect type: {effect_type!r}")


def build_post_roll_effect(data: dict) -> PostRollEffect:
    effect_type = data["type"]
    if effect_type == "when":
        return PostRollWhen(
            condition=data["condition"],
            inner=build_post_roll_effect(data["effect"]),
        )
    if effect_type == "multiply_total":
        return MultiplyTotal(
            factor=data["factor"],
            note=data.get("note", ""),
            target_tags=_parse_tags(data.get("target_tags")),
        )
    if effect_type == "set_minimum_total":
        return SetMinimumTotal(
            minimum=data["minimum"],
            target_tags=_parse_tags(data.get("target_tags")),
        )
    if effect_type == "add_flat_bonus":
        return AddFlatBonus(
            bonus=data["bonus"],
            target_tags=_parse_tags(data.get("target_tags")),
        )
    raise ValueError(f"unknown post-roll effect type: {effect_type!r}")


def build_pre_roll_effects(data: list[dict]) -> list[PreRollEffect]:
    return [build_pre_roll_effect(item) for item in data]


def build_post_roll_effects(data: list[dict]) -> list[PostRollEffect]:
    return [build_post_roll_effect(item) for item in data]
