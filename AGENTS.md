# Agent Guide (todo_txt_tui)

This repository is a Python terminal UI (urwid) app for managing a `todo.txt` file.

Facts verified in-repo (2026-01-31):
- Entry point: `src/main.py` (run with `python src/main.py /path/to/todo.txt`).
- Dependencies: `requirements.txt` (currently: `urwid`, `python-dateutil`, `aiohttp`).
- No lint/format/test tooling or test suite is present in this repo.
- No Cursor rules found (`.cursor/rules/` or `.cursorrules`).
- No Copilot instructions found (`.github/copilot-instructions.md`).

Repository layout (high level):
- `src/main.py`: CLI arg parsing, urwid loop wiring, global UI state.
- `src/config/`: constants and UI palette/settings.
- `src/services/`: file/task manipulation (`Tasks`), autosuggestions.
- `src/ui/`: urwid widgets and keybindings.
- `src/models/`: task parsing/formatting model (`Task`).
- `src/utils/`: small helpers.

Architecture patterns (copy these when adding features):
- UI keybindings and navigation live in `src/ui/components.py:Body.keypress()`.
- Task persistence and normalization live in `src/services/task_service.py:Tasks`.
- Rendering tasks for display lives in `src/ui/widgets.py:TaskUI`.
- Autosuggestions are derived from parsing the current `todo.txt` content
  (`src/services/auto_suggestions.py`).
- A small amount of shared UI state is stored as module globals in `src/main.py` and
  accessed via local imports (ex: `import src.main as main_module`) to avoid circular imports.

Local dev setup
- Recommended (per `README.md`): conda env with Python 3.12.
  - `conda create -n todo python=3.12 -y`
  - `conda activate todo`
  - `pip install -r requirements.txt`

Commands

Run
- Run app:
  - `python src/main.py /absolute/path/to/todo.txt`
- Version/help:
  - `python src/main.py --version`
  - `python src/main.py --help`

Build
- There is no build step (no packaging config like `pyproject.toml`).
- If you need a quick syntax/type sanity check without extra deps:
  - `python -m compileall src`

Lint / format
- No linter/formatter is configured in this repo.
- If you add one, document it here and prefer a single-command workflow (ex: `ruff check`, `ruff format`).

Dependency management
- Python dependencies are declared in `requirements.txt`.
- If you add/remove a dependency, update `requirements.txt` and keep imports consistent.

Tests
- There is no test suite or test runner configured in this repo.
- If/when `pytest` is added:
  - Run all tests: `pytest`
  - Run one file: `pytest tests/test_something.py`
  - Run one test: `pytest tests/test_something.py::test_case_name`
  - Run by substring: `pytest -k name_substring`
  - Stop on first failure: `pytest -x`

Single-test guidance (important)
- Don’t claim a test command “works” unless you can see a `tests/` tree and a test dependency.
- Prefer the narrowest invocation (single test node id) when iterating.

Workspace hygiene
- This repo currently contains a `venv/` directory. Treat it as local/ephemeral:
  - Do not edit files under `venv/`.
  - Do not rely on repo-embedded `venv/` for reproducibility; prefer conda (per README).
- `src/utils/helpers.py:debug()` appends to `debug.txt` in CWD; avoid adding new always-on debug writes.

Code style (follow existing patterns unless you have a strong reason)

Imports
- Group imports in this order, separated by blank lines:
  - stdlib
  - third-party
  - local (`from src...`)
- Avoid adding new `sys.path` manipulation. `src/main.py` currently adjusts `sys.path` to make
  `python src/main.py ...` work; keep new code importable via `from src...`.
- Prefer explicit imports over `import *`.

Formatting
- Use 4-space indents.
- Keep module-level docstrings at the top of non-trivial modules (many files already do this).
- Keep lines readable; wrap long expressions and long argument lists.
- Prefer f-strings for interpolation.

Types
- Add type hints for new/modified public functions and non-trivial helpers.
- Prefer modern annotations in new code:
  - `list[str]`, `dict[str, str]`, `tuple[int, str]`, and `X | None`.
- Be consistent within a file (don’t mix `Optional[X]` and `X | None` in the same module).

Naming
- Modules: `snake_case.py`.
- Functions/variables: `snake_case`.
- Classes: `PascalCase`.
- Constants:
  - In `src/config/constants.py`, existing constants use `__double_underscore__` names.
    Keep that convention when adding new constants there (don’t rename existing exports).
  - Elsewhere, prefer `UPPER_SNAKE_CASE` for true constants.

Data model and todo.txt semantics
- The app treats the on-disk `todo.txt` as the source of truth.
- Preserve the existing task normalization rules:
  - `Tasks.restructure_task_components()` controls ordering of task parts.
  - `Tasks.normalize_task()` and `Tasks.normalize_file()` enforce spacing and ordering.
- Prefer reusing `src/models/task.py:Task` parsing/formatting when adding new features that need
  structured access to a task’s components.

Error handling
- CLI/user-facing failures: print a clear message and return/exit (see `src/main.py`).
- File I/O:
  - Handle `FileNotFoundError` when reading metadata like mtime/size.
  - Keep exception scopes narrow; don’t blanket-catch `Exception` unless you re-raise or add
    a user-actionable message.
- UI loop:
  - Use `raise urwid.ExitMainLoop()` only for the intentional quit path.

Circular imports
- Local imports inside functions are used in a few places to avoid cycles (ex: `Task.from_string`).
- Prefer fixing cycles via better module boundaries, but if you must use a local import, keep it
  narrowly scoped and comment the reason.

Side effects and safety
- This app edits user files (`todo.txt`, and `done.txt` when archiving). Be conservative:
  - Avoid surprising writes (no background writes beyond the established ones).
  - When changing write behavior, consider atomic write patterns (temp file + replace) and
    document the rationale and risks.

Cross-platform considerations
- URL opening uses OS-specific commands (`xdg-open`, `open`, `start`) in `src/ui/components.py`.
- Avoid assumptions about terminal capabilities; colors are handled via urwid palette.

When changing behavior
- Keep changes small and reversible.
- Update `README.md` only if user-facing usage/setup changes.
- If you introduce lint/test tooling, add:
  - dependencies (and where they are declared)
  - one-command “run all”
  - “run one test” examples
  - expected Python version
