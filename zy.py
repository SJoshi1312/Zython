
from pathlib import Path
import sys

from lexer import tokenize
from parser import Parser
from interpreter import execute


def main():
    if len(sys.argv) != 2:
        print("Usage: python zy.py <file.zy>")
        return

    path = Path(sys.argv[1])

    if path.suffix != ".zy":
        print("Error: Zython files must use the .zy extension.")
        return

    try:
        source = path.read_text(encoding="utf-8")
        tokens = tokenize(source)
        program = Parser(tokens).parse()    
        execute(program)

    except (SyntaxError, RuntimeError) as error:
        print(f"Zython error: {error}")


if __name__ == "__main__":
    main()


