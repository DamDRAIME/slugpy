import random

from slugpy.dataset.label import NAME2LABEL
from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, Transform


class AppendExpression(Transform):
    """
    A `Transform` adding an expression at the end of a `C` character line.

    Args:
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(self, p: float = 0.5):
        c = Condition(["C"], exclude=["U", "N"])
        super().__init__(c, p)
        self.options = [
            "'S VOICE",
            " (OFF)",
            " (PHONE)",
            " (OVER THE PHONE)",
            " OFF-SCREEN",
            " (O/S)",
            " O/S",
            " O.S.",
            " 0/S",
            " 0.S.",
            " o-s",
            " o-c",
            " (o.c.)",
            " (VOICE OVER)",
            " (V.O.)",
            " V.O.",
            " V.0.",
            " (V/O)",
            " (CONT'D)",
            " (CONT`D)",
            " (cont'd)",
            " (cont’d)",
        ]
        assert "Expression" in NAME2LABEL, "The 'Expression' label should be defined in the dataset labels."
        self.e_label = NAME2LABEL["Expression"]

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply the transform to a script line payload.

        Args:
            x (ScriptLinePayload): The payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with the new expression added at the end of the original line.
        """
        sl = x.line
        expression = random.choice(self.options)
        sl.line = sl.line.rstrip() + expression
        sl.labels.append(self.e_label)
        return x
