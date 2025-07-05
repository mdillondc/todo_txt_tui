# TodoTxtTUI Refactoring Progress

## Overview
This file tracks the progress of refactoring todo_txt_tui from a monolithic `core.py` to a modern Python package structure using `src/` directory layout.

## ⚠️ Temporary Fixes Protocol

**MANDATORY for all phases**: When implementing temporary workarounds during refactoring:

### 1. Mark in Code
```python
# TODO: TEMPORARY FIX - [Brief description of why this is temporary]
# This [specific issue] will be resolved in Phase [X] when [what happens]
[temporary code here]
```

### 2. Document in TODO File
Add a "⚠️ Temporary Fixes Applied" section to the completed phase:
```markdown
### ⚠️ Temporary Fixes Applied (To Be Resolved in Later Phases)
- **Issue**: [What temporary fix was applied]
- **Location**: [File and line number]
- **Reason**: [Why it was necessary at this phase]
- **Resolution**: [Which phase will fix it and how]
```

### 3. Track Resolution
- Add resolution tasks to the appropriate future phase
- Use `**RESOLVE**:` prefix for cleanup tasks
- Verify all temporary fixes are addressed before marking any phase complete

### 4. Final Cleanup
Phase 6 MUST resolve ALL temporary fixes:
- Search codebase for "TODO: TEMPORARY FIX" - should find none
- Verify no circular imports remain
- Confirm clean separation of concerns

**Why This Matters**: Temporary fixes are necessary for incremental refactoring, but they must be tracked and cleaned up to avoid technical debt.

---

## Pre-Refactoring Baseline
- [x] **Environment Setup**: Conda environment `todo` activated
- [x] **Dependencies Installed**: `pip install -r requirements.txt` completed
- [x] **Baseline Test**: `python todo_txt_tui/core.py --help` works
- [x] **Baseline Test**: `python todo_txt_tui/core.py --version` works
- [x] **Baseline Test**: Basic functionality with test todo.txt file works

## Phase 0: Rename Directory Structure
**Goal**: Move from todo_txt_tui/ to src/ directory structure

### Actions
- [x] Rename `todo_txt_tui/` directory to `src/`
- [x] Update all import statements in `main.py` to use `src.` instead of `todo_txt_tui.`
- [x] Update entry point from `python todo_txt_tui/main.py` to `python src/main.py`

### Testing Phase 0
- [x] **Basic Commands**: `python src/main.py --help`
- [x] **Basic Commands**: `python src/main.py --version`
- [x] **Full Application**: Verify app launches with test todo.txt
- [x] **Configuration**: Verify all imports work correctly

**Phase 0 Status**: ✅ Complete

---

## Phase 1: Extract Constants & Settings
**Goal**: Move global constants to dedicated config module

### Actions
- [x] Create `todo_txt_tui/__init__.py` (empty)
- [x] Create `todo_txt_tui/config/__init__.py`
- [x] Create `todo_txt_tui/config/settings.py`
  - [x] Move `PALETTE` 
  - [x] Move `COLORS`
  - [x] Move `SETTINGS`
  - [x] Move `setting_enabled()` function
- [x] Create `todo_txt_tui/config/constants.py`
  - [x] Move `__version__`
  - [x] Move `__sync_refresh_rate__`
  - [x] Move `__track_focused_task_interval__`
  - [x] Move regex patterns (`STRIP_X_FROM_TASK`, `PRIORITY_REGEX`, etc.)
- [x] Rename `core.py` to `main.py`
- [x] Update imports in `main.py`

### Testing Phase 1
- [x] **Basic Commands**: `python src/main.py --help`
- [x] **Basic Commands**: `python src/main.py --version`
- [x] **Full Application**: Create test todo.txt and verify app launches
- [x] **UI Rendering**: Verify colors/themes display correctly
- [x] **Settings**: Verify all settings work as expected

**Phase 1 Status**: ✅ Complete

---

## Phase 2: Extract Utility Functions
**Goal**: Move standalone helper functions

### Actions
- [x] Create `src/utils/__init__.py`
- [x] Create `src/utils/helpers.py`
  - [x] Move `debug()` function
  - [x] Move `is_valid_date()` function
- [x] Update imports in `main.py`

