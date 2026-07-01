from __future__ import annotations

import unittest
from unittest.mock import patch

from gm_roller.dice.context import AttackRollContext, RollContext
from gm_roller.dice.effects import (
    AddDice,
    AppendDieOps,
    ChangeDieSides,
    DoubleDice,
    MultiplyTotal,
    PreRollWhen,
)
from gm_roller.dice.engine import DiceEngine
from gm_roller.dice.pipeline import run_pre_roll
from gm_roller.dice.registry import build_pre_roll_effect, build_pre_roll_effects
from gm_roller.dice.spec import DieTerm, ExpressionSpec, parse_expr
from gm_roller.models.attack import Attack, DamageComponent


def _ctx(*, is_crit: bool = False, tags: frozenset[str] | None = None) -> RollContext:
    return RollContext(
        is_crit=is_crit,
        is_nat_20=is_crit,
        enabled_options=frozenset(),
        component_id="base",
        component_tags=tags or frozenset({"weapon"}),
        attack_id="test",
    )


class TestExpressionSpec(unittest.TestCase):
    def test_parse_and_compile_simple(self) -> None:
        spec = parse_expr("1d8+5")
        self.assertEqual(spec.dice, (DieTerm(1, 8),))
        self.assertEqual(spec.modifier, 5)
        self.assertEqual(spec.compile(), "1d8+5")

    def test_parse_multiple_dice_groups(self) -> None:
        spec = parse_expr("1d8+1d6+3")
        self.assertEqual(len(spec.dice), 2)
        self.assertEqual(spec.modifier, 3)
        self.assertEqual(spec.compile(), "1d8+1d6+3")

    def test_double_dice_on_crit(self) -> None:
        spec = parse_expr("1d10+5")
        effects = [PreRollWhen("crit", DoubleDice())]
        result = run_pre_roll(spec, _ctx(is_crit=True), effects)
        self.assertEqual(result.compile(), "2d10+5")

    def test_double_dice_skipped_when_not_crit(self) -> None:
        spec = parse_expr("1d10+5")
        effects = [PreRollWhen("crit", DoubleDice())]
        result = run_pre_roll(spec, _ctx(is_crit=False), effects)
        self.assertEqual(result.compile(), "1d10+5")

    def test_append_die_ops_gwf(self) -> None:
        spec = parse_expr("2d6+4")
        effects = [PreRollWhen("option:gwf", AppendDieOps("ro<3", target_tags=frozenset({"weapon"})))]
        ctx = RollContext(
            is_crit=False,
            is_nat_20=False,
            enabled_options=frozenset({"gwf"}),
            component_id="base",
            component_tags=frozenset({"weapon"}),
            attack_id="test",
        )
        result = run_pre_roll(spec, ctx, effects)
        self.assertEqual(result.compile(), "2d6ro<3+4")

    def test_add_dice_and_change_sides_on_crit(self) -> None:
        spec = parse_expr("2d6+4")
        effects = [
            PreRollWhen("crit", DoubleDice()),
            PreRollWhen("crit", AddDice((DieTerm(1, 10),))),
            PreRollWhen("crit", ChangeDieSides(from_sides=6, to_sides=8)),
        ]
        result = run_pre_roll(spec, _ctx(is_crit=True), effects)
        self.assertEqual(result.compile(), "4d8+1d10+4")

    def test_build_effects_from_json(self) -> None:
        data = [
            {
                "type": "when",
                "condition": "crit",
                "effect": {"type": "double_dice", "target_tags": ["weapon"]},
            },
            {
                "type": "when",
                "condition": "option:gwf",
                "effect": {
                    "type": "append_die_ops",
                    "ops": "ro<3",
                    "target_tags": ["weapon"],
                },
            },
        ]
        effects = build_pre_roll_effects(data)
        self.assertEqual(len(effects), 2)
        self.assertIsInstance(effects[0], PreRollWhen)
        self.assertIsInstance(build_pre_roll_effect(data[1]["effect"]), AppendDieOps)


class TestDiceEngine(unittest.TestCase):
    def test_roll_attack_damage_with_crit_pipeline(self) -> None:
        attack = Attack(
            id="greatsword",
            to_hit="1d20+8",
            components=[
                DamageComponent(
                    id="base",
                    label="Greatsword",
                    expr="2d6+5",
                    tags=["weapon", "melee"],
                ),
            ],
            pre_roll_effects=[],
        )
        engine = DiceEngine()
        roll_ctx = AttackRollContext(
            is_crit=True,
            is_nat_20=True,
            enabled_options=frozenset(),
            attack_id=attack.id,
        )

        with patch("random.randrange", side_effect=[4, 3, 5, 2]):
            result = engine.roll_attack_damage(attack, roll_ctx)

        self.assertEqual(result.components[0].expression, "4d6+5")
        self.assertEqual(result.total, 23)

    def test_optional_component_requires_enabled_option(self) -> None:
        attack = Attack(
            id="sneak",
            to_hit="1d20+7",
            components=[
                DamageComponent(
                    id="base",
                    label="Shortsword",
                    expr="1d6+4",
                    tags=["weapon"],
                ),
                DamageComponent(
                    id="sneak",
                    label="Sneak Attack",
                    expr="3d6",
                    tags=["sneak"],
                    optional=True,
                    option_id="sneak_attack",
                ),
            ],
        )
        engine = DiceEngine()
        without_sneak = AttackRollContext(
            is_crit=False,
            is_nat_20=False,
            enabled_options=frozenset(),
            attack_id=attack.id,
        )
        with_sneak = AttackRollContext(
            is_crit=False,
            is_nat_20=False,
            enabled_options=frozenset({"sneak_attack"}),
            attack_id=attack.id,
        )

        with patch("random.randrange", side_effect=[3, 2, 4, 5, 6]):
            no_sneak = engine.roll_attack_damage(attack, without_sneak, global_pre=[])
            sneak = engine.roll_attack_damage(attack, with_sneak, global_pre=[])

        self.assertEqual(len(no_sneak.components), 1)
        self.assertEqual(len(sneak.components), 2)
        self.assertGreater(sneak.total, no_sneak.total)

    def test_post_roll_multiply_total(self) -> None:
        attack = Attack(
            id="custom",
            to_hit="1d20+5",
            components=[
                DamageComponent(id="base", label="Hit", expr="1d6+2", tags=["weapon"]),
            ],
            post_roll_effects=[
                {
                    "type": "when",
                    "condition": "crit",
                    "effect": {"type": "multiply_total", "factor": 2, "note": "double result"},
                },
            ],
        )
        engine = DiceEngine()
        roll_ctx = AttackRollContext(
            is_crit=True,
            is_nat_20=True,
            enabled_options=frozenset(),
            attack_id=attack.id,
        )

        with patch("random.randrange", return_value=2):
            result = engine.roll_attack_damage(
                attack,
                roll_ctx,
                global_pre=[],
                global_post=[],
            )

        self.assertEqual(result.components[0].total, 10)
        self.assertIn("double result", result.components[0].detail)


if __name__ == "__main__":
    unittest.main()
