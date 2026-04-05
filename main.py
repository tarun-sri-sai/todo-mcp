import logging
from pathlib import Path
from lib.logging_util import setup_logger
from lib.todo import parse_todo, TodoParserError


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")
    logging.getLogger()


def main():
    init_logger()


if __name__ == "__main__":
    main()
