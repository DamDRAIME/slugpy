from slugpy.dataset.label import NAME2LABEL
from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, Transform
from slugpy.transform.utils import ExtensionSampler, Sampler


class AppendExpression(Transform):
    """
    A `Transform` adding an expression at the end of a `C` character line.

    Args:
        extensions_sampler (Sampler, optional): A sampler for selecting extensions. Defaults to ExtensionSampler.
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(self, extensions_sampler: Sampler = ExtensionSampler(), p: float = 0.5):
        c = Condition(["C"], exclude=["U", "N"])
        super().__init__(c, p)
        self.sampler = extensions_sampler
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
        expression = self.sampler.sample()
        sl.line = sl.line.rstrip() + expression
        sl.labels.append(self.e_label)
        return x
