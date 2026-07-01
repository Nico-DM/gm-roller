from __future__ import annotations

import re
from dataclasses import dataclass, replace

_DICE_PART = re.compile(r"^(\d+)d(\d+)(.*)$")
_INT_PART = re.compile(r"^[+-]?\d+$")


@dataclass(frozen=True)
class DieTerm:
    count: int
    sides: int
    ops: str = ""

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError(f"die count must be >= 1, got {self.count}")
        if self.sides < 1:
            raise ValueError(f"die sides must be >= 1, got {self.sides}")


@dataclass(frozen=True)
class ExpressionSpec:
    dice: tuple[DieTerm, ...] = ()
    modifier: int = 0

    def compile(self) -> str:
        if not self.dice:
            return str(self.modifier)
        dice_str = "+".join(f"{d.count}d{d.sides}{d.ops}" for d in self.dice)
        if self.modifier > 0:
            return f"{dice_str}+{self.modifier}"
        if self.modifier < 0:
            return f"{dice_str}{self.modifier}"
        return dice_str

    def with_dice(self, dice: list[DieTerm]) -> ExpressionSpec:
        return replace(self, dice=tuple(dice))

    def with_modifier(self, modifier: int) -> ExpressionSpec:
        return replace(self, modifier=modifier)


def parse_expr(expr: str) -> ExpressionSpec:
    """Parse simple NdS expressions with optional modifiers (e.g. 1d8+1d6+3)."""
    cleaned = expr.replace(" ", "")
    if not cleaned:
        raise ValueError("empty expression")

    dice: list[DieTerm] = []
    modifier = 0
    for part in cleaned.split("+"):
        dice_match = _DICE_PART.match(part)
        if dice_match:
            dice.append(
                DieTerm(
                    int(dice_match.group(1)),
                    int(dice_match.group(2)),
                    dice_match.group(3) or "",
                )
            )
            continue
        if _INT_PART.match(part):
            modifier += int(part)
            continue
        raise ValueError(f"cannot parse expression part: {part!r}")

    return ExpressionSpec(tuple(dice), modifier)


def die_terms_from_dicts(items: list[dict]) -> list[DieTerm]:
    return [
        DieTerm(count=item["count"], sides=item["sides"], ops=item.get("ops", ""))
        for item in items
    ]
