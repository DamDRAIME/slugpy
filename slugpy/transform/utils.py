import linecache
from pathlib import Path
from random import random

DEFAULT_CHARACTERS_FILEPATH = Path(__file__).parent.parent.parent / "data/characters.txt"
DEFAULT_PARENTHETICALS_FILEPATH = Path(__file__).parent.parent.parent / "data/parentheticals.txt"


def split_at_indentation(x: str) -> tuple[str, int]:
    """Split a string at its indentation level.

    Args:
        x (str): The input string.

    Returns:
        tuple[str, int]: A tuple containing the stripped string and the indentation level.
    """
    indentation = get_indentation(x)
    return x[indentation:], indentation


def get_indentation(x: str) -> int:
    """Get the indentation level of a string.

    Args:
        x (str): The input string.

    Returns:
        int: The indentation level of the string.
    """
    return len(x) - len(x.lstrip())


class Sampler:
    """A simple sampler to sample, with replacement, from a file containing one item per line."""

    def __init__(self, filepath: Path | str):
        self.filepath = Path(filepath)
        with self.filepath.open("rb") as f:
            self.n_lines = sum(1 for _ in f)

    def sample(self) -> str:
        random_line_idx = random.randint(1, self.n_lines)
        return linecache.getline(str(self.filepath), random_line_idx).rstrip()

    def sample_n(self, n: int) -> list[str]:
        return [self.sample() for _ in range(n)]


class CharacterSampler(Sampler):
    """A sampler to sample characters from a file containing one character name per line."""

    def __init__(self, filepath: Path | str = DEFAULT_CHARACTERS_FILEPATH):
        super().__init__(filepath)


class ParentheticalSampler(Sampler):
    """A sampler to sample parentheticals from a file containing one parenthetical per line."""

    def __init__(self, filepath: Path | str = DEFAULT_PARENTHETICALS_FILEPATH):
        super().__init__(filepath)
