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





# Global state variables
__current_search_query__ = ''
__focused_task_index__ = ''
__focused_task_text__ = ''


class CustomCheckBox(urwid.CheckBox):
    """
    CustomCheckBox is a subclass of urwid.CheckBox that includes an additional attribute
    to store the original text of the task. This is useful for keeping track of any
    modifications made to the task text for display purposes, while still retaining
    the original text for operations like edit, complete, delete, etc.
    """

    def __init__(self, label, state=False, original_text=''):
        """
        Initialize a new CustomCheckBox instance.

        Parameters:
        - label (str): The text to display on the checkbox. This could be a modified
                       or simplified version of the original task text.
        - state (bool): The initial state of the checkbox. True for checked, False for unchecked.
        - original_text (str): The original text of the task. This is used to retain
                                the full details of the task that might not be displayed.

        """
        # Initialize the parent urwid.CheckBox class
        super().__init__(label, state=state)

        # Store the original task text
        self.original_text = original_text

    def keypress(self, size, key):
        if key in ('enter', ' '):  # Don't allow space and enter to toggle checkboxes
            return key
        return super().keypress(size, key)  # For other keys, call the superclass method




class TaskUI:
    """
    Handle UI components like displaying the actual task list and the add/edit dialog and so on
    """

    # Display the list of tasks inside the "Tasks" area
    @staticmethod
    def render_and_display_tasks(tasks, palette):
        """
        Renders and displays tasks in the terminal UI.

        Parameters:
        tasks (list)
        palette (dict): A dictionary that maps color names to terminal colors.

        Returns:
        urwid.Pile: A urwid Pile widget containing the rendered tasks.
        """

        # Initialize the list to hold UI widgets for each task
        widgets = []

        # Initialize variables to keep track of the current due date section and whether it's the first heading
        current_due_date = ''
        first_heading = True

        # Get today's date for comparison with task due dates
        today = datetime.today().date()

        # Loop through each task
        for task in tasks:

            # Skip tasks that don't match the current search query
            if __current_search_query__ and __current_search_query__.lower() not in task['text'].lower():
                continue

            # Check for hidden tasks based on the setting
            if 'h:1' in task['text'] and not setting_enabled('displayHiddenTasksByDefault'):
                continue

            # Check for hideTasksWithThresholdDates setting
            if setting_enabled('hideTasksWithThresholdDates'):
                threshold_date_match = re.search(r't:(\d{4}-\d{2}-\d{2})', task['text'])
                if threshold_date_match:
                    threshold_date_str = threshold_date_match.group(1)
                    threshold_date = datetime.strptime(threshold_date_str, '%Y-%m-%d').date()
                    # Skip task if threshold date is in the future
                    if threshold_date > today:
                        continue

            # Extract the due date from the current task
            due_date = task['due_date']

            # Check if we're entering a new due date section
            if due_date != current_due_date:
                current_due_date = due_date
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d') if due_date else None

                # Create section heading based on due date
                if due_date_obj:
                    day_name = due_date_obj.strftime("%A")
                    heading_str = f"{due_date}: {day_name}"
                else:
                    heading_str = 'No due date'

                # Color the heading based on its relation to today's date
                if due_date_obj and due_date_obj.date() < today:
                    heading_text = urwid.Text(('heading_overdue', heading_str + ' (Overdue)'))
                elif due_date_obj and due_date_obj.date() == today:
                    heading_text = urwid.Text(('heading_today', heading_str + ' (Today)'))
                else:
                    heading_text = urwid.Text(('heading_future', heading_str))

                # Add a divider between sections (skipped for the first heading)
                if not first_heading:
                    widgets.append(urwid.Divider(' '))

                # Add the heading to the list of widgets
                widgets.append(heading_text)
                first_heading = False

            # Prepare the task line for display
            task_line = task['text'].strip()
            is_task_complete = task['completed']  # Determine if the task is complete
            display_text = []

            # Handle Markdown links and replace them with placeholders
            md_links = re.findall(r'\[(.*?)\]\((https?://\S+|file://\S+)\)', task_line)
            total_md_links = len(md_links)
            for i, (text, url) in enumerate(md_links):
                placeholder = f"MDLINK{i}"
                task_line = task_line.replace(f"[{text}]({url})", placeholder)

            # Count the number of plain text links
            total_plain_links = len(re.findall(r'(https?://\S+|file://\S+)', task_line))

            # Decide if we should count links based on the total number of Markdown and plain text links
            should_count_links = (total_md_links + total_plain_links) > 1

            # Split the task text into words
            task_words = task_line.split()
            link_counter = 0  # Initialize the link counter for each task

            # Loop through each word to apply color-coding logic
            for index, word in enumerate(task_words):
                color = 'is_complete' if is_task_complete else 'text'

                if setting_enabled('hideCompletionAndCreationDates'):
                    if index == 0 and is_valid_date(word):
                        continue

                    if index == 1 and is_valid_date(word):
                        continue

                    if index == 2 and is_valid_date(word):
                        continue

                # Apply color-coding based on the word's prefix or content
                if not is_task_complete:
                    if word == 'h:1':
                        color = 'is_complete'
                    elif word.startswith('t:'):
                        color = 'is_complete'
                    elif word.startswith('@'):
                        color = 'context'
                    elif word.startswith('+'):
                        color = 'project'
                    elif word in COLORS:
                        color = COLORS[word]
                    elif re.match(r'(https?://\S+|file://\S+)', word):
                        color = 'is_link'
                        if should_count_links:
                            link_counter += 1
                            word = f"{word}({link_counter})"
                    elif any(word.startswith(keyword) for keyword in COLORS):
                        color = COLORS.get(word[:4], 'text')
                    elif is_valid_date(word):
                        color = 'is_complete'

                # Restore Markdown links and count if necessary
                if word.startswith("MDLINK"):
                    i = int(word.replace("MDLINK", ""))
                    text, url = md_links[i]
                    if not is_task_complete:
                        color = 'is_link'
                    if should_count_links:
                        link_counter += 1
                        word = f"{text}({link_counter})"
                    else:
                        word = text  # If only one link, no need for a counter

                display_text.append((color, word))
                display_text.append(('text', ' '))

            # Remove the trailing space from the colored text
            display_text = display_text[:-1]

            # Create a custom checkbox for the task and apply the color scheme
            original_text = 'x ' + task['text'].strip() if task['completed'] else task['text'].strip()
            checkbox = CustomCheckBox(display_text, state=task['completed'], original_text=original_text)

            wrapped_checkbox = urwid.AttrMap(checkbox, None, focus_map='bold')

            # Add the checkbox to the list of widgets
            widgets.append(wrapped_checkbox)

        # Return a Pile widget containing all the task widgets
        return urwid.Pile(widgets)

    def open_task_add_edit_dialog(keymap_instance, title, default_text=None, place_cursor_at_end=True):
        """
        Opens a dialog for adding or editing a task.

        Parameters:
        keymap_instance: Instance of the Keymap class, handling key mapping and UI updates.
        title: Title for the dialog.
        default_text: Text to pre-fill in the edit dialog, useful for editing tasks.
        place_cursor_at_end: Flag to determine where to place the cursor.
                             If True, place at the end of the entire task.
                             If False, place at the end of the task text component.

        Returns:
        None: This function updates the UI but does not return a value.
        """

        # Initialize Tasks instance
        tasks = Tasks(keymap_instance.txt_file)

        # Function to handle the entered text
        def on_ask(text):
            if not text.strip():  # Exit if text is empty
                return

            if default_text:  # Edit existing task
                tasks.edit(default_text, text)
                keymap_instance.refresh_displayed_tasks()
                keymap_instance.focus_on_specific_task(__focused_task_index__)
            else:  # Add a new task
                if setting_enabled('enableCompletionAndCreationDates'):
                    text = datetime.now().strftime('%Y-%m-%d') + ' ' + text

                tasks.add(keymap_instance, text)

        # Initialize urwid Edit widget
        ask = urwid.Edit()

        # Function to identify the end of the task text component
        def find_task_text_end(task_text):
            # List of possible identifiers that mark the beginning of task metadata
            identifiers = [' +', ' @', ' due:', ' rec:', ' t:', ' h:']

            # Find the first occurrence of any metadata identifier, default to the full length of the text
            first_identifier_pos = min([task_text.find(idf) for idf in identifiers if task_text.find(idf) != -1],
                                       default=len(task_text))
            return first_identifier_pos

        # If default_text is provided, pre-fill the Edit widget
        if default_text:
            if not place_cursor_at_end:
                # Find the end of the task text component
                cursor_pos = find_task_text_end(default_text)
                ask.set_edit_text(default_text)
                # Set cursor at the end of the task text component
                ask.set_edit_pos(cursor_pos)
            else:
                # For the case of 'e', simply place the cursor at the end of the entire task
                ask.set_edit_text(default_text)
                ask.set_edit_pos(len(default_text))

        # Create BoxAdapter to hold suggestions with a height of 1
        suggestions_box_adapter = urwid.BoxAdapter(keymap_instance.auto_suggestions.dialog, height=1)

        # Apply text color to suggestions_box_adapter
        colored_suggestions_box = urwid.AttrMap(suggestions_box_adapter, 'context')

        # Create Pile widget to hold the Edit and Suggestions widgets
        layout = urwid.Pile([('pack', ask), ('pack', colored_suggestions_box)])

        # Add a border and title around the layout
        bordered_layout = urwid.LineBox(layout, title="Edit Task" if default_text else "Add Task")

        # Center the bordered layout
        fill = urwid.Filler(bordered_layout, 'middle')
        overlay = urwid.Overlay(fill, keymap_instance.tasklist_decorations, 'center', 80, 'middle', 5)

        # Function to handle key presses in the dialog
        def keypress(key):
            if key == 'enter':
                on_ask(ask.get_edit_text())
                urwid.ExitMainLoop()
                tasks.normalize_file()
            elif key == 'esc':
                keymap_instance.main_frame.contents['body'] = (keymap_instance.tasklist_decorations, None)
            elif key == 'tab':  # Autocomplete logic for projects/contexts
                first_suggestion = None
                if keymap_instance.auto_suggestions.dialog.body and len(keymap_instance.auto_suggestions.dialog.body) > 0:
                    first_suggestion_widget = keymap_instance.auto_suggestions.dialog.body[0]
                    if first_suggestion_widget:
                        all_suggestions = first_suggestion_widget.get_text()[0]
                        if all_suggestions:
                            first_suggestion = all_suggestions.split(", ")[0]
                if first_suggestion:
                    cursor_position = ask.edit_pos
                    existing_text = ask.get_edit_text()
                    start_of_word = existing_text.rfind(' ', 0, cursor_position) + 1
                    end_of_word = existing_text.find(' ', cursor_position)
                    if end_of_word == -1:
                        end_of_word = len(existing_text)
                    new_text = existing_text[:start_of_word] + first_suggestion + ' ' + existing_text[end_of_word:]
                    ask.set_edit_text(new_text)
                    ask.set_edit_pos(start_of_word + len(first_suggestion) + 1)

        # Function to update suggestions as text changes
        def on_text_change(edit, new_edit_text):
            cursor_position = edit.edit_pos
            text = new_edit_text
            start_of_word = text.rfind(' ', 0, cursor_position) + 1
            end_of_word = text.find(' ', cursor_position)
            if end_of_word == -1:
                current_word = text[start_of_word:]
            else:
                current_word = text[start_of_word:end_of_word]
            keymap_instance.auto_suggestions.update_suggestions(current_word)

        # Connect the on_text_change function to the Edit widget
        urwid.connect_signal(ask, 'change', on_text_change)

        # Update the UI to show the dialog
        keymap_instance.main_frame.contents['body'] = (overlay, None)
        keymap_instance.loop.unhandled_input = keypress


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
