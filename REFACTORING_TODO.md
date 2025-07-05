# TodoTxtTUI Refactoring Progress

## Overview
This file tracks the progress of refactoring todo_txt_tui from a monolithic `core.py` to a modern Python package structure using `src/` directory layout.

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
- [ ] Create `src/utils/__init__.py`
- [ ] Create `src/utils/helpers.py`
  - [ ] Move `debug()` function
  - [ ] Move `is_valid_date()` function
- [ ] Update imports in `main.py`

### Testing Phase 2
- [ ] **Debug Logging**: Verify debug function works
- [ ] **Date Validation**: Test date parsing functionality
- [ ] **Full Application**: Verify no functionality broken

**Phase 2 Status**: ❌ Not Started

---

## Phase 3: Extract Task Model & Logic
**Goal**: Separate task data operations from UI

### Actions
- [ ] Create `src/models/__init__.py`
- [ ] Create `src/models/task.py`
  - [ ] Create task data structures
  - [ ] Move task parsing logic
- [ ] Create `src/services/__init__.py`
- [ ] Create `src/services/task_service.py`
  - [ ] Move `Tasks` class
  - [ ] Maintain all existing methods
- [ ] Update imports in `main.py`

### Testing Phase 3
- [ ] **Task Operations**: Add new tasks
- [ ] **Task Operations**: Edit existing tasks
- [ ] **Task Operations**: Delete tasks
- [ ] **Task Operations**: Complete/uncomplete tasks
- [ ] **Task Operations**: Archive completed tasks
- [ ] **Task Parsing**: Verify priorities, due dates, contexts, projects
- [ ] **Task Sorting**: Verify sort order maintained
- [ ] **File Sync**: Verify file watching/syncing works
- [ ] **Search**: Verify task search functionality

**Phase 3 Status**: ❌ Not Started

---

## Phase 4: Extract UI Components
**Goal**: Organize UI components separately

### Actions
- [ ] Create `src/ui/__init__.py`
- [ ] Create `src/ui/widgets.py`
  - [ ] Move `CustomCheckBox` class
  - [ ] Move `TaskUI` class
- [ ] Update imports in `main.py`

### Testing Phase 4
- [ ] **UI Rendering**: Verify task list displays correctly
- [ ] **Checkbox Interactions**: Test task completion via UI
- [ ] **Task Display**: Verify colors, formatting, priorities
- [ ] **Task Grouping**: Verify due date groupings
- [ ] **Keybindings**: Test all keyboard shortcuts

**Phase 4 Status**: ❌ Not Started

---

## Phase 5: Extract Remaining Classes
**Goal**: Move remaining large classes

### Actions
- [ ] Create `src/services/auto_suggestions.py`
  - [ ] Move `AutoSuggestions` class
- [ ] Create `src/ui/components.py`
  - [ ] Move `Body` class
  - [ ] Move `Search` class
- [ ] Update imports in `main.py`

### Testing Phase 5
- [ ] **Auto-suggestions**: Test project/context auto-completion
- [ ] **Keybindings**: Test all keyboard shortcuts (j/k, gg/G, etc.)
- [ ] **Search**: Test search functionality (f key, filtering)
- [ ] **Navigation**: Test cursor movement and selection
- [ ] **Task Editing**: Test inline editing (e, E keys)
- [ ] **URL Handling**: Test URL opening (u, U keys)
- [ ] **Priority Filtering**: Test priority display filtering (Shift+1-9)
- [ ] **Task Visibility**: Test threshold/hidden task toggling (t, h keys)

**Phase 5 Status**: ❌ Not Started

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