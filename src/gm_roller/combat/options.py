from __future__ import annotations

from gm_roller.models.attack import Attack
from gm_roller.models.character import Character


def collect_attack_options(attack: Attack) -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    for component in attack.components:
        if component.optional and component.option_id:
            options.append((component.option_id, component.label))
    return options


def collect_character_options(character: Character) -> set[str]:
    options: set[str] = set()
    for effects in (character.pre_roll_effects, character.post_roll_effects):
        for effect in effects:
            _collect_options_from_effect(effect, options)
    return options


def _collect_options_from_effect(data: dict, options: set[str]) -> None:
    condition = data.get("condition")
    if isinstance(condition, str) and condition.startswith("option:"):
        options.add(condition.removeprefix("option:"))
    inner = data.get("effect")
    if isinstance(inner, dict):
        _collect_options_from_effect(inner, options)


def known_options(character: Character, attack: Attack) -> set[str]:
    known = {option_id for option_id, _ in collect_attack_options(attack)}
    known.update(collect_character_options(character))
    return known


def validate_options(character: Character, attack: Attack, selected: list[str]) -> None:
    known = known_options(character, attack)
    unknown = [option for option in selected if option not in known]
    if unknown:
        known_display = ", ".join(sorted(known)) or "(none)"
        raise ValueError(
            f"unknown option(s): {', '.join(unknown)}. Known options: {known_display}"
        )


def option_label(option_id: str) -> str:
    return option_id.replace("_", " ").title()


def collect_option_choices(character: Character, attack: Attack) -> list[tuple[str, str]]:
    """Return (option_id, display_label) pairs for attack and character-level options."""
    labels = {option_id: label for option_id, label in collect_attack_options(attack)}
    choices: list[tuple[str, str]] = []
    seen: set[str] = set()
    for option_id in sorted(known_options(character, attack)):
        if option_id in seen:
            continue
        seen.add(option_id)
        choices.append((option_id, labels.get(option_id, option_label(option_id))))
    return choices
