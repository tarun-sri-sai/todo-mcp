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
            return datetime.strptime(date_str, self._DATE_FMT)
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

    def _get_date_range(self, from_date_str=None, to_date_str=None):
        from_date = (
            self._history.peekitem(0)[0]
            if from_date_str is None
            else self._try_parse_date(from_date_str)
        )
        to_date = (
            self._history.peekitem(-1)[0]
            if to_date_str is None
            else self._try_parse_date(to_date_str)
        )

        if from_date > to_date:
            raise TodoAnalyzerError(
                "'start date' must be less than or equal to 'end date'"
            )

        ceiling = self._history.bisect_left(from_date)
        if ceiling == len(self._history):
            raise TodoAnalyzerError(
                f"no todos found for 'start date' {from_date_str}"
            )
        history_start_date = self._history.items()[ceiling][0]

        floor = self._history.bisect_right(to_date) - 1
        if floor == -1:
            raise TodoAnalyzerError(
                f"no todos found for 'end date' {to_date_str}"
            )
        history_end_date = self._history.items()[floor][0]

        return history_start_date, history_end_date

    def get_tasks(self, from_date_str=None, to_date_str=None):
        history_start_date, history_end_date = self._get_date_range(
            from_date_str,
            to_date_str
        )
        history_dates = self._history.irange(
            history_start_date,
            history_end_date
        )

        tasks = {}
        for commit in (self._history[date] for date in history_dates):
            commit_obj = self._todo_repo.commit(commit)
            try:
                todo_file = commit_obj.tree / self._TODO_FILE
                todo_contents = todo_file.data_stream.read().decode("utf-8")
                task_map = parse_todo(todo_contents)

                curr_tasks = set(task_map.keys())

                for task_id, task in task_map.items():
                    if task_id not in tasks and not task["finished"]:
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
                    if task_id not in curr_tasks and not task["finished"]:
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

    def _get_tasks_by_min_days(self, tasks, min_days=0):
        return {
            task_id: task
            for task_id, task in tasks.items()
            if (
                self._try_parse_date(task["end_date"])
                - self._try_parse_date(task["start_date"])
            ).days >= min_days
        }

    def get_abandoned_tasks(self, from_date_str=None, to_date_str=None, min_days=0):
        tasks = self.get_tasks(from_date_str, to_date_str)
        abandoned_tasks = {
            task_id: task
            for task_id, task in tasks.items()
            if task.get("abandoned", False)
        }
        return self._get_tasks_by_min_days(abandoned_tasks, min_days)

    def get_finished_tasks(self, from_date_str=None, to_date_str=None, min_days=0):
        tasks = self.get_tasks(from_date_str, to_date_str)
        finished_tasks = {
            task_id: task
            for task_id, task in tasks.items()
            if task.get("finished", False)
        }
        return self._get_tasks_by_min_days(finished_tasks, min_days)