### Testing Phase 2
- [x] **Debug Logging**: Verify debug function works
- [x] **Date Validation**: Test date parsing functionality
- [x] **Full Application**: Verify no functionality broken

**Phase 2 Status**: ✅ Complete

---

## Phase 3: Extract Task Model & Logic
**Goal**: Separate task data operations from UI

### Actions
- [x] Create `src/models/__init__.py`
- [x] Create `src/models/task.py`
  - [x] Create task data structures
  - [x] Move task parsing logic
- [x] Create `src/services/__init__.py`
- [x] Create `src/services/task_service.py`
  - [x] Move `Tasks` class
  - [x] Maintain all existing methods
- [x] Update imports in `main.py`

### Testing Phase 3
- [x] **Task Operations**: Add new tasks
- [x] **Task Operations**: Edit existing tasks
- [x] **Task Operations**: Delete tasks
- [x] **Task Operations**: Complete/uncomplete tasks
- [x] **Task Operations**: Archive completed tasks
- [x] **Task Parsing**: Verify priorities, due dates, contexts, projects
- [x] **Task Sorting**: Verify sort order maintained
- [x] **File Sync**: Verify file watching/syncing works
- [x] **Search**: Verify task search functionality

**Phase 3 Status**: ✅ Complete

### ⚠️ Temporary Fixes Applied (To Be Resolved in Later Phases)
- **Circular Import Workarounds** (Will be fixed in Phase 4):
  - `from src.main import TaskUI` in task_service.py line 488
  - `from src.main import CustomCheckBox` in task_service.py line 601
  - These imports will be removed when UI components are extracted
- **Global Variable Placement** (Will be fixed in Phase 5):
  - Added `__focused_task_index__` and `__current_search_query__` to task_service.py lines 18-19
  - These globals don't belong in service layer - will be moved to proper location
- **Notes**: These workarounds allow Phase 3 to function while maintaining proper separation. They must be addressed in subsequent phases.

---

## Phase 4: Extract UI Components
**Goal**: Organize UI components separately

### Actions
- [x] Create `src/ui/__init__.py`
- [x] Create `src/ui/widgets.py`
  - [x] Move `CustomCheckBox` class
  - [x] Move `TaskUI` class
- [x] Update imports in `main.py`

### Testing Phase 4
- [x] **UI Rendering**: Verify task list displays correctly
- [x] **Checkbox Interactions**: Test task completion via UI
- [x] **Task Display**: Verify colors, formatting, priorities
- [x] **Task Grouping**: Verify due date groupings
- [x] **Keybindings**: Test all keyboard shortcuts

### ⚠️ Temporary Fixes to Address in Phase 4
- [x] **RESOLVE**: Phase 3 circular import workarounds for UI components
  - Remove `from src.main import TaskUI` in task_service.py
  - Remove `from src.main import CustomCheckBox` in task_service.py
- [x] **Document**: Any new temporary fixes needed for UI extraction
- [x] **Mark in Code**: Add `TODO: TEMPORARY FIX` comments for any workarounds
- [x] **Update TODO**: Document any new temporary fixes in this section

**Phase 4 Status**: ✅ Complete

### ⚠️ Temporary Fixes Applied (To Be Resolved in Later Phases)
- **Local Imports for Global Variables** (Will be fixed in Phase 5):
  - `import src.main as main_module` in widgets.py lines 80 and 247
  - Local imports used to avoid circular dependencies with global variables
  - These imports will be removed when globals are properly reorganized
- **Local Import for Tasks Class** (Will be fixed in Phase 5):
  - `from src.services.task_service import Tasks` in widgets.py line 235
  - Local import used to avoid circular dependency during module initialization
  - This will be resolved when global state is properly managed
- **Notes**: All Phase 3 circular import workarounds were successfully resolved. New temporary fixes are minimal and will be addressed in Phase 5.

---

## Phase 5: Extract Remaining Classes
**Goal**: Move remaining large classes

### Actions
- [x] Create `src/services/auto_suggestions.py`
  - [x] Move `AutoSuggestions` class
- [x] Create `src/ui/components.py`
  - [x] Move `Body` class
  - [x] Move `Search` class
- [x] Update imports in `main.py`

