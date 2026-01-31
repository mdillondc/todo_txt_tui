"""
Constants for todo_txt_tui application.
"""

# Version information
__version__ = '1.0.0'

# Refresh rates and intervals
__sync_refresh_rate__ = 2
__track_focused_task_interval__ = .1

# Regular expressions for parsing todo.txt format
STRIP_X_FROM_TASK = r'^x\s'
PRIORITY_REGEX = r'\(([A-Z])\)'
DUE_DATE_REGEX = r'due:(\d{4}-\d{2}-\d{2})'
RECURRENCE_REGEX = r'rec:([+]?[0-9]+[dwmy])'
URLS_REGEX = r'(https?://[^\s\)]+|file://[^\s\)]+)'
