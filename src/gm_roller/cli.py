from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gm_roller.combat import (
    RollSettings,
    collect_attack_options,
    collect_character_options,
    format_roll_outcome,
    roll_character_attack,
)
from gm_roller.dice.engine import DiceEngine
from gm_roller.models.character import Character
from gm_roller.storage import CharacterNotFoundError, CharacterStore


def _make_store(data_dir: Path | None) -> CharacterStore:
    return CharacterStore(data_dir) if data_dir else CharacterStore()


def _format_hp(character: Character) -> str:
    if character.hp is None:
        return "-"
    return f"{character.hp.current}/{character.hp.max}"


def cmd_characters_list(store: CharacterStore) -> int:
    characters = store.list()
    if not characters:
        print("No characters found.")
        return 0

    for character in characters:
        ac = character.ac if character.ac is not None else "-"
        print(f"{character.id}\t{character.name}\tAC {ac}\tHP {_format_hp(character)}")
    return 0


def cmd_characters_show(store: CharacterStore, character_id: str) -> int:
    try:
        character = store.get(character_id)
    except CharacterNotFoundError as exc:
        raise SystemExit(f"character not found: {exc}") from exc

    print(f"{character.name} ({character.id})")
    if character.ac is not None:
        print(f"AC: {character.ac}")
    if character.hp is not None:
        print(f"HP: {character.hp.current}/{character.hp.max}")

    char_options = collect_character_options(character)
    if char_options:
        print(f"Character options: {', '.join(sorted(char_options))}")

    print("Attacks:")
    for attack in character.attacks:
        print(f"  {attack.id} — to hit {attack.to_hit}")
        for option_id, label in collect_attack_options(attack):
            print(f"    option: {option_id} ({label})")
    return 0


def cmd_roll(
    store: CharacterStore,
    engine: DiceEngine,
    *,
    character_id: str,
    attack_id: str,
    options: list[str],
    advantage: bool,
    disadvantage: bool,
    crit: bool,
    damage_only: bool,
    no_default_crit: bool,
) -> int:
    try:
        character = store.get(character_id)
    except CharacterNotFoundError as exc:
        raise SystemExit(f"character not found: {exc}") from exc

    try:
        attack = character.get_attack(attack_id)
    except KeyError as exc:
        known = ", ".join(a.id for a in character.attacks) or "(none)"
        raise SystemExit(f"attack not found: {attack_id!r}. Known attacks: {known}") from exc

    try:
        settings = RollSettings(
            options=frozenset(options),
            advantage=advantage,
            disadvantage=disadvantage,
            force_crit=crit,
            damage_only=damage_only,
            no_default_crit=no_default_crit,
        )
        outcome = roll_character_attack(character, attack, engine, settings)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(format_roll_outcome(outcome))
    return 0


def cmd_dice(
    engine: DiceEngine,
    expression: str,
    *,
    advantage: bool,
    disadvantage: bool,
) -> int:
    result = engine.roll_attack(
        expression,
        advantage=advantage,
        disadvantage=disadvantage,
    )
    print(result.result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gm-roller", description="Combat dice roller for tabletop game masters")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="directory containing character JSON files",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    characters_parser = subparsers.add_parser("characters", help="list or show characters")
    characters_sub = characters_parser.add_subparsers(dest="characters_command", required=True)

    characters_sub.add_parser("list", help="list all characters")
    show_parser = characters_sub.add_parser("show", help="show one character")
    show_parser.add_argument("character_id", help="character id")

    roll_parser = subparsers.add_parser("roll", help="roll an attack and damage")
    roll_parser.add_argument("character_id", help="character id")
    roll_parser.add_argument("attack_id", help="attack id")
    roll_parser.add_argument(
        "-o",
        "--option",
        action="append",
        default=[],
        dest="options",
        metavar="OPTION",
        help="enable optional damage or character effect (repeatable)",
    )
    roll_parser.add_argument("--advantage", action="store_true", help="roll attack with advantage")
    roll_parser.add_argument(
        "--disadvantage",
        action="store_true",
        help="roll attack with disadvantage",
    )
    roll_parser.add_argument("--crit", action="store_true", help="force crit on damage roll")
    roll_parser.add_argument(
        "--damage-only",
        action="store_true",
        help="skip attack roll and roll damage only",
    )
    roll_parser.add_argument(
        "--no-default-crit",
        action="store_true",
        help="disable default crit doubling on damage dice",
    )

    dice_parser = subparsers.add_parser("dice", help="roll a raw dice expression")
    dice_parser.add_argument("expression", help='dice expression, e.g. "2d6+4"')
    dice_parser.add_argument("--advantage", action="store_true")
    dice_parser.add_argument("--disadvantage", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    store = _make_store(args.data_dir)
    engine = DiceEngine()

    if args.command == "characters":
        if args.characters_command == "list":
            return cmd_characters_list(store)
        if args.characters_command == "show":
            return cmd_characters_show(store, args.character_id)

    if args.command == "roll":
        return cmd_roll(
            store,
            engine,
            character_id=args.character_id,
            attack_id=args.attack_id,
            options=args.options,
            advantage=args.advantage,
            disadvantage=args.disadvantage,
            crit=args.crit,
            damage_only=args.damage_only,
            no_default_crit=args.no_default_crit,
        )

    if args.command == "dice":
        return cmd_dice(
            engine,
            args.expression,
            advantage=args.advantage,
            disadvantage=args.disadvantage,
        )

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
