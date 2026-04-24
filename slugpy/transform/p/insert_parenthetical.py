import random
from copy import deepcopy

from slugpy.dataset.label import NAME2LABEL
from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, ConditionWithCtx, Transform
from slugpy.transform.utils import ParentheticalSampler, Sampler, get_indentation


class InsertParenthetical(Transform):
    """
    A `Transform` inserting a parenthetical in place of the script line.

    The default `parentheticals_sampler` is based on a file containing +200 LLM-generated parentheticals.

    Args:
        parentheticals_sampler (Sampler, optional): A sampler for selecting parentheticals. Defaults to ParentheticalSampler.
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(
        self,
        parentheticals_sampler: Sampler = ParentheticalSampler(),
        condition: Condition | ConditionWithCtx | None = None,
        p: float = 0.5,
    ):
        super().__init__(condition, p)
        self.sampler = parentheticals_sampler
        assert "Parenthetical" in NAME2LABEL, "The 'Parenthetical' label should be defined in the dataset labels."
        self.p_label = NAME2LABEL["Parenthetical"]

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply the transform to a script line payload.

        Args:
            x (ScriptLinePayload): The payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with the new parenthetical replacing the original line.
        """
        sl = x.line
        # Store the original line to shift it down the post-context
        original_line = deepcopy(sl)
        indent = get_indentation(sl.line) + random.randint(0, 4)  # `P` usually have a higher indentation than `U`
        parenthetical = self.sampler.sample()
        sl.line = (" " * indent) + parenthetical
        sl.labels = [self.p_label]
        # Shift the post-context one down, starting from the original line
        if x.post_ctx:
            x.post_ctx = [original_line] + x.post_ctx[:-1]
        return x


class InsertParentheticalAfterCharacter(InsertParenthetical):
    """
    A `Transform` inserting a parenthetical after a `C` character line.

    Args:
        parentheticals_filepath (Path | str, optional): Path to the file containing parentheticals, one per line.
            Defaults to DEFAULT_PARENTHETICALS_FILEPATH.
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(self, parentheticals_sampler: Sampler = ParentheticalSampler(), p: float = 0.5):
        c = ConditionWithCtx(Condition(["U"], exclude=["N"]), pre_ctx=[Condition(["C"])])
        super().__init__(parentheticals_sampler, c, p)


class InsertParentheticalBetweenUtterances(InsertParenthetical):
    """
    A `Transform` inserting a parenthetical in the middle of a dialogue, i.e. between two `U` lines.

    Args:
        parentheticals_filepath (Path | str, optional): Path to the file containing parentheticals, one per line.
            Defaults to DEFAULT_PARENTHETICALS_FILEPATH.
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(self, parentheticals_sampler: Sampler = ParentheticalSampler(), p: float = 0.5):
        c = ConditionWithCtx(Condition(["U"], exclude=["N"]), pre_ctx=[Condition(["U"])], post_ctx=[Condition(["U"])])
        super().__init__(parentheticals_sampler, c, p)
