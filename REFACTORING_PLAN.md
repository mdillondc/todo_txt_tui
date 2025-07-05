# TodoTxtTUI Refactoring Plan

## Current State Analysis

**Single Monolithic File**: `todo_txt_tui/core.py` (1581 lines) - to be moved to `src/main.py`
- 6 Classes: `CustomCheckBox`, `Tasks`, `TaskUI`, `AutoSuggestions`, `Body`, `Search`
- Global state: Multiple global variables, settings, and constants
- No package structure: No `__init__.py`, no proper modules
- Mixed concerns: UI, business logic, file I/O, and parsing all in one file

## Goals

- **Modernize Python structure** while maintaining 100% functionality
- **Separate concerns** for better maintainability
- **Enable testing** of individual components
- **Improve code organization** without breaking existing usage

## Core Principles & Constraints

✅ **Keep `requirements.txt`** as dependency management (no setup.py/pyproject.toml)  
✅ **Maintain ALL existing functionality** (non-negotiable)  
✅ **Test at every checkpoint** to confirm functionality intact  
✅ **Update entry point**: `python src/main.py` (moved from todo_txt_tui/core.py)
✅ **Incremental refactoring** - app works at every step  
✅ **Track temporary fixes** - Document all workarounds for later cleanup

## Progress Tracking

**Use `REFACTORING_TODO.md` to track all progress:**
- ✅ Check off completed items as you go
- ✅ Update status indicators for each phase
- ✅ Document any issues or blockers in the notes section
- ✅ **CRITICAL**: Each phase must be fully tested and verified before proceeding to next phase

**Workflow**:
1. Read the phase details in this plan
2. Execute the actions listed in `REFACTORING_TODO.md`
3. Check off each action as completed
4. Run ALL testing steps for the phase
5. Mark phase status as ✅ Complete only after ALL tests pass
6. Move to next phase

## Temporary Fixes Protocol

**MANDATORY for all phases**: When temporary workarounds are needed:

1. **Mark in Code**: Add `TODO: TEMPORARY FIX - [reason]` comments
2. **Document in TODO**: Add "⚠️ Temporary Fixes Applied" section to the phase
3. **Explain Why**: Document why the fix is temporary and when it will be resolved
4. **Track Resolution**: Note which future phase will address the workaround

**Example**:
```python
# TODO: TEMPORARY FIX - Circular import workaround
# This import will be removed in Phase 4 when UI components are extracted
from src.main import CustomCheckBox
```

**In REFACTORING_TODO.md**:
```markdown
### ⚠️ Temporary Fixes Applied (To Be Resolved in Later Phases)
- **Description**: What was done temporarily
- **Reason**: Why it was necessary
- **Resolution**: Which phase will fix it
```

## Target Structure

```
todo_txt_tui_code/
├── requirements.txt             # Keep as-is
├── src/
│   ├── __init__.py              # New - empty for now
│   ├── main.py                  # Main entry point (moved from todo_txt_tui/core.py)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Extract SETTINGS, PALETTE, COLORS
│   │   └── constants.py         # Extract regex patterns, version
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py              # Task parsing/data structures
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── components.py        # Body, Search classes
│   │   └── widgets.py           # CustomCheckBox, TaskUI
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_service.py      # Tasks class (CRUD operations)
│   │   └── auto_suggestions.py  # AutoSuggestions class
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # debug, is_valid_date, etc.
```

## Refactoring Phases

### Phase 1: Extract Constants & Settings
**Goal**: Move global constants to dedicated config module

**Actions**:
- Create `config/` module structure
- Move `PALETTE`, `COLORS`, `SETTINGS` to `config/settings.py`
- Move `__version__`, regex patterns to `config/constants.py`
- Update imports in `main.py`

**Checkpoint**: Test that `python src/main.py /path/to/todo.txt` works identically

**Temporary Fixes**: Document any workarounds needed for imports or dependencies

### Phase 2: Extract Utility Functions
**Goal**: Move standalone helper functions

**Actions**:
- Create `utils/` module
- Move `debug()`, `is_valid_date()`, `setting_enabled()` to `utils/helpers.py`
- Update imports in `main.py`

