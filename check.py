import sys
from argparse import ArgumentParser
from lib.todo.parser import parse_todo, TodoParserError


def main():
    parser = ArgumentParser(description="check the syntax of a to-do file")
    parser.add_argument("file", help="the to-do file to check")

    args = parser.parse_args()

    try:
        with open(args.file, "r") as f:
            contents = f.read()
    except Exception as e:
        print("fatal: unable to read file")
        return 1

    try:
        parse_todo(contents)
        print("valid syntax")
        return 0
    except TodoParserError as e:
        print(f"invalid syntax: {e}")
        return 2


if __name__ == '__main__':
    sys.exit(main())
