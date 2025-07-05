"""
Auto-suggestions service for todo.txt contexts and projects.
"""

import urwid
import re
from src.services.task_service import Tasks


class AutoSuggestions:
    """
    Handle auto suggesting projects and contexts.
    """

    def __init__(self, txt_file):
        """
        Initializes the AutoSuggestions instance.

        :param txt_file: Path to the todo.txt file.
        """
        self.txt_file = txt_file  # Set the file path
        self.contexts = self.fetch_contexts()  # Fetch and set the contexts
        self.projects = self.fetch_projects()  # Fetch and set the projects
        self.dialog = urwid.ListBox(urwid.SimpleFocusListWalker([]))  # Create an empty ListBox for suggestions

    def fetch_contexts(self):
        """
        Fetches unique context tags from the todo.txt file.

        :returns: A list of unique context tags.
        """
        contexts = set()  # Create an empty set to store unique context tags
        tasks = Tasks(self.txt_file)  # Initialize Tasks
        for task in tasks.read():  # Loop through all tasks
            # Regex to find context tags, making sure they are properly bounded
            for match in re.finditer(r'(^| )@([^ ]+)( |$)', task):
                contexts.add(match.group(2))  # Add the context to the set
        return list(contexts)  # Convert set to list and return

    def fetch_projects(self):
        """
        Fetches unique project tags from the todo.txt file.

        :returns: A list of unique project tags.
        """
        projects = set()  # Create an empty set to store unique project tags
        tasks = Tasks(self.txt_file)  # Initialize Tasks
        for task in tasks.read():  # Loop through all tasks
            # Regex to find project tags, making sure they are properly bounded
            for match in re.finditer(r'(^| )\+([^ ]+)( |$)', task):
                projects.add(match.group(2))  # Add the project to the set
        return list(projects)  # Convert set to list and return

    def update_suggestions(self, current_word):
        """
        Updates the suggestion dialog based on the current word being typed.

        :param current_word: The current word being typed by the user.
        """
        # Refresh the contexts and projects each time this method is called
        self.contexts = self.fetch_contexts()
        self.projects = self.fetch_projects()

        filtered = []  # Initialize empty list to store filtered suggestions
        color = ''  # Initialize color to empty string

        # If the current word starts with '@', suggest contexts
        if current_word.startswith("@"):
            filtered = [item for item in self.contexts if item.lower().startswith(current_word[1:].lower())]
            symbol = "@"  # Symbol to prepend to each suggestion
            color = 'context'  # Color for context suggestions

        # If the current word starts with '+', suggest projects
        elif current_word.startswith("+"):
            filtered = [item for item in self.projects if item.lower().startswith(current_word[1:].lower())]
            symbol = "+"  # Symbol to prepend to each suggestion
            color = 'project'  # Color for project suggestions

        # Sort the filtered list alphabetically (case-insensitive)
        filtered.sort(key=str.lower)

        # Create a comma-separated string of suggestions with the appropriate symbol prepended
        suggestions_str = ', '.join([symbol + item for item in filtered])

        # Create a Text widget for the suggestions and set its color
        suggestions_widget = urwid.Text((color, suggestions_str))

        # Update the dialog body with the new suggestions
        self.dialog.body = urwid.SimpleFocusListWalker([suggestions_widget])

        # Invalidate the layout so that it gets redrawn
        self.dialog._invalidate()