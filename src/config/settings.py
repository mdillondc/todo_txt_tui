"""
Settings and configuration for todo_txt_tui application.
"""

# Color palette for urwid UI
PALETTE = [
    ("bold", "bold", ""),
    ("text", "", ""),  # Default to terminal
    ("priority_a", "light red", ""),
    ("priority_b", "brown", ""),
    ("priority_c", "light green", ""),
    ("priority_d", "light blue", ""),
    ("priority_e", "dark magenta", ""),
    ("context", "light magenta", ""),
    ("project", "yellow", ""),
    ("is_complete", "dark gray", ""),
    ("is_danger", "light red", ""),
    ("is_success", "light green", ""),
    ("is_link", "light blue", ""),
    ("heading_overdue", "light red,italics,bold", ""),
    ("heading_today", "light green,italics,bold", ""),
    ("heading_future", "default,italics,bold", ""),
]

# Color mappings for task elements
COLORS = {
    "(A)": "priority_a",
    "(B)": "priority_b",
    "(C)": "priority_c",
    "(D)": "priority_d",
    "(E)": "priority_e",
    "(F)": "priority_f",
    "due:": "is_complete",
    "end:": "is_complete",
    "rec:": "is_complete",
    "@": "context",
    "+": "project",
    "http": "is_link",
    "is_danger": "is_danger",
    "is_success": "is_success",
    "is_complete": "is_complete",
}

# Default settings
SETTINGS = [
    ("enableCompletionAndCreationDates", "true"),
    ("hideCompletionAndCreationDates", "true"),
    ("placeCursorBeforeMetadataWhenEditingTasks", "false"),
    ("displayHiddenTasksByDefault", "false"),
    ("hideTasksWithThresholdDates", "true"),
]


def setting_enabled(setting):
    """Check if a setting is enabled (value is 'true')."""
    return any(
        item for item in SETTINGS if item[0] == setting and item[1].lower() == "true"
    )
