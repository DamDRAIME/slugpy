import random

from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, Transform


class AddExpression(Transform):
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

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        sl = x.line
        expression = random.choice(self.options)
        sl.line = sl.line.rstrip() + expression
        sl.labels.append("E")
        return x
