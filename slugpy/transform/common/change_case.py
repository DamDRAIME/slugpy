import random

from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, ConditionWithCtx, Transform


class ChangeCase(Transform):
    def __init__(self, condition: Condition | ConditionWithCtx | None = None, p: float = 0.5):
        super().__init__(condition, p)

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply the transform to a script line payload.

        Args:
            x (ScriptLinePayload): The payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with the case changed.
        """
        lower_count, upper_count = 0, 0
        for ch in x.line.line.strip():
            if ch.isspace():
                continue
            if ch.islower():
                lower_count += 1
            else:
                upper_count += 1

        # If there are no cased characters, do nothing
        if lower_count == 0 and upper_count == 0:
            return x

        # If line is predominantly lowercased, convert to uppercase, otherwise to lowercase
        x.line.line = x.line.line.upper() if lower_count >= upper_count else x.line.line.lower()
        return x
