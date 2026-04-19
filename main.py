import argparse
import json
import logging
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from lib.logging_util import setup_logger
from lib.todo.analyzer import TodoAnalyzer
from lib.todo.exceptions import TodoAnalyzerError


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")
    logging.getLogger()


def init_mcp(repo_path):
    mcp = FastMCP("todo-mcp", json_response=True)
    analyzer = TodoAnalyzer(repo_path)

    @mcp.tool()
    def get_tasks(
        from_date: str | None = None,
        to_date: str | None = None
    ) -> str:
        """
        Get all tasks for a date range.

        Args:
            from_date: Start date in YYYY-MM-DD format (optional)
            to_date: End date in YYYY-MM-DD format (optional)

        Returns:
            JSON string containing all tasks in the date range
        """
        try:
            tasks = analyzer.get_tasks(from_date, to_date)
            return json.dumps(tasks, indent=2, default=str)
        except TodoAnalyzerError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def get_abandoned_tasks(
        from_date: str | None = None,
        to_date: str | None = None,
        min_days: int = 0
    ) -> str:
        """
        Get abandoned tasks for a date range.

        Args:
            from_date: Start date in YYYY-MM-DD format (optional)
            to_date: End date in YYYY-MM-DD format (optional)
            min_days: Minimum number of days a task was tracked (default: 0)

        Returns:
            JSON string containing abandoned tasks in the date range
        """
        try:
            tasks = analyzer.get_abandoned_tasks(from_date, to_date, min_days)
            return json.dumps(tasks, indent=2, default=str)
        except TodoAnalyzerError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def get_finished_tasks(
        from_date: str | None = None,
        to_date: str | None = None,
        min_days: int = 0
    ) -> str:
        """
        Get finished tasks for a date range.

        Args:
            from_date: Start date in YYYY-MM-DD format (optional)
            to_date: End date in YYYY-MM-DD format (optional)
            min_days: Minimum number of days a task was tracked (default: 0)

        Returns:
            JSON string containing finished tasks in the date range
        """
        try:
            tasks = analyzer.get_finished_tasks(from_date, to_date, min_days)
            return json.dumps(tasks, indent=2, default=str)
        except TodoAnalyzerError as e:
            return json.dumps({"error": str(e)})

    mcp.run(transport="stdio")


def main():
    init_logger()

    parser = argparse.ArgumentParser(
        description="MCP server for todo analysis"
    )
    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to the git repository containing todo history"
    )

    args = parser.parse_args()
    repo_path = Path(args.repo_path)

    if not repo_path.exists():
        logging.critical(f"repository path does not exist: {repo_path}")
        return 1

    init_mcp(repo_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
