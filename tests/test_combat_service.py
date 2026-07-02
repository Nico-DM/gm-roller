from __future__ import annotations

import unittest
from unittest.mock import patch

from gm_roller.combat import RollSettings, roll_character_attack
from gm_roller.dice.engine import DiceEngine
from gm_roller.models.attack import Attack, DamageComponent
from gm_roller.storage import CharacterStore, default_characters_dir


class TestCombatService(unittest.TestCase):
    def setUp(self) -> None:
        self.store = CharacterStore(default_characters_dir())
        self.store.load_all()
        self.engine = DiceEngine()

    def test_roll_with_bonus_option(self) -> None:
        scout = self.store.get("scout")
        attack = scout.get_attack("blade")
        settings = RollSettings(options=frozenset({"bonus_strike"}), damage_only=True)

        with patch("random.randrange", side_effect=[2, 1, 3, 4, 5]):
            outcome = roll_character_attack(scout, attack, self.engine, settings)

        self.assertIsNone(outcome.attack_line)
        self.assertEqual(len(outcome.components), 2)
        self.assertGreater(outcome.total, 0)

    def test_roll_with_reroll_low_option(self) -> None:
        warrior = self.store.get("warrior")
        attack = warrior.get_attack("two_handed")
        settings = RollSettings(options=frozenset({"reroll_low"}), damage_only=True)

        with patch("random.randrange", side_effect=[3, 4]):
            outcome = roll_character_attack(warrior, attack, self.engine, settings)

        self.assertEqual(outcome.components[0].expression, "2d6ro<3+5")

    def test_roll_attack_line_when_not_damage_only(self) -> None:
        scout = self.store.get("scout")
        attack = scout.get_attack("blade")
        settings = RollSettings()

        with patch("random.randrange", return_value=10):
            outcome = roll_character_attack(scout, attack, self.engine, settings)

        self.assertIsNotNone(outcome.attack_line)
        self.assertIn("=", outcome.attack_line or "")

    def test_crit_doubles_dice_by_default(self) -> None:
        attack = Attack(
            id="two_handed",
            to_hit="1d20+8",
            components=[
                DamageComponent(
                    id="base",
                    label="Two-handed blade",
                    expr="2d6+5",
                    tags=["weapon"],
                ),
            ],
        )
        scout = self.store.get("scout")
        settings = RollSettings(force_crit=True, damage_only=True)

        with patch("random.randrange", side_effect=[3, 4, 5, 2]):
            outcome = roll_character_attack(scout, attack, self.engine, settings)

        self.assertEqual(outcome.components[0].expression, "4d6+5")

    def test_unknown_option_raises(self) -> None:
        scout = self.store.get("scout")
        attack = scout.get_attack("blade")
        settings = RollSettings(options=frozenset({"not_real"}), damage_only=True)

        with self.assertRaises(ValueError):
            roll_character_attack(scout, attack, self.engine, settings)


if __name__ == "__main__":
    unittest.main()
