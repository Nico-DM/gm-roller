from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gm_roller.dice.context import AttackRollContext
from gm_roller.dice.engine import DiceEngine
from gm_roller.models.character import Character
from gm_roller.storage import (
    CharacterNotFoundError,
    CharacterStore,
    DuplicateCharacterError,
    default_characters_dir,
)


class TestCharacterStore(unittest.TestCase):
    def setUp(self) -> None:
        self.data_dir = default_characters_dir()

    def test_load_rogue_json(self) -> None:
        rogue_path = self.data_dir / "rogue.json"
        self.assertTrue(rogue_path.is_file(), f"missing sample file: {rogue_path}")

        character = CharacterStore().load(rogue_path)
        self.assertEqual(character.id, "rogue")
        self.assertEqual(character.name, "Shadow")
        self.assertEqual(character.ac, 15)
        self.assertIsNotNone(character.hp)
        assert character.hp is not None
        self.assertEqual(character.hp.current, 28)
        self.assertEqual(character.hp.max, 28)

        attack = character.get_attack("shortsword")
        self.assertEqual(attack.to_hit, "1d20+7")
        self.assertEqual(len(attack.components), 2)
        self.assertTrue(attack.components[1].optional)
        self.assertEqual(attack.components[1].option_id, "sneak_attack")

    def test_load_all_sample_characters(self) -> None:
        store = CharacterStore(self.data_dir)
        characters = store.load_all()
        self.assertEqual(set(characters), {"rogue", "fighter"})
        self.assertEqual(store.list()[0].name, "Brom")
        self.assertEqual(store.list()[1].name, "Shadow")

    def test_get_missing_character_raises(self) -> None:
        store = CharacterStore(self.data_dir)
        store.load_all()
        with self.assertRaises(CharacterNotFoundError):
            store.get("missing")

    def test_duplicate_character_id_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "a.json").write_text(
                json.dumps({"id": "dup", "name": "A", "attacks": []}),
                encoding="utf-8",
            )
            (directory / "b.json").write_text(
                json.dumps({"id": "dup", "name": "B", "attacks": []}),
                encoding="utf-8",
            )
            store = CharacterStore(directory)
            with self.assertRaises(DuplicateCharacterError):
                store.load_all()

    def test_save_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            store = CharacterStore(directory)
            character = Character(id="test", name="Test", attacks=[])
            path = store.save(character)
            self.assertEqual(path, directory / "test.json")
            loaded = store.load(path)
            self.assertEqual(loaded, character)
            self.assertEqual(store.get("test"), character)


class TestCharacterEngineIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.store = CharacterStore(default_characters_dir())
        self.store.load_all()
        self.engine = DiceEngine()

    def test_roll_character_attack_with_sneak_option(self) -> None:
        rogue = self.store.get("rogue")
        roll_ctx = AttackRollContext(
            is_crit=False,
            is_nat_20=False,
            enabled_options=frozenset({"sneak_attack"}),
            attack_id="shortsword",
        )

        with patch("random.randrange", side_effect=[2, 1, 3, 4, 5]):
            result = self.engine.roll_character_attack_damage(
                rogue,
                "shortsword",
                roll_ctx,
                global_pre=[],
            )

        self.assertEqual(len(result.components), 2)
        self.assertEqual(result.components[0].expression, "1d6+4")
        self.assertEqual(result.components[1].expression, "3d6")

    def test_fighter_gwf_appends_reroll_ops(self) -> None:
        fighter = self.store.get("fighter")
        roll_ctx = AttackRollContext(
            is_crit=False,
            is_nat_20=False,
            enabled_options=frozenset({"gwf"}),
            attack_id="greatsword",
        )

        with patch("random.randrange", side_effect=[3, 4]):
            result = self.engine.roll_character_attack_damage(
                fighter,
                "greatsword",
                roll_ctx,
                global_pre=[],
            )

        self.assertEqual(result.components[0].expression, "2d6ro<3+5")


if __name__ == "__main__":
    unittest.main()
