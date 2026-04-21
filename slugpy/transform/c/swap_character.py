import linecache
import random
from pathlib import Path

from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, Transform


class SwapCharacter(Transform):
    def __init__(self, characters_filepath: Path | str, p: float = 0.5):
        c = Condition(["C"], exclude=["U", "E", "P", "N"])
        super().__init__(c, p)
        self.characters_filepath = Path(characters_filepath)
        with self.characters_filepath.open("rb") as f:
            self.n_lines = sum(1 for _ in f)

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        random_line_idx = random.randint(1, self.n_lines)
        character = linecache.getline(str(self.characters_filepath), random_line_idx).rstrip()
        sl = x.line
        indent = len(sl.line) - len(sl.line.lstrip())
        sl.line = (" " * indent) + character
        return x
