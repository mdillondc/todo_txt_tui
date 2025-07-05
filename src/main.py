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
from src.services.auto_suggestions import AutoSuggestions
from src.ui.components import Body, Search





# Global state variables
__current_search_query__ = ''
__focused_task_index__ = ''
__focused_task_text__ = ''











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
