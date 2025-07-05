"""
Task data model and parsing logic.
"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from src.utils.helpers import is_valid_date


@dataclass
class Task:
    """
    Represents a single todo.txt task with all its components.
    """
    text: str
    priority: Optional[str] = None
    due_date: Optional[str] = None
    completed: bool = False
    recurrence: Optional[str] = None
    threshold_date: Optional[str] = None
    contexts: List[str] = None
    projects: List[str] = None
    creation_date: Optional[str] = None
    completion_date: Optional[str] = None
    hidden: bool = False
    raw_text: str = ""

    def __post_init__(self):
        if self.contexts is None:
            self.contexts = []
        if self.projects is None:
            self.projects = []

    @classmethod
    def from_string(cls, task_string: str) -> 'Task':
        """
        Parse a task string into a Task object.

        Args:
            task_string: Raw task string from todo.txt file

        Returns:
            Task object with parsed components
        """
        # Import here to avoid circular imports
        from src.config.constants import PRIORITY_REGEX, DUE_DATE_REGEX, RECURRENCE_REGEX

        task_string = task_string.strip()

        # Initialize task components
        task_text_parts = []
        task_dates = []
        projects = []
        contexts = []
        priority = None
        due_date = None
        recurrence = None
        threshold_date = None
        completed = False
        hidden = False

        # Check if task is completed
        if task_string.startswith('x '):
            completed = True
            task_string = task_string[2:]  # Remove 'x ' prefix

        words = task_string.split()

        for index, word in enumerate(words):
            if word.startswith('+'):
                projects.append(word)
            elif word.startswith('@'):
                contexts.append(word)
            elif word.startswith('due:'):
                due_date = word[4:]  # Remove 'due:' prefix
            elif word.startswith('rec:'):
                recurrence = word[4:]  # Remove 'rec:' prefix
            elif word.startswith('t:'):
                threshold_date = word[2:]  # Remove 't:' prefix
            elif word == 'h:1':
                hidden = True
            elif re.match(PRIORITY_REGEX, word):
                priority = word[1:-1]  # Remove parentheses
            elif is_valid_date(word):
                task_dates.append(word)
            else:
                task_text_parts.append(word)

        # Determine creation and completion dates
        creation_date = None
        completion_date = None

        if completed and len(task_dates) >= 1:
            if len(task_dates) == 1:
                creation_date = task_dates[0]
            elif len(task_dates) == 2:
                completion_date = task_dates[0]
                creation_date = task_dates[1]
        elif not completed and len(task_dates) >= 1:
            creation_date = task_dates[0]

        # Join remaining words as task text
        text = ' '.join(task_text_parts)

        return cls(
            text=text,
            priority=priority,
            due_date=due_date,
            completed=completed,
            recurrence=recurrence,
            threshold_date=threshold_date,
            contexts=sorted(contexts, key=str.casefold),
            projects=sorted(projects, key=str.casefold),
            creation_date=creation_date,
            completion_date=completion_date,
            hidden=hidden,
            raw_text=task_string
        )

    def to_string(self) -> str:
        """
        Format the Task object back into a todo.txt string.

        Returns:
            Formatted task string
        """
        parts = []

        # Add completion marker
        if self.completed:
            parts.append('x')

        # Add priority
        if self.priority:
            parts.append(f'({self.priority})')

        # Add dates (completion date first if completed, then creation date)
        if self.completed and self.completion_date:
            parts.append(self.completion_date)
        if self.creation_date:
            parts.append(self.creation_date)

        # Add main task text
        if self.text:
            parts.append(self.text)

        # Add projects and contexts (sorted)
        parts.extend(sorted(self.projects, key=str.casefold))
        parts.extend(sorted(self.contexts, key=str.casefold))

        # Add metadata
        if self.due_date:
            parts.append(f'due:{self.due_date}')
        if self.recurrence:
            parts.append(f'rec:{self.recurrence}')
        if self.threshold_date:
            parts.append(f't:{self.threshold_date}')
        if self.hidden:
            parts.append('h:1')

        return ' '.join(parts)

    def get_sort_key(self) -> tuple:
        """
        Generate a sort key for this task based on due date and text.

        Returns:
            Tuple suitable for sorting tasks
        """
        # Convert due_date to a date object for proper sorting
        due_date_key = datetime.strptime(self.due_date, '%Y-%m-%d').date() if self.due_date else datetime(9999, 12, 31).date()

        # Create sort text without dates and completion markers
        sort_text = self.text.lower().strip() if self.text else ''

        return (due_date_key, sort_text)

    def is_overdue(self) -> bool:
        """Check if the task is overdue."""
        if not self.due_date:
            return False

        try:
            due_date = datetime.strptime(self.due_date, '%Y-%m-%d').date()
            return due_date < datetime.now().date()
        except ValueError:
            return False

    def is_due_today(self) -> bool:
        """Check if the task is due today."""
        if not self.due_date:
            return False

        try:
            due_date = datetime.strptime(self.due_date, '%Y-%m-%d').date()
            return due_date == datetime.now().date()
        except ValueError:
            return False

    def matches_search(self, query: str) -> bool:
        """
        Check if the task matches a search query.

        Args:
            query: Search query string

        Returns:
            True if task matches the query
        """
        if not query:
            return True

        # Search in the full task string representation
        full_text = self.to_string().lower()
        return query.lower() in full_text

    def clone(self) -> 'Task':
        """Create a copy of this task."""
        return Task(
            text=self.text,
            priority=self.priority,
            due_date=self.due_date,
            completed=self.completed,
            recurrence=self.recurrence,
            threshold_date=self.threshold_date,
            contexts=self.contexts.copy(),
            projects=self.projects.copy(),
            creation_date=self.creation_date,
            completion_date=self.completion_date,
            hidden=self.hidden,
            raw_text=self.raw_text
        )


def parse_task_string(task_string: str) -> Task:
    """
    Convenience function to parse a task string into a Task object.

    Args:
        task_string: Raw task string from todo.txt file

    Returns:
        Task object with parsed components
    """
    return Task.from_string(task_string)


def parse_task_list(task_strings: List[str]) -> List[Task]:
    """
    Parse a list of task strings into Task objects.

    Args:
        task_strings: List of raw task strings

    Returns:
        List of Task objects
    """
    return [Task.from_string(task_string) for task_string in task_strings if task_string.strip()]


def sort_tasks(tasks: List[Task]) -> List[Task]:
    """
    Sort a list of tasks based on due date and text.

    Args:
        tasks: List of Task objects to sort

    Returns:
        Sorted list of Task objects
    """
    return sorted(tasks, key=lambda task: task.get_sort_key())