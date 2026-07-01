from __future__ import annotations

import d20
from d20 import AdvType, CritType, SimpleStringifier

from gm_roller.dice.context import AttackRollContext, RollContext
from gm_roller.dice.effects import DEFAULT_PRE_ROLL_EFFECTS, PostRollEffect, PreRollEffect
from gm_roller.dice.pipeline import merge_effects, run_post_roll, run_pre_roll
from gm_roller.dice.results import ComponentRoll, DamageResult
from gm_roller.dice.spec import parse_expr
from gm_roller.models.attack import Attack, DamageComponent


class DiceEngine:
    def __init__(self) -> None:
        self._roller = d20.Roller()
        self._plain = SimpleStringifier()

    def roll_expression(
        self,
        expr: str,
        *,
        advantage: AdvType = AdvType.NONE,
    ) -> d20.RollResult:
        return self._roller.roll(expr, stringifier=self._plain, advantage=advantage)

    def roll_attack(
        self,
        to_hit: str,
        *,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> d20.RollResult:
        adv = AdvType.NONE
        if advantage and not disadvantage:
            adv = AdvType.ADV
        elif disadvantage and not advantage:
            adv = AdvType.DIS
        return self.roll_expression(to_hit, advantage=adv)

    def attack_roll_context_from_result(
        self,
        attack: Attack,
        attack_result: d20.RollResult,
        enabled_options: frozenset[str],
    ) -> AttackRollContext:
        return AttackRollContext(
            is_crit=attack_result.crit == CritType.CRIT,
            is_nat_20=attack_result.crit == CritType.CRIT,
            enabled_options=enabled_options,
            attack_id=attack.id,
        )

    def roll_component(
        self,
        component: DamageComponent,
        *,
        ctx: RollContext,
        pre_effects: list[PreRollEffect],
        post_effects: list[PostRollEffect],
    ) -> ComponentRoll:
        spec = parse_expr(component.expr)
        spec = run_pre_roll(spec, ctx, pre_effects)
        expr = spec.compile()
        d20_result = self.roll_expression(expr)

        roll = ComponentRoll(
            label=component.label,
            expression=expr,
            total=d20_result.total,
            detail=d20_result.result,
            tags=component.tag_set,
            d20_result=d20_result,
        )
        return run_post_roll(roll, ctx, post_effects)

    def roll_attack_damage(
        self,
        attack: Attack,
        roll_ctx: AttackRollContext,
        *,
        global_pre: list[PreRollEffect] | None = None,
        global_post: list[PostRollEffect] | None = None,
        character_pre: list[PreRollEffect] | None = None,
        character_post: list[PostRollEffect] | None = None,
    ) -> DamageResult:
        pre_effects = merge_effects(
            list(DEFAULT_PRE_ROLL_EFFECTS if global_pre is None else global_pre),
            list(character_pre or []),
            attack.parsed_pre_roll_effects(),
        )
        post_effects = merge_effects(
            [] if global_post is None else list(global_post),
            list(character_post or []),
            attack.parsed_post_roll_effects(),
        )

        components: list[ComponentRoll] = []
        for component in attack.active_components(roll_ctx.enabled_options):
            ctx = roll_ctx.for_component(component.id, component.tag_set)
            components.append(
                self.roll_component(
                    component,
                    ctx=ctx,
                    pre_effects=pre_effects,
                    post_effects=post_effects,
                )
            )

        total = sum(component.total for component in components)
        return DamageResult(total=total, components=tuple(components))
