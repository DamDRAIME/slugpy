def deduplicate_chars(x: str) -> str:
    newline = x.endswith("\n")
    x = x.rstrip()
    n = len(x) - 1
    deduplicated = ""
    i = 0
    while i < n:
        if x[i] == " ":  # Whitespaces are not duplicated
            deduplicated += " "
            i += 1
        elif (char := x[i]) == x[i + 1]:
            deduplicated += char
            i += 2
        else:
            return x + "\n" if newline else ""
    return deduplicated + "\n" if newline else ""
