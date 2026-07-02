from __future__ import annotations

from dataclasses import dataclass

from d20 import CritType

from gm_roller.combat.options import validate_options
from gm_roller.dice.context import AttackRollContext
from gm_roller.dice.engine import DiceEngine
from gm_roller.dice.results import ComponentRoll
from gm_roller.models.attack import Attack
from gm_roller.models.character import Character


@dataclass(frozen=True)
class RollSettings:
    options: frozenset[str] = frozenset()
    advantage: bool = False
    disadvantage: bool = False
    force_crit: bool = False
    damage_only: bool = False
    no_default_crit: bool = False


@dataclass(frozen=True)
class RollOutcome:
    attack_line: str | None
    components: tuple[ComponentRoll, ...]
    total: int


def roll_character_attack(
    character: Character,
    attack: Attack,
    engine: DiceEngine,
    settings: RollSettings,
) -> RollOutcome:
    validate_options(character, attack, list(settings.options))
    global_pre = [] if settings.no_default_crit else None
    attack_line: str | None = None

    if settings.damage_only:
        roll_ctx = AttackRollContext(
            is_crit=settings.force_crit,
            is_nat_20=settings.force_crit,
            enabled_options=settings.options,
            attack_id=attack.id,
        )
    else:
        attack_result = engine.roll_attack(
            attack.to_hit,
            advantage=settings.advantage,
            disadvantage=settings.disadvantage,
        )
        attack_line = attack_result.result
        is_crit = settings.force_crit or attack_result.crit == CritType.CRIT
        roll_ctx = AttackRollContext(
            is_crit=is_crit,
            is_nat_20=attack_result.crit == CritType.CRIT,
            enabled_options=settings.options,
            attack_id=attack.id,
        )

    damage = engine.roll_attack_damage(
        attack,
        roll_ctx,
        global_pre=global_pre,
        character_pre=character.parsed_pre_roll_effects(),
        character_post=character.parsed_post_roll_effects(),
    )
    return RollOutcome(
        attack_line=attack_line,
        components=damage.components,
        total=damage.total,
    )


def format_roll_outcome(outcome: RollOutcome) -> str:
    lines: list[str] = []
    if outcome.attack_line is not None:
        lines.append(f"Attack: {outcome.attack_line}")
    for component in outcome.components:
        lines.append(f"  {component.label}: {component.detail}")
    lines.append(f"Total damage: {outcome.total}")
    return "\n".join(lines)
