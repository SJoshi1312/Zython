
KEYWORDS = {
    "zprint", "zif", "zlse", "zhile", "zef",
    "zeturn", "zrue", "zalse", "zone",
    "zand", "zor", "zot", "zfor", "zin", "zreak", "zontinue"
}

TWO_CHAR_OPERATORS = {"==", "!=", ">=", "<="}
ONE_CHAR_OPERATORS = set("+-*/%=<>(),:[].")

def tokenize(source):
    tokens = []
    indent_stack = [0]

    for line_number, line in enumerate(source.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))

        if "\t" in line[:indent]:
            raise SyntaxError(
                f"Use spaces instead of tabs on line {line_number}"
            )

        if indent > indent_stack[-1]:
            indent_stack.append(indent)
            tokens.append(("INDENT", indent, line_number))

        elif indent < indent_stack[-1]:
            while indent < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(("DEDENT", indent, line_number))

            if indent != indent_stack[-1]:
                raise SyntaxError(
                    f"Inconsistent indentation on line {line_number}"
                )

        i = indent

        while i < len(line):
            char = line[i]

            if char.isspace():
                i += 1
                continue

            if char == "#":
                break

            if char in ('"', "'"):
                quote = char
                i += 1
                value = ""

                while i < len(line) and line[i] != quote:
                    if line[i] == "\\" and i + 1 < len(line):
                        i += 1

                    value += line[i]
                    i += 1

                if i == len(line):
                    raise SyntaxError(
                        f"Unclosed string on line {line_number}"
                    )

                i += 1
                tokens.append(("STRING", value, line_number))
                continue

            if char.isdigit():
                start = i

                while i < len(line) and (
                    line[i].isdigit() or line[i] == "."
                ):
                    i += 1

                tokens.append(("NUMBER", line[start:i], line_number))
                continue

            if char.isalpha() or char == "_":
                start = i

                while i < len(line) and (
                    line[i].isalnum() or line[i] == "_"
                ):
                    i += 1

                value = line[start:i]
                kind = "KEYWORD" if value in KEYWORDS else "IDENTIFIER"
                tokens.append((kind, value, line_number))
                continue

            pair = line[i:i + 2]

            if pair in TWO_CHAR_OPERATORS:
                tokens.append(("OPERATOR", pair, line_number))
                i += 2
                continue

            if char in ONE_CHAR_OPERATORS:
                tokens.append(("OPERATOR", char, line_number))
                i += 1
                continue

            raise SyntaxError(
                f"Unexpected character {char!r} on line {line_number}"
            )

        tokens.append(("NEWLINE", None, line_number))

    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(("DEDENT", indent_stack[-1], len(source.splitlines())))

    tokens.append(("EOF", None, len(source.splitlines()) + 1))
    return tokens
