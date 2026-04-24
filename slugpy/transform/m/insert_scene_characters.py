import random
from copy import deepcopy

from slugpy.dataset.label import NAME2LABEL
from slugpy.dataset.payload import ScriptLine, ScriptLinePayload
from slugpy.transform.base import Condition, ConditionWithCtx, Transform
from slugpy.transform.utils import CharacterSampler, Sampler, get_indentation


class InsertSceneCharacters(Transform):
    """
    A `Transform` inserting a scene character(s) after a scene heading `S` line.

    The default `characters_sampler` is based on a file containing character names scraped +3000 movies' credits.

    Args:
        characters_sampler (Sampler, optional): A sampler for selecting character names. Defaults to CharacterSampler.
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(self, characters_sampler: Sampler = CharacterSampler(), p: float = 0.5):
        c = ConditionWithCtx(["O"], pre_ctx=[Condition(["S"])])
        super().__init__(c, p)
        self.sampler = characters_sampler
        assert "Meta" in NAME2LABEL, "The 'Meta' label should be defined in the dataset labels."
        self.m_label = NAME2LABEL["Meta"]
        self.sep_options = [" / ", " & ", ", ", " - "]

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply the transform to a script line payload.

        Args:
            x (ScriptLinePayload): The payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with the new scene characters meta line replacing the original line.
        """
        original_line = deepcopy(x.line)

        # Create a new line with the inserted characters
        scene_heading_indent = get_indentation(x.pre_ctx[-1].line)
        n_characters = random.randint(1, 3)
        characters = self.sampler.sample_n(n_characters)
        sep = random.choice(self.sep_options)
        x.line.line = (" " * scene_heading_indent) + sep.join(characters)
        x.line.labels = [self.m_label]

        # Update the pre and post contexts
        if random.random() < 0.5:
            # Add a blank line between the scene heading `S` line and the new meta line with the characters.
            x.pre_ctx = x.pre_ctx[1:] + [ScriptLine(line="", idx=x.pre_ctx[-1].idx, labels=[NAME2LABEL["Omit"]])]

        if x.post_ctx[0].labels[0] != NAME2LABEL["Omit"]:
            x.post_ctx = [original_line] + x.post_ctx[:-1]

        return x
