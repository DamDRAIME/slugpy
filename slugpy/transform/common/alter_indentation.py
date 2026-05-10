import random

from slugpy.dataset.payload import ScriptLinePayload
from slugpy.helpers.utils import get_indentation, split_at_indentation
from slugpy.transform.base import Condition, ConditionWithCtx, Transform


class AlterIndentation(Transform):
    """
    A `Transform` altering the indentation level of the script line.

    If no context is available, the transform will randomly alter the indentation level by adding or removing up to
    4 spaces. The transform ensures that the indentation level does not become negative.

    If the context contains multiple indentation levels (different than the script line), one of them will be picked
    randomly and used as the new indentation level for the script line.


    Args:
        condition (Condition | ConditionWithCtx | None, optional): Condition to determine if the transform should be
            applied. Defaults to None.
        p (float, optional): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(
        self,
        condition: Condition | ConditionWithCtx | None = None,
        p: float = 0.5,
    ):
        super().__init__(condition, p)

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply indentation alterations to the script line payload.

        Args:
            x (ScriptLinePayload): The input payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with indentation alterations applied.
        """
        x_stripped, indent = split_at_indentation(x.line.line)
        indentations_ctx = self.get_ctx_identation(x)
        try:
            indentations_ctx.remove(indent)
        except KeyError:
            pass
        if indentations_ctx:
            indent = indentations_ctx.pop()
        else:
            indent = max(0, indent + random.randint(-4, 4))
        x.line.line = (" " * indent) + x_stripped
        return x

    def get_ctx_identation(self, x: ScriptLinePayload) -> set[int]:
        """Get the indentation level of the script line's context.

        Args:
            x (ScriptLinePayload): The script line payload.

        Returns:
            set[int]: The indentation levels of the script line's context.
        """
        identations = set()
        for ctx in [x.pre_ctx, x.post_ctx]:
            if ctx is not None:
                for line in ctx:
                    identations.add(get_indentation(line.line))
        return identations
