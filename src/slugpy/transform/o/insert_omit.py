import random
from copy import deepcopy
from datetime import date
from string import Formatter, ascii_uppercase

from slugpy.dataset.label import NAME2LABEL
from slugpy.dataset.payload import ScriptLinePayload
from slugpy.helpers.utils import get_indentation
from slugpy.transform.base import Condition, ConditionWithCtx, Transform
from slugpy.transform.sampler import OmissionSampler, Sampler


class InsertOmit(Transform):
    """
    A `Transform` inserting irrelevant `O` lines in place of the script line.

    The default `omission_sampler` is based on a file containing +100 LLM-generated templates for omissions lines.

    Args:
        omission_sampler (Sampler, optional): A sampler for selecting omissions. Defaults to OmissionSampler.
        p (float): Probability of applying the transform. Defaults to 0.5.
    """

    def __init__(
        self,
        omission_sampler: Sampler = OmissionSampler(),
        condition: Condition | ConditionWithCtx | None = None,
        p: float = 0.5,
    ):
        super().__init__(condition, p)
        self.sampler = omission_sampler
        assert "Omit" in NAME2LABEL, "The 'Omit' label should be defined in the dataset labels."
        self.o_label = NAME2LABEL["Omit"]

    def apply(self, x: ScriptLinePayload) -> ScriptLinePayload:
        """Apply the transform to a script line payload.

        Args:
            x (ScriptLinePayload): The payload containing the script line.

        Returns:
            ScriptLinePayload: The modified payload with the new omit line replacing the original line.
        """
        sl = x.line
        # Store the original line to shift it down the post-context
        original_line = deepcopy(sl)
        indent = max(0, get_indentation(sl.line) + random.randint(-15, 15))
        omission_template = self.sampler.sample()
        omission = self.format_template(omission_template)
        sl.line = (" " * indent) + omission
        sl.labels = [self.o_label]
        # Shift the post-context one down, starting from the original line
        if x.post_ctx:
            x.post_ctx = [original_line] + x.post_ctx[:-1]
        return x

    def format_template(self, template: str) -> str:
        # Extract field names from the template
        field_names = [field_name for _, field_name, _, _ in Formatter().parse(template) if field_name]
        if not field_names:
            return template

        # Create a mapping of field names to random values
        field_values = {field_name: self.generate_random_value(field_name) for field_name in field_names}
        return template.format(**field_values)

    def generate_random_value(self, field_name: str) -> str:
        match field_name:
            case "date":
                return self.get_date()
            case "day":
                return str(random.randint(1, 31))
            case "month":
                return str(random.randint(1, 12))
            case "year":
                return str(random.randint(1950, 2027))
            case "page_num":
                return str(random.randint(1, 200))
            case "color":
                return self.get_color()
            case "version":
                return self.get_version()
            case "episode_num":
                return f"{random.randint(1, 5)}{random.randint(1, 12):02d}"
            case "episode_title":  # TODO: Get a sampler for episode titles
                return random.choice(["The Beginning", "The End", "A New Hope", "The Mystery", "The Reveal"])
            case "title":  # TODO: Get a sampler for movie titles
                return random.choice(
                    ["The Great Adventure", "Mystery of the Lost City", "Love in Paris", "The Final Battle"]
                )
            case "title_accronym":
                return "".join(random.choices(ascii_uppercase, k=random.randint(2, 5)))
            case "space":
                return " " * random.randint(5, 15)
            case _:
                return f"<{field_name}>"

    def get_date(self) -> str:
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%A, %d %b %Y",
            "%d%m%y",
            "%m-%d",
            "%d %b",
            "%Y",
            "%b %Y",
        ]
        random_format = random.choice(formats)
        d = date.fromordinal(random.randint(date(1950, 1, 1).toordinal(), date(2027, 12, 31).toordinal()))
        return d.strftime(random_format)

    def get_color(self) -> str:
        c = random.choice(
            [
                "red",
                "blue",
                "green",
                "yellow",
                "purple",
                "green",
                "pink",
                "white",
                "goldenrod",
                "buff",
                "salmon",
                "cherry",
                "2nd blue",
                "2nd pink",
            ]
        )
        if (rng := random.random()) < 0.25:
            return c.upper()
        elif rng < 0.5:
            return c.capitalize()
        return c

    def get_version_num(self) -> str:
        rng = random.random()
        if rng < 0.25:
            return str(random.randint(1, 10))
        if rng < 0.5:
            return f"{random.randint(1, 10)}.{random.randint(0, 10)}"
        if rng < 0.75:
            return random.choice(ascii_uppercase) + str(random.randint(1, 10))
        return str(random.randint(1, 10)) + random.choice(ascii_uppercase)
