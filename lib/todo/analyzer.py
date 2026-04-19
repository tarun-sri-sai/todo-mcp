import git
import logging
from datetime import datetime
from sortedcontainers import SortedDict
from .parser import parse_todo
from .exceptions import TodoAnalyzerError, TodoParserError

logging.getLogger()


class TodoAnalyzer:
    def __init__(self, repo_path):
        self._DATE_FMT = "%Y-%m-%d"
        self._TODO_FILE = "to-do.txt"

        self._todo_repo = git.Repo(repo_path)
        self._history = SortedDict()

        self._cache_history()

    def _try_parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, format=self._DATE_FMT)
        except ValueError:
            raise TodoAnalyzerError(
                f"invalid date format: {date_str}, expected {self._DATE_FMT}"
            )

    def _cache_history(self):
        for commit in self._todo_repo.iter_commits():
            sha = commit.hexsha
            message = commit.message.strip()

            try:
                self._history[self._try_parse_date(message)] = commit.hexsha
            except TodoAnalyzerError:
                logging.warning(
                    f"commit {sha} - invalid date format: {message}"
                )

    def _get_commit_range(self, from_date_str=None, to_date_str=None):
        if from_date_str is None:
            from_date = self._history.peekitem(0)[0]

        if to_date_str is None:
            from_date = self._history.peekitem(-1)[0]

        from_date = from_date or self._try_parse_date(from_date_str)
        to_date = to_date or self._try_parse_date(to_date_str)

        if from_date > to_date:
            raise TodoAnalyzerError(
                "'start date' must be less than or equal to 'end date'"
            )

        ceiling = self._history.bisect_left(from_date)
        if ceiling == len(self._history):
            raise TodoAnalyzerError(
                f"no todos found for 'start date' {from_date_str}"
            )
        history_start_commit = self._history.items()[ceiling][1]

        floor = self._history.bisect_right(to_date) - 1
        if floor == -1:
            raise TodoAnalyzerError(
                f"no todos found for 'end date' {to_date_str}"
            )
        history_end_commit = self._history.items()[floor][1]

        return history_start_commit, history_end_commit

    def get_tasks(self, from_date_str=None, to_date_str=None):
        history_start_commit, history_end_commit = self._get_commit_range(
            from_date_str,
            to_date_str
        )
        commits = self._history.irange(
            history_start_commit,
            history_end_commit
        )

        tasks = {}
        for commit in commits:
            commit_obj = self._todo_repo.commit(commit)
            try:
                todo_file = commit_obj.tree / self._TODO_FILE
                todo_contents = todo_file.data_stream.read().decode("utf-8")
                task_map = parse_todo(todo_contents)

                curr_tasks = set(task_map.keys())

                for task_id, task in task_map.items():
                    if task_id not in tasks:
                        tasks[task_id] = {
                            **task, 
                            "start_date": commit_obj.message.strip()
                        }
                        continue

                    tasks[task_id]["updates"] = task["updates"]

                    if task["finished"] and not tasks[task_id]["finished"]:
                        tasks[task_id]["finished"] = True
                        tasks[task_id]["end_date"] = commit_obj.message.strip()

                for task_id, task in tasks.items():
                    if task_id not in curr_tasks:
                        task["abandoned"] = True
                        task["end_date"] = commit_obj.message.strip()
            except TodoParserError:
                logging.warning(
                    f"commit {commit} - failed to parse {self._TODO_FILE}"
                )
            except Exception as e:
                logging.warning(
                    f"commit {commit} - error parsing {self._TODO_FILE}: {e}"
                )

        return tasks
