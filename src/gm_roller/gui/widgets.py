from __future__ import annotations

from gm_roller.models.character import Character


def format_character_summary(character: Character) -> str:
    parts = [f"{character.name} ({character.id})"]
    if character.ac is not None:
        parts.append(f"AC {character.ac}")
    if character.hp is not None:
        parts.append(f"HP {character.hp.current}/{character.hp.max}")
    return " · ".join(parts)
