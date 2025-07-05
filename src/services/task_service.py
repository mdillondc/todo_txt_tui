"""
Task service for CRUD operations and file management.
"""

import os
import re
import urwid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from src.config.constants import (
    PRIORITY_REGEX, DUE_DATE_REGEX, RECURRENCE_REGEX,
    __sync_refresh_rate__
)
from src.config.settings import PALETTE, setting_enabled
from src.utils.helpers import is_valid_date
from src.ui.widgets import TaskUI, CustomCheckBox


class Tasks:
    """
    Task manipulation
    Add, edit, delete, etc
    """

    def __init__(self, txt_file):
        self.txt_file = txt_file

    # Reads task lines from the file and returns them as a list
    def read(self):
        with open(self.txt_file, 'r') as f:
            return [line.strip() for line in f.readlines()]

    # Sorts a list of tasks based on due date, priority, and text
    @staticmethod
    def sort(tasks):
        def parse(task_text):
            priority_match = re.search(PRIORITY_REGEX, task_text)
            due_date_match = re.search(DUE_DATE_REGEX, task_text)
            completed = task_text.startswith('x ')
            recurrence_match = re.search(RECURRENCE_REGEX, task_text)

            if completed:
                task_text = task_text[2:]

            return {
                'text': task_text,
                'priority': priority_match.group(1) if priority_match else None,
                'due_date': due_date_match.group(1) if due_date_match else None,
                'completed': completed,
                'recurrence': recurrence_match.group(1) if recurrence_match else None,
            }

        def get_sort_key(task):
            # Convert due_date to a date object for proper sorting, default to a date far in the future if None
            due_date_key = datetime.strptime(task['due_date'], '%Y-%m-%d').date() if task['due_date'] else datetime(
                9999, 12, 31).date()

            sort_text = ''
            words = task['text'].split()

            for index, word in enumerate(words):
                if index == 0 and word == 'x':
                    continue
                elif is_valid_date(word.strip()):
                    continue
                else:
                    sort_text += word + ' '

            # Remove trailing whitespace and convert to lowercase for case-insensitive sorting
            sort_text = sort_text.strip().lower()

            return (due_date_key, sort_text)

        # Parse each task line into a dictionary of its components
        parsed_tasks = [parse(task) for task in tasks]

        # Sort tasks by due date, then by text
        parsed_tasks.sort(key=get_sort_key)

        return parsed_tasks

    # Do not allow adding duplicate tasks
    def task_already_exists(self, task_text):
        existing_tasks = self.read()
        return task_text in existing_tasks

    # Adds a new task to the task file
    def add(self, keymap_instance, new_task):
        # Normalize the new task to remove extra spaces
        normalized_task = self.normalize_task(new_task)

        # Convert NLP dates to actual dates
        normalized_task = self.convert_nlp_to_dates(normalized_task)

        # Check if the file is empty
        file_is_empty = False
        try:
            file_is_empty = os.path.getsize(self.txt_file) == 0
        except FileNotFoundError:
            file_is_empty = True  # File doesn't exist, so consider it as empty

        # Append the new task to the file
        if not self.task_already_exists(normalized_task):
            with open(self.txt_file, 'a') as f:
                if not file_is_empty:
                    f.write('\n')
                f.write(normalized_task)

        keymap_instance.refresh_displayed_tasks()
        keymap_instance.focus_on_specific_task(normalized_task.strip())

    # Edits an existing task in the task file
    def edit(self, old_task, new_task):
        """
        Edits an existing task in the task file. Returns the updated task text after restructuring.

        Parameters:
        old_task (str): The original task text.
        new_task (str): The modified task text.

        Returns:
        str: The updated task text after restructuring.
        """

        # Normalize both the old and new tasks
        normalized_old_task = self.normalize_task(old_task)
        normalized_new_task = self.normalize_task(new_task)

        # Convert NLP dates to actual dates
        normalized_new_task = self.convert_nlp_to_dates(normalized_new_task)

        # Read all tasks from the file
        with open(self.txt_file, 'r') as f:
            tasks = f.readlines()

        # Find the task to be edited and replace it with the new task
        for i, task in enumerate(tasks):
            if self.normalize_task(task.strip()) == normalized_old_task:
                tasks[i] = normalized_new_task + '\n'
                break

        # Write the updated tasks back to the file
        with open(self.txt_file, 'w') as f:
            f.writelines(tasks)

        # Restructure the updated task components
        restructured_task = self.restructure_task_components(normalized_new_task)

        # Return the restructured task text
        return restructured_task

    def delete(self, task_text):
        # Normalize the task text for consistency
        normalized_task = self.normalize_task(task_text)

        # Read all tasks from the file
        with open(self.txt_file, 'r') as f:
            tasks = f.readlines()

        # Filter out the task to be deleted
        tasks = [task for task in tasks if self.normalize_task(task.strip()) != normalized_task]

        # Write the remaining tasks back to the file
        with open(self.txt_file, 'w') as f:
            f.writelines(tasks)

    # Postpone task to tomorrow
    def postpone_to_tomorrow(self, task_text):
        # Search for the due date in task_text
        due_date_match = re.search(DUE_DATE_REGEX, task_text)
        if not due_date_match:
            return  # Return if no due date is found

        # Convert the found due date to a datetime object
        due_date_str = due_date_match.group(1)
        due_date_dt = datetime.strptime(due_date_str, '%Y-%m-%d')

        # Get today's date
        today_dt = datetime.today().date()

        # Compare today's date with due date and decide on the new due date
        if due_date_dt.date() >= today_dt:
            new_due_date_dt = due_date_dt + timedelta(days=1)
        else:
            new_due_date_dt = datetime.combine(today_dt, datetime.min.time()) + timedelta(days=1)

        # Replace the original due date with the new one
        new_due_date_str = datetime.strftime(new_due_date_dt, '%Y-%m-%d')
        updated_task = re.sub(DUE_DATE_REGEX, f'due:{new_due_date_str}', task_text)

        # Read all tasks from the file
        with open(self.txt_file, 'r') as f:
            tasks = f.readlines()

        # Find the task to be edited and replace it with the new task
        for i, task in enumerate(tasks):
            if task.strip() == task_text:
                tasks[i] = updated_task + '\n'
                break

        # Write the updated tasks back to the file
        with open(self.txt_file, 'w') as f:
            f.writelines(tasks)

        return updated_task

    # Toggle the completion status of a task (and add a new task if rec rule is present)
    def complete(self, task_text):
        # Read the current tasks from the file
        tasks = self.read()

        # Lists to store the modified tasks and recurring tasks
        modified_tasks = []
        recurring_tasks = []

        # Flag to check if a task has been toggled (completed/uncompleted)
        task_toggled = False

        # Current date of completion (today's date)
        completion_date = datetime.now().date()

        for i, task in enumerate(tasks):
            # Remove leading and trailing whitespaces
            text = task.strip()

            # Check if the task is already complete
            is_complete = text.startswith('x ')

            # Check if the modified task text matches the provided task_text
            if text == task_text and not task_toggled:
                # Set the flag to True
                task_toggled = True

                # Toggle the task's completed state
                if is_complete:
                    modified_task = text[2:]  # Slice off "x " to make the task incomplete

                    if setting_enabled('enableCompletionAndCreationDates'):
                        if len(modified_task) >= 14 and is_valid_date(
                                modified_task[4:14]):  # Task has creation date and priority
                            # Remove completion date since the task is no longer marked complete
                            modified_task = modified_task[:4] + modified_task[15:]

                        elif len(modified_task) >= 10 and is_valid_date(
                                modified_task[0:10]):  # Task has creation date but no priority
                            # Remove the completion date from the task
                            modified_task = modified_task[10:]

                else:
                    has_priority = bool(re.match(r'^\([A-Z]\)', text[0:3]))
                    priority = text[0:3]

                    if setting_enabled('enableCompletionAndCreationDates'):
                        if has_priority:
                            modified_task = 'x ' + priority + ' ' + datetime.now().strftime('%Y-%m-%d') + re.sub(
                                r'^\([A-Z]\)', '', text)
                        else:
                            modified_task = 'x ' + datetime.now().strftime('%Y-%m-%d') + ' ' + text
                    else:
                        modified_task = 'x ' + text

                # Remove any extra white spaces
                modified_tasks.append(re.sub(r'\s+', ' ', modified_task).strip())

                # Handle recurring tasks
                if "rec:" in text and not is_complete:
                    # Extract recurrence value
                    recurrence_value = re.search(RECURRENCE_REGEX, text).group(1)

                    # Check if the recurrence is strict (starts with '+')
                    is_strict = recurrence_value.startswith('+')

                    # Extract old due date and threshold date if present
                    due_date_match = re.search(DUE_DATE_REGEX, text)
                    old_due_date = datetime.strptime(due_date_match.group(1),
                                                     '%Y-%m-%d').date() if due_date_match else None

                    threshold_date_match = re.search(r't:(\d{4}-\d{2}-\d{2})', text)
                    old_threshold_date = datetime.strptime(threshold_date_match.group(1),
                                                           '%Y-%m-%d').date() if threshold_date_match else None

                    # Calculate new due date based on recurrence
                    amount_match = re.match(r"\+?(\d+)", recurrence_value)
                    if not amount_match:
                        continue
                    amount = int(amount_match.group(1))
                    unit = recurrence_value[-1]
                    unit_mapping = {'d': 'days', 'w': 'weeks', 'm': 'months', 'y': 'years'}
                    delta = relativedelta(**{unit_mapping[unit]: amount})

                    if is_strict:
                        new_due_date = old_due_date + delta if old_due_date else None
                        new_threshold_date = old_threshold_date + delta if old_threshold_date else None
                    else:
                        new_due_date = completion_date + delta
                        if old_threshold_date and old_due_date:
                            days_difference = (old_due_date - old_threshold_date).days
                            new_threshold_date = new_due_date - relativedelta(days=days_difference)
                        else:
                            new_threshold_date = None

                    # Format new due date and threshold date strings
                    new_due_date_str = f'due:{new_due_date.strftime("%Y-%m-%d")}' if new_due_date else ''
                    new_threshold_date_str = f't:{new_threshold_date.strftime("%Y-%m-%d")}' if new_threshold_date else ''

                    # Create new task with updated dates
                    new_task = text
                    if due_date_match:
                        new_task = re.sub(DUE_DATE_REGEX, new_due_date_str, new_task)
                    elif new_due_date_str:
                        new_task += f' {new_due_date_str}'

                    if threshold_date_match:
                        new_task = re.sub(r't:(\d{4}-\d{2}-\d{2})', new_threshold_date_str, new_task)
                    elif new_threshold_date_str:
                        new_task += f' {new_threshold_date_str}'

                    has_priority = False

                    # Remove old creation date if present (for tasks without priority)
                    if len(modified_task) >= 10 and is_valid_date(new_task[0:10]):
                        new_task = new_task[11:]  # strip creation date from new task text

                    # Remove old creation date if present (for tasks with priority)
                    if len(modified_task) >= 14 and is_valid_date(new_task[4:14]):
                        new_task = new_task[:3] + new_task[14:]  # strip creation date from new task text
                        has_priority = True

                    # Add new creation date if setting is enabled
                    if setting_enabled('enableCompletionAndCreationDates'):
                        if not has_priority:
                            new_task = datetime.now().strftime('%Y-%m-%d') + ' ' + new_task
                        else:
                            priority = new_task[:4]
                            text = new_task[3:]
                            new_task = priority + datetime.now().strftime('%Y-%m-%d') + text

                    # Add the new task to recurring_tasks if it doesn't already exist
                    if not self.task_already_exists(new_task):
                        recurring_tasks.append(new_task)

            else:
                modified_tasks.append(text)

        # Write the updated tasks back to the file
        with open(self.txt_file, 'w') as f:
            f.write('\n'.join(modified_tasks + recurring_tasks))

    # Archives completed tasks to a 'done.txt' file and removes them from the original file
    def archive(self):
        completed_tasks = []
        incomplete_tasks = []

        # Read all tasks from the file
        with open(self.txt_file, 'r') as f:
            tasks = f.readlines()

        # Separate tasks into completed and incomplete lists
        for task in tasks:
            if task.startswith('x '):
                completed_tasks.append(task.strip())
            else:
                incomplete_tasks.append(task.strip())

        # Append completed tasks to 'done.txt'
        done_txt_file = os.path.join(os.path.dirname(self.txt_file), 'done.txt')
        with open(done_txt_file, 'a') as f:
            f.write('\n'.join(completed_tasks) + '\n')

        # Write only incomplete tasks back to the original task file
        with open(self.txt_file, 'w') as f:
            f.write('\n'.join(incomplete_tasks))

    # Format a single task line by splitting the task into its components
    def restructure_task_components(self, task):
        """
        Before: Go +zzzProject to @aContext [YouTube](https://youtube.com) and watch rec:+1d a video. +anotherProject due:2023-01-01 @work
        After: Go to [YouTube](https://youtube.com) and watch a video. +anotherProject +zzzProject @aContext @work due:2023-01-01 rec:+1d
        """

        # Store task components
        task_text_dates = []  # completion/creation date
        task_text = []
        projects = []
        contexts = []
        priority = ""
        due_date = ""
        rec_rule = ""
        threshold_date = ""  # Variable for threshold date
        complete = False
        hidden_tag = None  # Initialize hidden tag variable

        words = task.split()

        for index, word in enumerate(words):
            if index == 0 and word == 'x':
                complete = True
                continue
            elif word.startswith('+'):
                projects.append(word)
            elif word.startswith('@'):
                contexts.append(word)
            elif word.startswith('due:'):
                due_date = word
            elif word.startswith('rec:'):
                rec_rule = word
            elif word.startswith('t:'):  # Check for threshold date
                threshold_date = word
            elif is_valid_date(word.strip()):
                task_text_dates.append(word)
            elif re.match(r'^\([A-Z]\)', word):
                priority = word
            elif word == 'h:1':
                hidden_tag = word
            else:
                task_text.append(word)

        # Sort projects and contexts
        projects.sort(key=str.casefold)
        contexts.sort(key=str.casefold)

        # Construct the task in the correct order
        restructured_task_parts = []

        # Add priority if it exists
        if priority:
            restructured_task_parts.append(priority)

        # Add dates if they exist
        if task_text_dates:
            restructured_task_parts.append(' '.join(task_text_dates))

        # Add the main task text
        restructured_task_parts.extend(task_text)

        # Add the projects, contexts if they exist
        restructured_task_parts.extend(projects)
        restructured_task_parts.extend(contexts)

        # Modify here: Add due date before recurrence rule if they exist
        if due_date:
            restructured_task_parts.append(due_date)
        if rec_rule:
            restructured_task_parts.append(rec_rule)

        # Add threshold date if it exists
        if threshold_date:
            restructured_task_parts.append(threshold_date)

        # Add the hidden tag if it was present
        if hidden_tag:
            restructured_task_parts.append(hidden_tag)

        # Join all parts with a single space
        restructured_task = ' '.join(restructured_task_parts)

        # If the task is complete, prepend 'x' to the task
        if complete:
            restructured_task = 'x ' + restructured_task

        return restructured_task.strip()

    # Normalizes a single task by removing extra spaces and restructuring it
    def normalize_task(self, task_text):
        # Remove extra spaces
        task_text = ' '.join(task_text.split())
        # Restructure the task
        return self.restructure_task_components(task_text)

    # Normalizes the entire task file
    def normalize_file(self, body=None):
        # Read all tasks from the file
        with open(self.txt_file, 'r') as f:
            tasks = f.readlines()

        # Remove extra spaces, filter out empty lines, and restructure tasks
        normalized_tasks = [self.restructure_task_components(task.strip()) for task in tasks if task.strip()]

        # Write the normalized tasks back to the file
        with open(self.txt_file, 'w') as f:
            f.write('\n'.join(normalized_tasks))

        # Refresh the task list display if a Body instance is provided
        if body is not None:
            body.refresh_displayed_tasks()

    # Performs a fuzzy search for tasks and updates the UI to display only matching tasks
    @staticmethod
    def search(edit_widget, search_query, txt_file, tasklist_instance):
        import src.main as main_module
        main_module.__current_search_query__ = search_query  # Update the current search query

        # Create a Tasks instance for the given file path
        tasks = Tasks(txt_file)

        # Read all tasks and filter those that match the search query
        filtered_tasks = [task for task in tasks.read() if search_query.lower() in task.lower()]

        # Update the UI to display only the filtered tasks
        tasklist_instance.body = urwid.SimpleFocusListWalker(
            [w for w, _ in TaskUI.render_and_display_tasks(tasks.sort(filtered_tasks), PALETTE).contents])

        # If 'Enter' was the last key pressed, refocus on the task list in the UI
        if hasattr(tasklist_instance, 'last_key') and tasklist_instance.last_key == 'enter':
            tasklist_instance.main_frame.focus_position = 'body'
            delattr(tasklist_instance, 'last_key')  # Remove the attribute once it's been used
            tasklist_instance.set_focus(0)  # Focus on the first task in the list

    # Convert natural language like due:tomorrow to actual dates
    def convert_nlp_to_dates(self, task):
        # Regular expression to find "due:" keyword and its value
        due_date_match = re.search(r'due:([a-zA-Z0-9]+)', task)

        if due_date_match:
            nlp_date = due_date_match.group(1).lower()
            today = datetime.now().date()
            weekday_to_number = {
                'mon': 0,
                'tue': 1,
                'wed': 2,
                'thu': 3,
                'fri': 4,
                'sat': 5,
                'sun': 6
            }

            # Convert natural language to standard date
            if nlp_date in ['tod', 'today']:
                new_date = today
            elif nlp_date in ['tom', 'tomorrow']:
                new_date = today + timedelta(days=1)
            elif nlp_date in weekday_to_number.keys():
                target_weekday = weekday_to_number[nlp_date]
                days_until_target = (target_weekday - today.weekday() + 7) % 7
                new_date = today + timedelta(days=days_until_target)
                if days_until_target == 0:
                    new_date += timedelta(days=7)
            elif nlp_date in ['nw', 'nextweek']:
                new_date = today + timedelta((0 - today.weekday() + 7))
            elif nlp_date in ['nm', 'nextmonth']:
                if today.month == 12:
                    new_date = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    new_date = today.replace(month=today.month + 1, day=1)
            elif re.match(r'\d{1,2}[a-zA-Z]{3}(\d{4})?$', nlp_date):
                # For patterns like 11dec, 1dec, or 11dec2027, 1dec2027
                day_match = re.search(r'\d{1,2}', nlp_date)
                month_match = re.search(r'[a-zA-Z]{3}', nlp_date)
                year_match = re.search(r'\d{4}$', nlp_date)

                if day_match and month_match:
                    day = int(day_match.group(0))
                    month_str = month_match.group(0)

                    month_to_number = {
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                    }
                    month = month_to_number.get(month_str.lower())
                    if month is None:
                        return task  # Return original if month is invalid

                    year = int(year_match.group(0)) if year_match else today.year
                    if month < today.month or (month == today.month and day < today.day):
                        year += 1  # Increment year if date has already passed
                    new_date = datetime(year, month, day).date()
            else:
                return task  # If it doesn't match any of these, return the original task

            # Replace in task
            actual_due_date = f"due:{new_date.strftime('%Y-%m-%d')}"
            task_text_with_actual_date = re.sub(r'due:[a-zA-Z0-9]+', actual_due_date, task)

            return task_text_with_actual_date

        # Return the original task if no conversion was possible
        return task

    # Checks for updates in the task file and refreshes the UI if needed
    def sync(self, loop, user_data):
        import src.main as main_module
        # Unpack user data to get file path, UI instance, and last modification time
        txt_file, tasklist_instance, last_mod_time = user_data

        # Check if a dialog is currently open in the UI; if so, skip the update
        if isinstance(tasklist_instance.main_frame.contents['body'][0], urwid.Overlay):
            # Reschedule to run this method after 5 seconds
            loop.set_alarm_in(__sync_refresh_rate__, self.sync, user_data)
            return

        # Get the current modification time of the task file
        current_mod_time = os.path.getmtime(txt_file)

        # Check if the task file has been modified since the last check
        if current_mod_time != last_mod_time[0]:
            # Save the currently focused task in the UI
            focused_widget = tasklist_instance.focus
            focused_task_text = None

            # Use the original task text if available
            if hasattr(focused_widget, 'original_widget') and isinstance(focused_widget.original_widget,
                                                                         CustomCheckBox):
                focused_task_text = focused_widget.original_widget.original_text

            # Refresh the task list UI
            tasklist_instance.refresh_displayed_tasks()

            # Refocus on the previously focused task in the UI based on its original text
            if focused_task_text:
                tasklist_instance.focus_on_specific_task(main_module.__focused_task_index__)

            # Update the last known modification time
            last_mod_time[0] = current_mod_time

        # Reschedule this method to run again after 5 seconds
        loop.set_alarm_in(__sync_refresh_rate__, self.sync, (txt_file, tasklist_instance, last_mod_time))