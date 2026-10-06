"""The spelling suggestion core package."""

from spell.core import DEFAULT_MAX_DISTANCE
from spell.core import MAX_WORD_LENGTH
from spell.core import BKTree
from spell.core import SpellError
from spell.core import edit_distance
from spell.core import suggest

__all__ = [
    "BKTree",
    "DEFAULT_MAX_DISTANCE",
    "MAX_WORD_LENGTH",
    "SpellError",
    "edit_distance",
    "suggest",
]