### Testing Phase 5
- [x] **Auto-suggestions**: Test project/context auto-completion
- [x] **Keybindings**: Test all keyboard shortcuts (j/k, gg/G, etc.)
- [x] **Search**: Test search functionality (f key, filtering)
- [x] **Navigation**: Test cursor movement and selection
- [x] **Task Editing**: Test inline editing (e, E keys)
- [x] **URL Handling**: Test URL opening (u, U keys)
- [x] **Priority Filtering**: Test priority display filtering (Shift+1-9)
- [x] **Task Visibility**: Test threshold/hidden task toggling (t, h keys)

### ⚠️ Temporary Fixes to Address in Phase 5
- [x] **RESOLVE**: Phase 3 global variable placement issues
  - Move `__focused_task_index__` and `__current_search_query__` from task_service.py to proper location
- [x] **RESOLVE**: Any remaining circular imports or dependencies
- [x] **Document**: Any new temporary fixes needed for remaining class extraction
- [x] **Mark in Code**: Add `TODO: TEMPORARY FIX` comments for any workarounds
- [x] **Update TODO**: Document any new temporary fixes in this section

**Phase 5 Status**: ✅ Complete

### ⚠️ Temporary Fixes Applied (To Be Resolved in Later Phases)
- **All Previous Temporary Fixes Resolved**: Successfully removed all global variables from task_service.py and moved them to main.py
- **Circular Import Issues Resolved**: Eliminated all local imports in widgets.py by passing global variables as parameters
- **Clean Module Structure**: All classes properly extracted with clear separation of concerns
- **Notes**: Phase 5 successfully completed with no remaining temporary fixes. All TODO: TEMPORARY FIX comments have been removed from codebase.

---

## Phase 6: Clean up main.py
**Goal**: Make main.py a thin orchestrator

### Actions
- [ ] Simplify `main()` function
- [ ] Add type hints where beneficial
- [ ] Remove any remaining global state
- [ ] Ensure `main.py` is clean and focused

### Testing Phase 6
- [ ] **Complete Functionality Test**: Run through all features
- [ ] **Edge Cases**: Test with various todo.txt formats
- [ ] **Performance**: Verify no performance regressions
- [ ] **Error Handling**: Test error scenarios

### ⚠️ Temporary Fixes - FINAL CLEANUP
- [ ] **RESOLVE**: All remaining temporary fixes from previous phases
- [ ] **VERIFY**: No `TODO: TEMPORARY FIX` comments remain in codebase
- [ ] **CONFIRM**: All circular imports resolved
- [ ] **CONFIRM**: All global variables properly located
- [ ] **CONFIRM**: Clean import structure throughout codebase
- [ ] **FINAL CHECK**: Search entire codebase for "TEMPORARY FIX" - should find none

**Phase 6 Status**: ❌ Not Started

---

## Final Verification
- [ ] **All Original Features**: Every feature from original core.py works
- [ ] **Entry Point**: `python todo_txt_tui/main.py` works identically to original
- [ ] **File Compatibility**: Works with existing todo.txt files
- [ ] **Settings**: All configuration options work
- [ ] **Keybindings**: All keyboard shortcuts work
- [ ] **Auto-completion**: Project/context suggestions work
- [ ] **File Sync**: External file changes are detected
- [ ] **Performance**: No noticeable performance impact
- [ ] **Config**: Check line `# ~/.config/todo-txt-tui/settings.conf` settings.py and tell me if that is just a holdover comment or if the feature to add config to ~/.config is actually implemented. If that is not implemented, delete the comment.
- [ ] **README**: Update any required part of README.md to fit the refactor

## Test Commands Reference
```bash
# Activate environment
eval "$(conda shell.bash hook)" && conda activate todo

# Basic functionality tests
python src/main.py --help
python src/main.py --version

# Full application test
echo "Test task due:2024-01-15 +project @context" > test_todo.txt
echo "(A) High priority task" >> test_todo.txt
echo "x 2024-01-01 Completed task" >> test_todo.txt
python src/main.py test_todo.txt
```

## Notes
- Each phase must be completed and verified before moving to the next
- Any issues found during testing should be documented here
- Rollback to previous working state if critical issues are discovered