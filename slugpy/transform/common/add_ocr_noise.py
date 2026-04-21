import random

from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, ConditionWithCtx, Transform


class AddOCRNoise(Transform):
    def __init__(self, max_alterations: int = 2, condition: Condition | ConditionWithCtx | None = None, p: float = 0.5):
        if max_alterations <= 0:
            raise ValueError("`max_alterations` should be a positive integer.")
        super().__init__(condition, p)
        self.max_alterations = max_alterations
        self.character_mapping = {
            "o": ("0", "O", "D", "q"),
            "O": ("o", "0", "Q"),
            "0": ("@", "o", "O"),
            "l": ("1", "i"),
            "1": ("l", "i", "I"),
            "i": ("1", "l", "j"),
            "j": ("i"),
            "I": ("1"),
            "cl": ("d"),
            "d": ("cl"),
            "rn": ("m"),
            "m": ("rn"),
            "vv": ("w"),
            "VV": ("W"),
            "w": ("vv"),
            "W": ("VV"),
            "v": ("y"),
            "8": ("B"),
            "B": ("8"),
            "5": ("S"),
            "S": ("5"),
            "2": ("Z"),
            "Z": ("2"),
        }

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        for _ in range(self.max_alterations):
            random_func = random.choice([self.add_space, self.remove_space, self.swap_character])
            x.line.line = random_func(x.line.line)
        return x

    def add_space(self, x: str) -> str:
        x_stripped = x.lstrip()
        indent = len(x) - len(x_stripped)
        idx = random.randint(1, len(x_stripped) - 1)
        return (" " * indent) + x_stripped[:idx] + " " + x_stripped[idx:]

    def remove_space(self, x: str) -> str:
        x_stripped = x.lstrip()
        space_indices = [i for i, char in enumerate(x_stripped) if char.isspace()]
        if not space_indices:
            return x
        indent = len(x) - len(x_stripped)
        space_idx = random.choice(space_indices)
        return (" " * indent) + x_stripped[:space_idx] + x_stripped[space_idx + 1 :]

    def swap_character(self, x: str, max_attempts: int = 10) -> str:
        max_attempts = len(self.character_mapping) if max_attempts == -1 else max_attempts
        for pattern in random.choices(list(self.character_mapping.keys()), k=max_attempts):
            if pattern not in x:
                continue
            return x.replace(pattern, random.choice(self.character_mapping[pattern]), count=1)
        return x
