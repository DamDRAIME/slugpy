def split_at_indentation(x: str) -> tuple[str, int]:
    """Split a string at its indentation level.

    Args:
        x (str): The input string.

    Returns:
        tuple[str, int]: A tuple containing the stripped string and the indentation level.
    """
    indentation = get_indentation(x)
    return x[indentation:], indentation


def get_indentation(x: str) -> int:
    """Get the indentation level of a string.

    Args:
        x (str): The input string.

    Returns:
        int: The indentation level of the string.
    """
    return len(x) - len(x.lstrip())
