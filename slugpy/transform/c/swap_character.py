from slugpy.dataset.payload import ScriptLinePayload
from slugpy.transform.base import Condition, Transform
from slugpy.transform.utils import CharacterSampler, Sampler, get_indentation


class SwapCharacter(Transform):
    """
    A `Transform` swapping the character name in a script line with a random character from a provided file.

    The default `characters_sampler` is based on a file containing character names scraped +3000 movies' credits.

    Args:
        characters_sampler (Sampler, optional): A sampler for selecting character names. Defaults to CharacterSampler.
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(self, characters_sampler: Sampler = CharacterSampler(), p: float = 0.5):
        c = Condition(["C"], exclude=["U", "E", "P", "N"])
        super().__init__(c, p)
        self.sampler = characters_sampler

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply the transform to a script line payload.

        Args:
            x (ScriptLinePayload): The payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with the character swapped.
        """
        character = self.sampler.sample()
        x.line.line = (" " * get_indentation(x.line.line)) + character
        return x
