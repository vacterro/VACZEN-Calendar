# Board

## DOING

## TODO
- [ ] T-010 Silent failures: bare `except: pass` in zen_calendar_gpt.py (~L405, L807) swallow errors | verify: add minimal error logging/handling
- [ ] T-011 Leftover `zen_calendar_gpt.py.backup` committed; 3 calendar variants (1/2/gpt) - canonical entry unclear | verify: remove .backup, document shipped .py

## DONE
- [x] T-001 VACZEN Calendar - README + EN/RU/ET translations (v0.0.1)
- [x] T-003 Set version 0.0.1 across source files
- [x] T-004 Connect GitHub remote
- [x] T-005 Initial push to GitHub
- [x] T-006 Add LICENSE (MIT)
- [x] T-007 Add .gitignore
- [x] T-008 Add CONTRIBUTING.md
- [x] T-009 Add version/license badges to README
- [x] CORE-001 Independent load per-section error isolation (all 3 files)
- [x] CORE-002 Settings validation/normalization (all 3 files)
- [x] CORE-003 Atomic save via temp+rename (all 3 files)
- [x] CORE-004 Keyboard bindings scoped to edit widgets (all 3 files)
- [x] W2-001 Generation counter for stale-write detection (all 3 files)
- [x] W2-002 Cancel semantics in v1 add_task/edit_task dialog chain
- [x] W2-003 Scrollable task container in v2 right panel
- [x] W2-004 Focus mode reset reconciliation in gpt
- [x] W2-005 Visible done-state feedback in v1 cell rendering
- [x] W2-006 Atomic settings apply with validation (all 3 variants)
- [x] W2-007 Navigation bounds for year domain date.min/max (all 3)
- [x] W2-008 Settings draft preservation in v2/gpt
- [x] PERF-001 Widget leak fix in v1 _update_cell_task_count
- [x] PERF-002 Selective day refresh in gpt (no full calendar rebuild)
- [x] PERF-003 Selective task row update in v2 _select_task
- [x] PERF-004 Clock tick optimization (smart interval)

## BLOCKED
