import random
import string
from collections import defaultdict

from slugpy.dataset.payload import ScriptLine, ScriptLinePayload
from slugpy.transform.base import Condition, ConditionWithCtx, Transform


class AddOCRNoise(Transform):
    """
    A `Transform` simulating OCR noise by randomly altering characters, adding or removing spaces in script lines.

    Args:
        apply_to_ctx (bool, optional): Whether to apply the transform to the script line's context. Defaults to False.
        max_alterations_per_line (int, optional): Maximum number of noise alterations to apply per line. Must be
            positive. Defaults to 2.
        condition (Condition | ConditionWithCtx | None, optional): Condition to determine if the transform should be
            applied. Defaults to None.
        p (float, optional): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(
        self,
        apply_to_ctx: bool = False,
        max_alterations_per_line: int = 2,
        condition: Condition | ConditionWithCtx | None = None,
        p: float = 0.5,
    ):
        if max_alterations_per_line <= 0:
            raise ValueError("`max_alterations_per_line` should be a positive integer.")
        super().__init__(condition, p)
        self.apply_to_ctx = apply_to_ctx
        self.max_alterations_per_line = max_alterations_per_line
        # Mapping of often confused characters in OCR pipelines.
        common_confusions = [
            ["o", "0", "O", "D", "q", "Q", "@"],
            ["l", "1", "i", "I", "j"],
            ["cl", "d"],
            ["rn", "m"],
            ["vv", "VV", "W", "w"],
            ["v", "y"]["8", "B"],
            ["5", "S"],
            ["2", "Z"],
            ["-", "—", "–"],
            ["'", "`", "′", "‘", "’"],
        ]
        # Build bidirectional mapping
        self.confusions_mapping = defaultdict(list)
        for confusions in common_confusions:
            for _ in range(len(confusions)):
                key = confusions.pop(0)
                self.confusions_mapping[key] = confusions
                confusions.append(key)

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply OCR noise alterations to the script line payload.

        Args:
            x (ScriptLinePayload): The input payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with noise applied.
        """
        x.line = self.apply_to_line(x.line)
        if self.apply_to_ctx:
            for ctx in [x.pre_ctx, x.post_ctx]:
                if ctx:
                    for line in ctx:
                        line = self.apply_to_line(line)
        return x

    def apply_to_line(self, x: ScriptLine) -> ScriptLine:
        """Apply OCR-like alterations to the script line.

        Args:
            x (ScriptLine): The input script line.

        Returns:
            ScriptLine: The modified script line with noise applied.
        """
        for _ in range(self.max_alterations_per_line):
            random_func = random.choice(
                [
                    self.add_space,
                    self.remove_space,
                    self.swap_character,
                    self.duplicate_alphanumeric,
                    self.remove_alphanumeric,
                ]
            )
            x.line = random_func(x.line)
        return x

    def add_space(self, x: str) -> str:
        """Add a random space to the string, preserving leading indentation.

        Args:
            x (str): The input string.

        Returns:
            str: The string with an added space.
        """
        return self.add_character(x, " ")

    def remove_space(self, x: str) -> str:
        """Remove a random space from the string, preserving leading indentation.

        Args:
            x (str): The input string.

        Returns:
            str: The string with a space removed, or unchanged if no spaces.
        """
        return self.remove_character(x, filter_func=str.isspace())

    def swap_character(self, x: str, max_attempts: int = 12) -> str:
        """Swap a character or pattern with a similar-looking one based on the mapping.

        Args:
            x (str): The input string.
            max_attempts (int): Maximum attempts to find a pattern to replace. If -1, tries with all patterns. If no
                attempts are successful, returns the original string. Defaults to 12.

        Returns:
            str: The string with a character swapped, or unchanged if no match.
        """
        max_attempts = len(self.confusions_mapping) if max_attempts == -1 else max_attempts
        for pattern in random.choices(list(self.confusions_mapping.keys()), k=max_attempts):
            if pattern not in x:
                continue
            return x.replace(pattern, random.choice(self.confusions_mapping[pattern]), count=1)
        return x

    def duplicate_alphanumeric(self, x: str) -> str:
        """Duplicate a random alphanumeric character in the string, preserving leading indentation.

        Args:
            x (str): The input string.
        Returns:
            str: The string with a character duplicated, or unchanged if no characters.
        """
        x_stripped = x.lstrip()
        indent = len(x) - len(x_stripped)
        indices = list(range(len(x_stripped)))
        idx = random.choice(indices)
        return (" " * indent) + x_stripped[: idx + 1] + x_stripped[idx:]

    def remove_alphanumeric(self, x: str) -> str:
        """Remove a random alphanumeric character from the string, preserving leading indentation.

        Args:
            x (str): The input string.

        Returns:
            str: The string with an alphanumeric character removed, or unchanged if no alphanumeric characters.
        """
        return self.remove_character(x, filter_func=str.isalnum)

    def add_alphanumeric(self, x: str) -> str:
        """Add a random alphanumeric character at a random position in the string, preserving leading indentation.

        Args:
            x (str): The input string.

        Returns:
            str: The string with a random alphanumeric character added.
        """
        char = random.choice(string.ascii_letters + string.digits)
        return self.add_character(x, char)

    def remove_character(self, x: str, filter_func: callable = None) -> str:
        """Remove a random character from the string, preserving leading indentation.

        Args:
            x (str): The input string.
            filter_func (callable, optional): A function to filter characters to remove. If None, removes any character. Defaults to None.

        Returns:
            str: The string with a character removed, or unchanged if no characters match the filter.
        """
        x_stripped = x.lstrip()
        indent = len(x) - len(x_stripped)
        if filter_func:
            indices = [i for i, char in enumerate(x_stripped) if filter_func(char)]
        else:
            indices = list(range(len(x_stripped)))
        if not indices:
            return x
        idx = random.choice(indices)
        return (" " * indent) + x_stripped[:idx] + x_stripped[idx + 1 :]

    def add_character(self, x: str, char: str) -> str:
        """Add a character at a random position in the string, preserving leading indentation.

        Args:
            x (str): The input string.
            char (str): The character to add.

        Returns:
            str: The string with the character added.
        """
        x_stripped = x.lstrip()
        indent = len(x) - len(x_stripped)
        idx = random.randint(0, len(x_stripped))
        return (" " * indent) + x_stripped[:idx] + char + x_stripped[idx:]
