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
        self.assertIn("scout", output)
        self.assertIn("warrior", output)
        self.assertIn("Shadow", output)
        self.assertIn("Brom", output)

    def test_characters_show_scout(self) -> None:
        code, output, _ = self._run("characters", "show", "scout")
        self.assertEqual(code, 0)
        self.assertIn("blade", output)
        self.assertIn("bonus_strike", output)

    def test_roll_damage_only_with_bonus_strike(self) -> None:
        with patch("random.randrange", side_effect=[2, 1, 3, 4, 5]):
            code, output, _ = self._run(
                "roll",
                "scout",
                "blade",
                "--damage-only",
                "-o",
                "bonus_strike",
            )
        self.assertEqual(code, 0)
        self.assertIn("Blade:", output)
        self.assertIn("Bonus Strike:", output)
        self.assertIn("Total damage:", output)

    def test_roll_warrior_reroll_low_shows_reroll_expression(self) -> None:
        with patch("random.randrange", side_effect=[3, 4]):
            code, output, _ = self._run(
                "roll",
                "warrior",
                "two_handed",
                "--damage-only",
                "-o",
                "reroll_low",
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
        self.assertIn("character not found", err)

    def test_unknown_attack_exits_nonzero(self) -> None:
        code, _, err = self._run("roll", "scout", "missing", "--damage-only")
        self.assertNotEqual(code, 0)
        self.assertIn("attack not found", err)

    def test_unknown_option_exits_nonzero(self) -> None:
        code, _, err = self._run(
            "roll",
            "scout",
            "blade",
            "--damage-only",
            "-o",
            "not_a_real_option",
        )
        self.assertNotEqual(code, 0)
        self.assertIn("unknown option", err)


if __name__ == "__main__":
    unittest.main()
