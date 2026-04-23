import linecache
import random
from pathlib import Path

from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, Transform
from slugpy.transform.utils import get_indentation

DEFAULT_CHARACTERS_FILEPATH = Path(__file__).parent.parent.parent / "data/characters.txt"


class SwapCharacter(Transform):
    """
    A `Transform` swapping the character name in a script line with a random character from a provided file.

    The default `characters_filepath` was created by scraping +3000 movies' credits.

    Args:
        characters_filepath (Path | str, optional): Path to the file containing character names, one per line.
            Defaults to DEFAULT_CHARACTERS_FILEPATH.
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(self, characters_filepath: Path | str = DEFAULT_CHARACTERS_FILEPATH, p: float = 0.5):
        c = Condition(["C"], exclude=["U", "E", "P", "N"])
        super().__init__(c, p)
        self.characters_filepath = Path(characters_filepath)
        with self.characters_filepath.open("rb") as f:
            self.n_lines = sum(1 for _ in f)

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply the transform to a script line payload.

        Args:
            x (ScriptLinePayload): The payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with the character swapped.
        """
        random_line_idx = random.randint(1, self.n_lines)
        character = linecache.getline(str(self.characters_filepath), random_line_idx).rstrip()
        x.line.line = (" " * get_indentation(x.line.line)) + character
        return x
