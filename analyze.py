import json
import logging
import sys
import traceback
from argparse import ArgumentParser
from pathlib import Path
from lib.logging_util import setup_logger
from lib.todo.analyzer import TodoAnalyzer
from lib.todo.exceptions import TodoAnalyzerError


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")
    logging.getLogger().setLevel(logging.DEBUG)


def analyze(repo_path, args):
    analyzer = TodoAnalyzer(repo_path)

    if args.command == "get-tasks":
        try:
            tasks = analyzer.get_tasks(args.from_date, args.to_date)
            print(f"tasks in date range {args.from_date} to {args.to_date}:")
            print(json.dumps(tasks, indent=2))
        except TodoAnalyzerError as e:
            logging.critical(f"error getting tasks: {e}")
            logging.debug(traceback.format_exc())
            return 1

    elif args.command == "get-abandoned-tasks":
        try:
            tasks = analyzer.get_abandoned_tasks(
                args.from_date,
                args.to_date,
                args.min_days
            )
            print(
                f"abandoned tasks in date range {args.from_date} to "
                f"{args.to_date} with min days {args.min_days}:"
            )
            print(json.dumps(tasks, indent=2))
        except TodoAnalyzerError as e:
            logging.critical(f"error getting abandoned tasks: {e}")
            logging.debug(traceback.format_exc())
            return 1

    elif args.command == "get-finished-tasks":
        try:
            tasks = analyzer.get_finished_tasks(
                args.from_date,
                args.to_date,
                args.min_days
            )
            print(
                f"finished tasks in date range {args.from_date} to "
                f"{args.to_date} with min days {args.min_days}:"
            )
            print(json.dumps(tasks, indent=2))
        except TodoAnalyzerError as e:
            logging.critical(f"error getting finished tasks: {e}")
            logging.debug(traceback.format_exc())
            return 1


def main():
    init_logger()

    parser = ArgumentParser(
        description="MCP server for todo analysis - test script"
    )
    parser.add_argument(
        "repo_path",
        type=str,
        help="path to the git repository containing todo history"
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="available subcommands"
    )

    get_tasks_parser = subparsers.add_parser(
        "get-tasks",
        help="get all tasks for a date range"
    )
    get_tasks_parser.add_argument(
        "--from-date",
        type=str
    )
    get_tasks_parser.add_argument(
        "--to-date",
        type=str
    )

    get_finished_tasks_parser = subparsers.add_parser(
        "get-finished-tasks",
        help="get finished tasks for a date range"
    )
    get_finished_tasks_parser.add_argument(
        "--from-date",
        type=str
    )
    get_finished_tasks_parser.add_argument(
        "--to-date",
        type=str
    )
    get_finished_tasks_parser.add_argument(
        "--min-days",
        type=int,
        default=0
    )

    get_abandoned_tasks_parser = subparsers.add_parser(
        "get-abandoned-tasks",
        help="get abandoned tasks for a date range"
    )
    get_abandoned_tasks_parser.add_argument(
        "--from-date",
        type=str
    )
    get_abandoned_tasks_parser.add_argument(
        "--to-date",
        type=str
    )
    get_abandoned_tasks_parser.add_argument(
        "--min-days",
        type=int,
        default=0
    )

    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        logging.critical(f"repository path does not exist: {repo_path}")
        return 1

    return analyze(repo_path, args)


if __name__ == "__main__":
    sys.exit(main())
