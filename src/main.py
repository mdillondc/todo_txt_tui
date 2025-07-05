import urwid
import re
import sys
import os
import subprocess
import platform
import json
import aiohttp
import threading
import asyncio
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

# Add parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import configuration
from src.config.constants import (
    __version__, __sync_refresh_rate__, __track_focused_task_interval__,
    STRIP_X_FROM_TASK, PRIORITY_REGEX, DUE_DATE_REGEX, RECURRENCE_REGEX, URLS_REGEX
)
from src.config.settings import PALETTE, COLORS, SETTINGS, setting_enabled
from src.utils.helpers import debug, is_valid_date
from src.services.task_service import Tasks
from src.ui.widgets import CustomCheckBox, TaskUI





# Global state variables
__current_search_query__ = ''
__focused_task_index__ = ''
__focused_task_text__ = ''








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


class Body(urwid.ListBox):
    """
    The primary frame of the application
    Also responsible for most keybindings
    """

    def __init__(self, txt_file):
        # File path for the task file
        self.txt_file = txt_file
        # Initialize AutoSuggestions object
        self.auto_suggestions = AutoSuggestions(self.txt_file)
        # Will hold the main frame of the UI
        self.main_frame = None
        # Will hold any decorations around the task list
        self.tasklist_decorations = None
        # Reference to the instance itself
        self.tasklist_instance = self
        # Will hold pending URL choices if multiple URLs are present in a task
        self.pending_url_choice = None
        # Initialize Tasks object
        self.tasks = Tasks(txt_file)
        # Helpers to detect double keypresses, e.g. `gg` for go to top
        self.last_key = None
        self.last_key_time = None

        # Another Tasks object to help with initialization
        tasks = Tasks(txt_file)

        # Initialize the ListBox with sorted tasks
        rendered_tasks = TaskUI.render_and_display_tasks(tasks.sort(tasks.read()), PALETTE)
        widgets = [w for w, _ in rendered_tasks.contents]
        super(Body, self).__init__(urwid.SimpleFocusListWalker(widgets))

    def toggle_display_hidden_tasks_setting(self):
        """
        Toggles the 'displayHiddenTasksByDefault' setting.
        """
        global SETTINGS
        for i, setting in enumerate(SETTINGS):
            if setting[0] == 'displayHiddenTasksByDefault':
                current_value = setting[1].lower() == 'true'
                new_value = 'false' if current_value else 'true'
                SETTINGS[i] = ('displayHiddenTasksByDefault', new_value)
                break

    def refresh_displayed_tasks(self):
        # Refresh the displayed tasks by reading and sorting tasks again
        tasks = Tasks(self.txt_file)
        # Update the ListBox body with newly sorted tasks
        rendered_tasks = TaskUI.render_and_display_tasks(tasks.sort(tasks.read()), PALETTE)
        widgets = [w for w, _ in rendered_tasks.contents]
        self.body = urwid.SimpleFocusListWalker(widgets)
        # Update the main frame body to reflect the new task list (only if initialized)
        if self.main_frame is not None:
            self.main_frame.contents['body'] = (self.tasklist_decorations, None)

    def focus_on_specific_task(self, task=None):
        """
        Set focus on specific task either based on its index or text content
        """
        # Check if the ListBox is empty
        if len(self.body) == 0:
            return  # Do nothing if the ListBox is empty

        if task is not None:
            if isinstance(task, int):  # If task is an integer, treat it as an index
                try:
                    # Try setting focus to the task at the given index
                    self.set_focus(task)
                except IndexError:
                    # If the index is out of range, do nothing or handle it differently
                    pass
            elif isinstance(task, str):  # If task is a string, treat it as the task text
                for i, widget in enumerate(self.body):
                    if hasattr(widget, 'original_widget') and \
                            isinstance(widget.original_widget, CustomCheckBox) and \
                            widget.original_widget.original_text == task:
                        self.set_focus(i)
                        break
        else:
            # Focus on the topmost task if no task is specified
            self.set_focus(1)

    def track_focused_task(self, loop, user_data):
        """
        Constantly updates the __focused_task_index/text__ global so we know which task is
        in focus at all times for easier task interaction throughout
        """
        global __focused_task_index__  # Ensure you're updating the global variable
        global __focused_task_text__

        try:
            focused_widget = self.focus
            focused_position = self.focus_position
            __focused_task_index__ = focused_position

            # Check if the focused widget is a CustomCheckBox
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget, CustomCheckBox):
                original_text = focused_widget.original_widget.original_text
            else:
                original_text = "Not a CustomCheckBox"

            __focused_task_text__ = original_text
        except IndexError:
            # ListBox is empty (e.g., no search results), set defaults
            __focused_task_index__ = None
            __focused_task_text__ = None

        loop.set_alarm_in(__track_focused_task_interval__,
                          self.track_focused_task)  # Schedule the next update in 1 second

    def keypress(self, size, key):
        global __focused_task_index__
        global __focused_task_text__

        # Dict: Qickly filter (search) tasks by priority SHIFT + [1-9]
        key_mapping_filter_priority = {
            '!': '(A)',
            '"': '(B)',
            '#': '(C)',
            '¤': '(D)',
            '$': '(D)',  # macOS
            '%': '(E)',
            '&': '(F)',
            '/': '(G)',
            '(': '(H)',
            ')': '(I)',
        }

        # Dict: Qickly set priority on focused task
        #key_mapping_set_priority = {
        #    '!': '(A)',
        #    '"': '(B)',
        #    '#': '(C)',
        #    '¤': '(D)',
        #    '$': '(D)',  # macOS
        #    '%': '(E)',
        #    '&': '(F)',
        #    '/': '(G)',
        #    '(': '(H)',
        #    ')': '(I)',
        #    '=': None
        #}

        # Determine the OS type for URL opening
        os_type = platform.system()
        # Get the current time for detecting rapid keypresses
        current_time = datetime.now()

        # Check if a key was pressed recently
        if self.last_key is not None:
            # Calculate the time difference between the last and current keypress
            time_difference = (current_time - self.last_key_time).total_seconds()
            # If two 'g' keys are pressed quickly, go to the top
            if time_difference < .3:
                if self.last_key == 'g' and key == 'g':
                    self.tasklist_instance.set_focus(1)

        # Update state to keep track of double keypresses, e.g. `gg`
        self.last_key = key
        self.last_key_time = current_time

        # Navigate to the bottom of the list
        if key == 'G':
            self.set_focus(len(self.body) - 1)

        # Quit the application
        elif key == 'q':
            raise urwid.ExitMainLoop()

        # Move focus down
        elif key == 'j':
            super(Body, self).keypress(size, 'down')

        # Move focus up
        elif key == 'k':
            return super(Body, self).keypress(size, 'up')

        # Add task
        elif key == 'n':
            TaskUI.open_task_add_edit_dialog(self, size)

        # Edit the currently focused task
        elif key == 'e':
            # Get the currently focused widget in the body
            focused_widget = self.focus

            # Check if the focused widget is a CustomCheckBox
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget, CustomCheckBox):
                # Retrieve the original task text from the CustomCheckBox
                task_text = focused_widget.original_widget.original_text

                # Open the task edit dialog with cursor placed at the end of the entire task
                dialog = TaskUI.open_task_add_edit_dialog(self, "Edit Task", task_text, place_cursor_at_end=True)

                # After closing the dialog, update the tasks display
                if dialog is not None:
                    self.update_tasks()


        # Edit the currently focused task but place cursor after task text
        elif key == 'E':
            # This branch is similar to the above, but handles the 'E' keypress
            focused_widget = self.focus
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget, CustomCheckBox):
                task_text = focused_widget.original_widget.original_text

                # Open the task edit dialog with cursor placed at the end of the task text component
                dialog = TaskUI.open_task_add_edit_dialog(self, "Edit Task", task_text, place_cursor_at_end=False)

                if dialog is not None:
                    self.update_tasks()

        # Archive completed tasks and refresh display
        elif key == 'A':
            self.tasks.archive()
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(__focused_task_index__)

        # Delete the currently focused task
        elif key == 'D':
            self.tasks.delete(__focused_task_text__)
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(__focused_task_index__)

        # Postpone the currently focused task to tomorrow
        elif key == 'P':
            focused_widget = self.focus
            if focused_widget is not None:
                task_text = focused_widget.original_widget.original_text
                task_text = Tasks.postpone_to_tomorrow(self, task_text)
                self.refresh_displayed_tasks()
                self.focus_on_specific_task(task_text)

        # Set focus to the search bar
        elif key == 'f':
            self.main_frame.focus_position = 'header'

        # Refresh the task list and clear the search field
        elif key in ['r', '=']:
            self.refresh_displayed_tasks()
            search_widget = self.main_frame.contents['header'][0].original_widget
            search_widget.set_edit_text('')
            self.tasklist_instance.set_focus(1)

        # Toggle task completion for the currently focused task
        elif key == 'x':
            self.tasks.complete(__focused_task_text__)
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(__focused_task_index__)

        # Toggle task completion and archive all completed tasks at the same time
        elif key == 'X':
            self.tasks.complete(__focused_task_text__)
            self.tasks.archive()
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(__focused_task_index__)

        # Open the URLs of the currently focused task
        elif key == 'u':
            focused_widget = self.focus
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget,
                                                                         urwid.CheckBox):
                task_text_display = focused_widget.original_widget.get_label().strip()
                original_task_line = focused_widget.original_widget.original_text
                urls = re.findall(URLS_REGEX, original_task_line)
                if len(urls) == 1:
                    if os_type == 'Linux':
                        subprocess.run(['xdg-open', urls[0]], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                    elif os_type == 'Windows':
                        subprocess.run(['start', urls[0]], shell=True, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.STDOUT)
                    elif os_type == 'Darwin':
                        subprocess.run(['open', urls[0]], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                elif len(urls) > 1:
                    self.pending_url_choice = urls

        # Open a specific URL if a numeric key is pressed following `u` and multiple URLs are present in the task
        elif key in map(str, range(1, 10)) and self.pending_url_choice:
            index = int(key) - 1
            if index < len(self.pending_url_choice):
                if os_type == 'Linux':
                    subprocess.run(['xdg-open', self.pending_url_choice[index]], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.STDOUT)
                elif os_type == 'Windows':
                    subprocess.run(['start', self.pending_url_choice[index]], shell=True, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.STDOUT)
                elif os_type == 'Darwin':
                    subprocess.run(['open', self.pending_url_choice[index]], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.STDOUT)
            self.pending_url_choice = None

        # Open all URLs of the currently focused task
        elif key == 'U':
            focused_widget = self.focus
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget,
                                                                         urwid.CheckBox):
                task_text_display = focused_widget.original_widget.get_label().strip()
                original_task_line = focused_widget.original_widget.original_text
                urls = re.findall(URLS_REGEX, original_task_line)
                for url in urls:
                    if os_type == 'Linux':
                        subprocess.run(['xdg-open', url], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                    elif os_type == 'Windows':
                        subprocess.run(['start', url], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                    elif os_type == 'Darwin':
                        subprocess.run(['open', url], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        # Toggle 'displayHiddenTasksByDefault' setting
        elif key == 'h':
            self.toggle_display_hidden_tasks_setting()
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(__focused_task_text__)

        # Quickly sort list by priority
        if key in key_mapping_filter_priority:
            # Set focus to the search bar
            self.main_frame.focus_position = 'header'
            search_widget = self.main_frame.contents['header'][0].original_widget
            # Clear the content of the search bar and insert the mapped text
            search_widget.set_edit_text(key_mapping_filter_priority[key])
            # Switch focus back to the body
            self.main_frame.focus_position = 'body'
            # If there are tasks, focus on the first task using focus_on_specific_task
            if len(self.body) > 1:
                self.focus_on_specific_task(1)

        # Quickly set priority on focused task
        #if key in key_mapping_set_priority:
        #    focused_widget = self.focus
        #    if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget,
        #                                                                 CustomCheckBox):
        #        original_task_text = focused_widget.original_widget.original_text
        #
        #        if key_mapping_set_priority[key] is not None:
        #            # Add or modify the priority
        #            new_task_text = re.sub(PRIORITY_REGEX + r'\s*', '', original_task_text).strip() + " " + \
        #                            key_mapping_set_priority[key]
        #        else:
        #            # Remove the priority
        #            new_task_text = re.sub(PRIORITY_REGEX + r'\s*', '', original_task_text).strip()
        #
        #        # Edit the task and get the updated task text
        #        updated_task_text = self.tasks.edit(original_task_text, new_task_text)
        #
        #        # Refresh the displayed tasks
        #        self.refresh_displayed_tasks()
        #
        #        # Refocus using the updated task text
        #        for idx, widget in enumerate(self.body):
        #            if hasattr(widget, 'original_widget') and isinstance(widget.original_widget, CustomCheckBox):
        #                if widget.original_widget.original_text == updated_task_text:
        #                    self.set_focus(idx)
        #                    break

        # Toggle 'hideTasksWithThresholdDates' setting and refresh display
        elif key == 't':
            global SETTINGS
            # Find and toggle the 'hideTasksWithThresholdDates' setting
            for i, setting in enumerate(SETTINGS):
                if setting[0] == 'hideTasksWithThresholdDates':
                    current_value = setting[1].lower() == 'true'
                    new_value = 'false' if current_value else 'true'
                    SETTINGS[i] = ('hideTasksWithThresholdDates', new_value)
                    break

            # Refresh displayed tasks
            self.refresh_displayed_tasks()
            # Refocus on the current task
            self.focus_on_specific_task(__focused_task_text__)

        # Pass the keypress event to the parent class if no match is found
        else:
            return super(Body, self).keypress(size, key)


class Search(urwid.Edit):
    """
    Extension of urwid.Edit to serve as search field for filtering tasks
    """

    def __init__(self, tasklist_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasklist_instance = tasklist_instance

    def keypress(self, size, key):
        if key == 'enter':
            self.tasklist_instance.main_frame.focus_position = 'body'

            # Set focus on topmost task if search results !empty
            if len(self.tasklist_instance.body) > 0:
                self.tasklist_instance.set_focus(1)
            else:
                # Reset search if no results
                self.set_edit_text('')
                self.tasklist_instance.set_focus(1)
            return

        super().keypress(size, key)


def main():
    """
    Init. and run the actual application
    """

    # Check if there are command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--version':
            print(f"Version: {__version__}")
            return
        elif sys.argv[1] == '--help':
            print("Help (keybindings, features, etc): https://github.com/mdillondc/todo_txt_tui")
            return

    # Check if a file path for the todo.txt file is provided as a command-line argument
    if len(sys.argv) < 2:
        print("Please provide the path to the todo.txt file.")
        return

    # Store the path to the todo.txt file
    txt_file = sys.argv[1]

    # Check if the file actually exists
    if not os.path.exists(txt_file):
        print(f"The file '{txt_file}' does not exist. Are you sure you specified the correct path?")
        return

    # Initialize Body as ListBox to serve as layout for tasks and handle tasks related keybindings
    tasklist = Body(txt_file)
    tasklist_decorations = urwid.LineBox(tasklist,
                                         title="Tasks")  # Wrap the Body ListBox in a border and add a title
    tasklist.tasklist_decorations = tasklist_decorations  # Store the tasklist layout back into tasklist for future reference and state management

    # Use Search instead of urwid.Edit for search field
    # Had to use Search instead of a direct urwid.Edit to make general_input work. No idea why.
    search = Search(tasklist_instance=tasklist,
                    caption="Search: ")  # Give the search field an inline title to make its function obviou
    search_decorations = urwid.LineBox(search)  # Wrap the search field in a border (LineBox)
    urwid.connect_signal(  # Filter tasklist based on search query when the text in the search field changes
        search,
        'change',
        lambda edit_widget, search_query: Tasks.search(
            edit_widget, search_query, txt_file, tasklist.tasklist_instance
        )
    )

    # Create a Frame to contain the search field and the tasklist
    tasklist.main_frame = urwid.Frame(tasklist_decorations, header=search_decorations)

    # Initialize Tasks to handle task manipulation
    tasks = Tasks(txt_file)
    tasks.normalize_file(tasklist)

    # Initialize the MainLoop
    tasklist.loop = urwid.MainLoop(tasklist.main_frame, palette=PALETTE, handle_mouse=False)

    # Prepare to update the tasklist if the todo.txt file has changed outside the application
    try:  # Check and store the last modification time of the todo.txt file
        last_mod_time = [os.path.getmtime(txt_file)]  # Note the list
    except FileNotFoundError:
        last_mod_time = [None]  # Note the list

    # Set an alarm to check for file changes every 5 seconds
    tasklist.loop.set_alarm_in(__sync_refresh_rate__, tasks.sync, (txt_file, tasklist, last_mod_time))

    # Set an alarm to update focused task index every 1 second
    tasklist.loop.set_alarm_in(__track_focused_task_interval__, tasklist.track_focused_task)

    # Start the MainLoop to display the application
    tasklist.loop.run()


# Start the application
if __name__ == '__main__':
    main()


# Needed to build for pypi because use of for main function await
def entry_point():
    main()
