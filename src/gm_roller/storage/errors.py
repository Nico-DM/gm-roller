class CharacterNotFoundError(KeyError):
    """Raised when a character id is not in the store."""


class DuplicateCharacterError(ValueError):
    """Raised when two character files share the same id."""
