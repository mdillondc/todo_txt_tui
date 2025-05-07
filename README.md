# TodoTxtTUI

A powerful, keyboard-driven terminal user interface (TUI) for managing your tasks in the todo.txt format. This application helps you organize and track your tasks with a simple, efficient interface.

![Screenshot](img/screenshot.png)

Supports Linux and macOS. In theory, it should work on Windows, but this is untested.

## Installation

### Prerequisites

- Git
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download)

### Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/mdillondc/todo_txt_tui.git
   cd todo_txt_tui
   ```

2. Create and activate a conda environment:
   ```
   conda create -n todo python=3.12 -y
   conda activate todo
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application directly by specifying the path to your todo.txt file:

```
python core.py /path/to/todo.txt
```

### Command Line Arguments

The following command line arguments are supported:

```
python todo_txt_tui/core.py --version  # Display version information
python todo_txt_tui/core.py --help     # Display help information
```

### Quick Access

Create an alias for quick access. Add this to your `.bashrc` or `.zshrc`, e.g.:
```
alias todo="~/miniconda3/envs/todo/bin/python ~/path/to/core.py ~/path/to/todo.txt"
```

The application requires an existing todo.txt file. If the specified file doesn't exist, the application will display an error message and exit.

## Features

- **Priorities**: Tasks can have priorities and are color-coded accordingly.
- **Sorting**: Tasks sorted by due date, priority and alphabetical (in that order).
- **Due Dates**: Tasks can have due dates and are grouped by them.
    - **Natural Language Processing (NLP)**: For example, `due:tom` or `due:tomorrow`.
- **Threshold Dates**: Also known as deferred tasks. See [details](details.md#threshold-dates).
- **Recurring tasks**: Tasks can have a recurrence pattern, automatically creating new tasks upon completion. For example `rec:1d` or `rec:+1y`.
- **Projects/Contexts**: With autosuggestions and autocompletion.
- **Search**: Quickly find the tasks you're looking for.
- **Archiving**: Completed tasks are moved to `done.txt`.
- **Completion/Creation dates**: Can be enabled or disabled in settings
- **Markdown links**: Yes.
- **Sync**: Changes made in todo.txt outside the application will be reflected in the app.
- **Keyboard driven**: Navigate and manipulate everything from your keyboard with vim-inspired keys.
- **Hidden tasks**: Default visibility can be set in settings and toggled with `t`

## Keybindings

- `j`/`down`: Move cursor down
- `k`/`up`: Move cursor up
- `gg`: Go top of list
- `G`: Go to bottom of list
- `n`: Add new task (`enter` to save, `esc` to dismiss)
- `e`: Edit existing task (`enter` to save, `esc` to dismiss)
  - `tab`: Autocomplete suggested projects and contexts
- `E`: Edit existing task, but place cursor at the end of the task text component 
- `x`: Toggle task complete/incomplete
- `X`: Complete and archive task immediately
- `A`: Archive completed tasks to done.txt
- `D`: Delete task
- `P`: Postpone task (set due date tomorrow if task has existing due date)
- `f`: Focus search field (`enter` to focus task list)
- `r`: Reset search/Refresh task list
- `u`: Open URL in focused task
    - If task has multiple URLs, press `u` followed by a number to open the specific URL
    - `U` Open all URLs in task
- `SHIFT + [1-9]`: Display only tasks with priority A, B, C, D, E, F, G, H or I
- `t`: Toggle visibility of tasks with threshold in future
- `h`: Toggle visibility of hidden tasks
- `q`: Quit application

The application uses the [urwid](http://urwid.org/) library for the terminal interface and supports powerful features like natural language date parsing, task completion tracking, and auto-suggestions.

## Todo.txt Format

For detailed information about the todo.txt format and TodoTxtTUI's extended features, see [details.md](details.md).

---

**Original concept by Gina Trapani**: Read more at [todotxt.org](http://todotxt.org/).

TodoTxtTUI extends the original todo.txt concept with additional features while maintaining compatibility with the original format.