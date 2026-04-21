import random

from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, ConditionWithCtx, Transform


class ChangeCase(Transform):
    def __init__(self, condition: Condition | ConditionWithCtx | None = None, p: float = 0.5):
        super().__init__(condition, p)

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        random_func = random.choice([lambda x: x.lower(), lambda x: x.upper()])
        x.line.line = random_func(x.line.line)
        return x
