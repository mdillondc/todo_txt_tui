import urwid
import re
from datetime import datetime

# Import configuration and utilities
from src.config.settings import COLORS, setting_enabled
from src.utils.helpers import is_valid_date


# Global variable imports resolved - no longer using local imports


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
    def render_and_display_tasks(tasks, palette, current_search_query=''):
        """
        Renders and displays tasks in the terminal UI.

        Parameters:
        tasks (list)
        palette (dict): A dictionary that maps color names to terminal colors.
        current_search_query (str): Current search query for filtering tasks.

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
            if current_search_query and current_search_query.lower() not in task['text'].lower():
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

    @staticmethod
    def open_task_add_edit_dialog(keymap_instance, title, default_text=None, place_cursor_at_end=True, focused_task_index=None):
        """
        Opens a dialog for adding or editing a task.

        Parameters:
        keymap_instance: Instance of the Keymap class, handling key mapping and UI updates.
        title: Title for the dialog.
        default_text: Text to pre-fill in the edit dialog, useful for editing tasks.
        place_cursor_at_end: Flag to determine where to place the cursor.
                             If True, place at the end of the entire task.
                             If False, place at the end of the task text component.
        focused_task_index: Index of the currently focused task.
        """

        # Initialize Tasks instance
        from src.services.task_service import Tasks
        tasks = Tasks(keymap_instance.txt_file)

        # Function to handle the entered text
        def on_ask(text):
            if not text.strip():  # Exit if text is empty
                return

            if default_text:  # Edit existing task
                tasks.edit(default_text, text)
                keymap_instance.refresh_displayed_tasks()
                keymap_instance.focus_on_specific_task(focused_task_index)
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