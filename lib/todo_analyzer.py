import git
import logging
from datetime import datetime
from sortedcontainers import SortedDict

logging.getLogger()


class TodoAnalyzerError(Exception):
    pass


class TodoAnalyzer:
    def __init__(self, repo_path):
        self._DATE_FMT = "%Y-%m-%d"

        self._todo_repo = git.Repo(repo_path)
        self._history = SortedDict()

        self._cache_history()

    def _cache_history(self):
        for commit in self._todo_repo.iter_commits():
            sha = commit.hexsha
            message = commit.message.strip()

            try:
                parsed_date = datetime.strptime(message, format=self._DATE_FMT)
                self._history[parsed_date] = commit.hexsha
            except ValueError:
                logging.warning(
                    f"commit {sha} - invalid date format: {message}"
                )
