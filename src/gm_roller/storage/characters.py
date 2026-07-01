from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from gm_roller.models.character import Character
from gm_roller.storage.errors import CharacterNotFoundError, DuplicateCharacterError


def default_characters_dir() -> Path:
    """Resolve the default characters directory (cwd, package bundle, or project root)."""
    cwd = Path.cwd() / "data" / "characters"
    if cwd.is_dir():
        return cwd

    here = Path(__file__).resolve()
    bundled = here.parent.parent / "data" / "characters"
    if bundled.is_dir():
        return bundled

    for parent in here.parents:
        candidate = parent / "data" / "characters"
        if candidate.is_dir():
            return candidate

    return Path.cwd() / "data" / "characters"


class CharacterStore:
    def __init__(self, directory: Path | None = None) -> None:
        self._directory = directory or default_characters_dir()
        self._characters: dict[str, Character] = {}

    @property
    def directory(self) -> Path:
        return self._directory

    def load(self, path: Path) -> Character:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Character.model_validate(data)

    def load_all(self) -> dict[str, Character]:
        if not self._directory.is_dir():
            self._characters = {}
            return {}

        characters: dict[str, Character] = {}
        for path in sorted(self._directory.glob("*.json")):
            character = self.load(path)
            if character.id in characters:
                raise DuplicateCharacterError(
                    f"duplicate character id {character.id!r} in {path}"
                )
            characters[character.id] = character

        self._characters = characters
        return dict(characters)

    def reload(self) -> dict[str, Character]:
        return self.load_all()

    def get(self, character_id: str) -> Character:
        if not self._characters:
            self.load_all()
        try:
            return self._characters[character_id]
        except KeyError as exc:
            raise CharacterNotFoundError(character_id) from exc

    def list(self) -> list[Character]:
        if not self._characters:
            self.load_all()
        return sorted(self._characters.values(), key=lambda c: c.name.lower())

    def save(self, character: Character) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / f"{character.id}.json"

        payload = character.model_dump(mode="json")
        text = json.dumps(payload, indent=2) + "\n"

        fd, temp_path = tempfile.mkstemp(
            dir=self._directory,
            prefix=f".{character.id}.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except Exception:
            os.unlink(temp_path)
            raise

        self._characters[character.id] = character
        return path
