"""
UI components for todo.txt TUI application.
"""

import urwid
import re
import os
import subprocess
import platform
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from src.config.constants import (
    STRIP_X_FROM_TASK, PRIORITY_REGEX, DUE_DATE_REGEX, RECURRENCE_REGEX,
    __track_focused_task_interval__
)
from src.config.settings import PALETTE, COLORS, SETTINGS, setting_enabled
from src.utils.helpers import debug, is_valid_date
from src.services.task_service import Tasks
from src.ui.widgets import CustomCheckBox, TaskUI
from src.services.auto_suggestions import AutoSuggestions


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

        # Determine the OS type for URL opening
        self.os_type = platform.system()

        # Another Tasks object to help with initialization
        tasks = Tasks(txt_file)

        # Initialize the ListBox with sorted tasks
        import src.main as main_module
        rendered_tasks = TaskUI.render_and_display_tasks(tasks.sort(tasks.read()), PALETTE, main_module.__current_search_query__)
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

    def open_url_or_terminal(self, url):
        """
        Opens a URL in browser or executes a terminal command based on prefix.
        term: prefix opens Ghostty with the command, otherwise uses xdg-open.
        """
        if url.startswith('term:'):
            command = url[5:].strip()  # Remove 'term:' prefix
            shell = os.environ.get('SHELL', 'zsh')
            if command:
                shell_cmd = f"{command}; exec {shell} -i"
            else:
                shell_cmd = f"exec {shell} -i"

            subprocess.Popen(
                ['ghostty', '-e', shell, '-ic', shell_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        else:
            if self.os_type == 'Linux':
                subprocess.Popen(
                    ['xdg-open', url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            elif self.os_type == 'Windows':
                subprocess.run(['start', url], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            elif self.os_type == 'Darwin':
                subprocess.run(['open', url], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def extract_task_links(self, task_line):
        """Extracts markdown link destinations and plain URLs from a task line."""

        if not task_line:
            return []

        # Markdown: [text](destination) - allow spaces in destination; stop at first ')'
        md_matches = list(re.finditer(r'\[([^\]]*?)\]\(([^)]*?)\)', task_line))
        links = []

        for m in md_matches:
            dest = m.group(2).strip()
            if dest:
                links.append(dest)

        # Strip markdown links before scanning for plain URLs (avoid double-counting).
        stripped_line = task_line
        for m in reversed(md_matches):
            stripped_line = stripped_line[:m.start()] + ' ' + stripped_line[m.end():]

        plain_links = re.findall(r'(https?://[^\s\)]+|file://[^\s\)]+|term:[^\s\)]+)', stripped_line)
        links.extend(plain_links)

        return links

    def refresh_displayed_tasks(self):
        # Refresh the displayed tasks by reading and sorting tasks again
        tasks = Tasks(self.txt_file)
        # Update the ListBox body with newly sorted tasks
        import src.main as main_module
        rendered_tasks = TaskUI.render_and_display_tasks(tasks.sort(tasks.read()), PALETTE, main_module.__current_search_query__)
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
        # Import global variables from main module
        import src.main as main_module

        try:
            focused_widget = self.focus
            focused_position = self.focus_position
            main_module.__focused_task_index__ = focused_position

            # Check if the focused widget is a CustomCheckBox
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget, CustomCheckBox):
                original_text = focused_widget.original_widget.original_text
            else:
                original_text = "Not a CustomCheckBox"

            main_module.__focused_task_text__ = original_text
        except IndexError:
            # ListBox is empty (e.g., no search results), set defaults
            main_module.__focused_task_index__ = None
            main_module.__focused_task_text__ = None

        loop.set_alarm_in(__track_focused_task_interval__,
                          self.track_focused_task)  # Schedule the next update in 1 second

    def keypress(self, size, key):
        # Import global variables from main module
        import src.main as main_module

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
            TaskUI.open_task_add_edit_dialog(self, size, focused_task_index=main_module.__focused_task_index__)

        # Edit the currently focused task
        elif key == 'e':
            # Get the currently focused widget in the body
            focused_widget = self.focus

            # Check if the focused widget is a CustomCheckBox
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget, CustomCheckBox):
                # Retrieve the original task text from the CustomCheckBox
                task_text = focused_widget.original_widget.original_text

                # Open the task edit dialog with cursor placed at the end of the entire task
                dialog = TaskUI.open_task_add_edit_dialog(self, "Edit Task", task_text, place_cursor_at_end=True, focused_task_index=main_module.__focused_task_index__)

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
                dialog = TaskUI.open_task_add_edit_dialog(self, "Edit Task", task_text, place_cursor_at_end=False, focused_task_index=main_module.__focused_task_index__)

                if dialog is not None:
                    self.update_tasks()

        # Archive completed tasks and refresh display
        elif key == 'A':
            self.tasks.archive()
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(main_module.__focused_task_index__)

        # Delete the currently focused task
        elif key == 'D':
            self.tasks.delete(main_module.__focused_task_text__)
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(main_module.__focused_task_index__)

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
            self.tasks.complete(main_module.__focused_task_text__)
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(main_module.__focused_task_index__)

        # Toggle task completion and archive all completed tasks at the same time
        elif key == 'X':
            self.tasks.complete(main_module.__focused_task_text__)
            self.tasks.archive()
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(main_module.__focused_task_index__)

        # Open the URLs of the currently focused task
        elif key == 'u':
            focused_widget = self.focus
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget,
                                                                         urwid.CheckBox):
                task_text_display = focused_widget.original_widget.get_label().strip()
                original_task_line = focused_widget.original_widget.original_text
                urls = self.extract_task_links(original_task_line)
                if len(urls) == 1:
                    self.open_url_or_terminal(urls[0])
                elif len(urls) > 1:
                    self.pending_url_choice = urls

        # Open a specific URL if a numeric key is pressed following `u` and multiple URLs are present in the task
        elif key in map(str, range(1, 10)) and self.pending_url_choice:
            index = int(key) - 1
            if index < len(self.pending_url_choice):
                self.open_url_or_terminal(self.pending_url_choice[index])
            self.pending_url_choice = None

        # Open all URLs of the currently focused task
        elif key == 'U':
            focused_widget = self.focus
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget,
                                                                         urwid.CheckBox):
                task_text_display = focused_widget.original_widget.get_label().strip()
                original_task_line = focused_widget.original_widget.original_text
                urls = self.extract_task_links(original_task_line)
                for url in urls:
                    self.open_url_or_terminal(url)

        # Toggle 'displayHiddenTasksByDefault' setting
        elif key == 'h':
            self.toggle_display_hidden_tasks_setting()
            self.refresh_displayed_tasks()
            self.focus_on_specific_task(main_module.__focused_task_text__)

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

        # Quickly filter by due date using ALT+[1-9]
        if isinstance(key, str) and key.startswith('meta '):
            meta_key = key.split(' ', 1)[1]
            if meta_key in [str(i) for i in range(1, 10)]:
                offset = int(meta_key) - 1
                target_date = date.today() + timedelta(days=offset)
                filter_text = f"due:{target_date.strftime('%Y-%m-%d')}"
                # Set focus to the search bar
                self.main_frame.focus_position = 'header'
                search_widget = self.main_frame.contents['header'][0].original_widget
                # Replace content of the search bar and insert the due filter
                search_widget.set_edit_text(filter_text)
                # Switch focus back to the body
                self.main_frame.focus_position = 'body'
                # If there are tasks, focus on the first task
                if len(self.body) > 1:
                    self.focus_on_specific_task(1)

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
            self.focus_on_specific_task(main_module.__focused_task_text__)

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
