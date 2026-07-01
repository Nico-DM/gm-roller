# gm-roller

A Python combat dice roller for tabletop game masters. Load character definitions from JSON, roll attacks with optional modifiers, and get a clear breakdown of each damage component.

Version **1.0.0**

## Features

- Dice engine powered by [d20](https://github.com/avrae/d20) with support for advantage, rerolls, and composable pre/post-roll effects
- Character roster stored as one JSON file per character
- CLI for listing characters and rolling attacks at the table
- Effect pipeline per attack: double dice on crit, add bonus dice, change die sizes, multiply totals, and more

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Install

```bash
git clone https://github.com/Nico-DM/gm-roller.git
cd gm-roller
uv sync
```

Install as a command:

```bash
uv sync
uv run gm-roller --help
```

## Quick start

List characters from `data/characters/`:

```bash
uv run gm-roller characters list
```

Show one character's attacks and optional toggles:

```bash
uv run gm-roller characters show scout
```

Roll an attack (to-hit, then damage):

```bash
uv run gm-roller roll scout blade -o bonus_strike
```

Roll damage only (when the hit is already known):

```bash
uv run gm-roller roll warrior two_handed -o reroll_low --damage-only
```

Roll a raw expression:

```bash
uv run gm-roller dice "2d6+4"
```

Use a custom character directory:

```bash
uv run gm-roller --data-dir /path/to/characters characters list
```

## Character files

Each character is a JSON file in `data/characters/` (filename should match the `id` field).

```json
{
  "id": "scout",
  "name": "Shadow",
  "ac": 15,
  "hp": { "current": 28, "max": 28 },
  "pre_roll_effects": [],
  "post_roll_effects": [],
  "attacks": [
    {
      "id": "blade",
      "to_hit": "1d20+7",
      "components": [
        {
          "id": "base",
          "label": "Blade",
          "expr": "1d6+4",
          "tags": ["weapon", "melee"]
        },
        {
          "id": "bonus",
          "label": "Bonus Strike",
          "expr": "3d6",
          "tags": ["bonus"],
          "optional": true,
          "option_id": "bonus_strike"
        }
      ],
      "pre_roll_effects": [],
      "post_roll_effects": []
    }
  ]
}
```

### Optional damage components

Set `"optional": true` and an `"option_id"` on a component, then pass `-o option_id` to the `roll` command to include it.

### Effects

Effects can be defined at the character or attack level. Pre-roll effects transform dice expressions before rolling; post-roll effects modify totals afterward.

Example — reroll low damage dice when an option is enabled:

```json
{
  "type": "when",
  "condition": "option:reroll_low",
  "effect": {
    "type": "append_die_ops",
    "ops": "ro<3",
    "target_tags": ["weapon"]
  }
}
```

Supported pre-roll effect types: `when`, `double_dice`, `add_dice`, `change_die_sides`, `append_die_ops`.

Supported post-roll effect types: `when`, `multiply_total`, `set_minimum_total`, `add_flat_bonus`.

Conditions: `always`, `crit`, `nat_20`, `option:<id>`, `tag:<tag>`, `not:<condition>`.

## Development

```bash
uv sync --group dev
uv run pytest
```

## Project layout

```
data/characters/     Sample character JSON files
src/gm_roller/
  cli.py               Command-line interface
  dice/                Dice engine and effect pipeline
  models/              Pydantic models (Character, Attack, …)
  storage/             JSON character loader
tests/
```
