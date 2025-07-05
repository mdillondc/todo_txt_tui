import urwid
import sys
import os
from typing import Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.config.constants import (
    __version__, __sync_refresh_rate__, __track_focused_task_interval__
)
from src.config.settings import PALETTE
from src.services.task_service import Tasks
from src.ui.components import Body, Search


# Global state variables
__current_search_query__ = ''
__focused_task_index__ = ''
__focused_task_text__ = ''

def handle_command_line_args() -> Optional[str]:
    """
    Handle command line arguments and return the todo file path.

    Returns:
        The path to the todo.txt file, or None if application should exit.
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == '--version':
            print(f"Version: {__version__}")
            return None
        elif sys.argv[1] == '--help':
            print("Help (keybindings, features, etc): https://github.com/mdillondc/todo_txt_tui")
            return None

    if len(sys.argv) < 2:
        print("Please provide the path to the todo.txt file.")
        return None

    return sys.argv[1]

def validate_file_path(txt_file: str) -> bool:
    """
    Validate that the todo.txt file exists.

    Args:
        txt_file: Path to the todo.txt file

    Returns:
        True if file exists, False otherwise
    """
    if not os.path.exists(txt_file):
        print(f"The file '{txt_file}' does not exist. Are you sure you specified the correct path?")
        return False
    return True

def setup_ui_components(txt_file: str) -> tuple[Body, urwid.Frame]:
    """
    Set up the UI components for the application.

    Args:
        txt_file: Path to the todo.txt file

    Returns:
        Tuple of (tasklist, main_frame)
    """
    # Initialize Body as ListBox to serve as layout for tasks and handle tasks related keybindings
    tasklist = Body(txt_file)
    tasklist_decorations = urwid.LineBox(tasklist, title="Tasks")
    tasklist.tasklist_decorations = tasklist_decorations  # type: ignore

    # Use Search instead of urwid.Edit for search field
    search = Search(tasklist_instance=tasklist, caption="Search: ")
    search_decorations = urwid.LineBox(search)

    # Connect search functionality
    urwid.connect_signal(
        search,
        'change',
        lambda edit_widget, search_query: Tasks.search(
            edit_widget, search_query, txt_file, tasklist.tasklist_instance
        )
    )

    # Create a Frame to contain the search field and the tasklist
    main_frame = urwid.Frame(tasklist_decorations, header=search_decorations)
    tasklist.main_frame = main_frame  # type: ignore

    return tasklist, main_frame

def initialize_application(txt_file: str, tasklist: Body, main_frame: urwid.Frame) -> tuple[Tasks, urwid.MainLoop, list[Optional[float]]]:
    """
    Initialize the application components.

    Args:
        txt_file: Path to the todo.txt file
        tasklist: The main tasklist Body widget
        main_frame: The main UI frame

    Returns:
        Tuple of (tasks, loop, last_mod_time)
    """
    # Initialize Tasks to handle task manipulation
    tasks = Tasks(txt_file)
    tasks.normalize_file(tasklist)

    # Initialize the MainLoop
    loop = urwid.MainLoop(main_frame, palette=PALETTE, handle_mouse=False)
    tasklist.loop = loop  # type: ignore

    # Prepare to update the tasklist if the todo.txt file has changed outside the application
    try:
        last_mod_time = [os.path.getmtime(txt_file)]
    except FileNotFoundError:
        last_mod_time = [None]

    return tasks, loop, last_mod_time

def run_application(tasks: Tasks, loop: urwid.MainLoop, txt_file: str, tasklist: Body, last_mod_time: list[Optional[float]]) -> None:
    """
    Run the main application loop with periodic updates.

    Args:
        tasks: Tasks instance for file operations
        loop: Urwid main loop
        txt_file: Path to the todo.txt file
        tasklist: The main tasklist Body widget
        last_mod_time: List containing last modification time of the file
    """
    # Set an alarm to check for file changes every 5 seconds
    loop.set_alarm_in(__sync_refresh_rate__, tasks.sync, (txt_file, tasklist, last_mod_time))

    # Set an alarm to update focused task index every 1 second
    loop.set_alarm_in(__track_focused_task_interval__, tasklist.track_focused_task)

    # Start the MainLoop to display the application
    loop.run()

def main() -> None:
    """
    Initialize and run the todo.txt TUI application.
    """
    # Handle command line arguments
    txt_file = handle_command_line_args()
    if txt_file is None:
        return

    # Validate file path
    if not validate_file_path(txt_file):
        return

    # Set up UI components
    tasklist, main_frame = setup_ui_components(txt_file)

    # Initialize application
    tasks, loop, last_mod_time = initialize_application(txt_file, tasklist, main_frame)

    # Run the application
    run_application(tasks, loop, txt_file, tasklist, last_mod_time)

if __name__ == '__main__':
    main()