**Checkpoint**: Test all utility functions work (debug logging, date validation, settings)

**Temporary Fixes**: Document any workarounds needed for function dependencies

### Phase 3: Extract Task Model & Logic
**Goal**: Separate task data operations from UI

**Actions**:
- Create `models/` and `services/` modules
- Move `Tasks` class to `services/task_service.py`
- Create task data structures in `models/task.py`
- Update imports in `main.py`

**Checkpoint**: Test all task operations (add, edit, delete, complete, search, file sync)

**Temporary Fixes**: Document any circular imports or global variable workarounds

### Phase 4: Extract UI Components
**Goal**: Organize UI components separately

**Actions**:
- Create `ui/` module
- Move `CustomCheckBox`, `TaskUI` to `ui/widgets.py`
- Update imports in `main.py`
- **RESOLVE**: Phase 3 circular import workarounds for UI components

**Checkpoint**: Test UI rendering, task display, checkbox interactions

**Temporary Fixes**: Document any remaining UI-related workarounds

### Phase 5: Extract Remaining Classes
**Goal**: Move remaining large classes

**Actions**:
- Move `AutoSuggestions` to `services/auto_suggestions.py`
- Move `Body`, `Search` to `ui/components.py`
- Update imports in `main.py`
- **RESOLVE**: Phase 3 global variable placement issues
- **RESOLVE**: Any remaining circular imports or workarounds

**Checkpoint**: Test all features (auto-suggestions, keybindings, search functionality)

**Temporary Fixes**: Document any final workarounds before Phase 6 cleanup

### Phase 6: Clean up `main.py`
**Goal**: Make main.py a thin orchestrator

**Actions**:
- Simplify `main()` function
- Add type hints where beneficial
- Remove any remaining global state
- Ensure `main.py` is clean and focused
- **RESOLVE**: All remaining temporary fixes from previous phases
- **VERIFY**: No TODO: TEMPORARY FIX comments remain in codebase

**Checkpoint**: Final comprehensive functionality test

**Temporary Fixes**: Phase 6 should resolve ALL temporary fixes - none should remain

### Phase 0: Rename Directory Structure
**Goal**: Move from todo_txt_tui/ to src/ directory structure

**Actions**:
- Rename `todo_txt_tui/` directory to `src/`
- Update all import statements in `main.py` to use `src.` instead of `todo_txt_tui.`
- Update entry point from `python todo_txt_tui/main.py` to `python src/main.py`

**Checkpoint**: Test that `python src/main.py --help` and `python src/main.py --version` work

## Testing Strategy

**At Each Checkpoint**:
1. **Basic functionality**: `python src/main.py --help` and `--version`
2. **Full application**: Create test todo.txt file and verify:
   - Task display and sorting
   - Add/edit/delete tasks
   - Task completion and archiving
   - Search functionality
   - Keybinding operations
   - Auto-suggestions
   - File sync behavior
3. **Edge cases**: Test with various todo.txt formats, empty files, etc.

**Test Commands**:
```bash
# Activate environment
eval "$(conda shell.bash hook)" && conda activate todo

# Test basic functionality
python src/main.py --help
python src/main.py --version

# Test with sample todo.txt
echo "Test task due:2024-01-15 +project @context" > test_todo.txt
python src/main.py test_todo.txt
```

## Success Criteria

- ✅ All existing functionality preserved
- ✅ `python src/main.py` entry point works (moved from todo_txt_tui/core.py)
- ✅ Code organized into logical modules
- ✅ No breaking changes to user experience
- ✅ Improved maintainability and testability
- ✅ Clear separation of concerns

## Risk Mitigation

- **Incremental approach**: Each phase is small and testable
- **Backward compatibility**: Original entry point always works
- **Comprehensive testing**: Manual testing at every checkpoint
- **Rollback capability**: Each phase can be reverted if issues arise

## Notes

- This refactoring prioritizes **safety and functionality preservation** over architectural perfection
- Type hints and modern Python features will be added gradually where they don't risk breaking existing code
- The goal is **better organization**, not a complete rewrite
- **Always use `REFACTORING_TODO.md` to track progress** - it contains the detailed checklist and testing steps