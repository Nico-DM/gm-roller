from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from gm_roller.cli import main
from gm_roller.storage import default_characters_dir


class TestCli(unittest.TestCase):
    def _run(self, *args: str) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        data_dir = default_characters_dir()
        argv = ["--data-dir", str(data_dir), *args]
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = main(argv)
            except SystemExit as exc:
                if isinstance(exc.code, int):
                    code = exc.code
                elif exc.code is None:
                    code = 0
                else:
                    code = 1
                    err.write(f"{exc.code}\n")
        return code, out.getvalue(), err.getvalue()

    def test_characters_list_includes_samples(self) -> None:
        code, output, _ = self._run("characters", "list")
        self.assertEqual(code, 0)
        self.assertIn("rogue", output)
        self.assertIn("fighter", output)
        self.assertIn("Shadow", output)
        self.assertIn("Brom", output)

    def test_characters_show_rogue(self) -> None:
        code, output, _ = self._run("characters", "show", "rogue")
        self.assertEqual(code, 0)
        self.assertIn("shortsword", output)
        self.assertIn("sneak_attack", output)

    def test_roll_damage_only_with_sneak_attack(self) -> None:
        with patch("random.randrange", side_effect=[2, 1, 3, 4, 5]):
            code, output, _ = self._run(
                "roll",
                "rogue",
                "shortsword",
                "--damage-only",
                "-o",
                "sneak_attack",
            )
        self.assertEqual(code, 0)
        self.assertIn("Shortsword:", output)
        self.assertIn("Sneak Attack:", output)
        self.assertIn("Total damage:", output)

    def test_roll_fighter_gwf_shows_reroll_expression(self) -> None:
        with patch("random.randrange", side_effect=[3, 4]):
            code, output, _ = self._run(
                "roll",
                "fighter",
                "greatsword",
                "--damage-only",
                "-o",
                "gwf",
            )
        self.assertEqual(code, 0)
        self.assertIn("2d6ro<3", output)

    def test_dice_expression(self) -> None:
        with patch("random.randrange", return_value=2):
            code, output, _ = self._run("dice", "2d6+4")
        self.assertEqual(code, 0)
        self.assertIn("= 10", output)

    def test_unknown_character_exits_nonzero(self) -> None:
        code, _, err = self._run("characters", "show", "missing")
        self.assertNotEqual(code, 0)
        combined = err
        self.assertIn("character not found", combined)

    def test_unknown_attack_exits_nonzero(self) -> None:
        code, _, err = self._run("roll", "rogue", "missing", "--damage-only")
        self.assertNotEqual(code, 0)
        self.assertIn("attack not found", err)

    def test_unknown_option_exits_nonzero(self) -> None:
        code, _, err = self._run(
            "roll",
            "rogue",
            "shortsword",
            "--damage-only",
            "-o",
            "not_a_real_option",
        )
        self.assertNotEqual(code, 0)
        self.assertIn("unknown option", err)


if __name__ == "__main__":
    unittest.main()
