# CalendarTask -- Overview

CalendarTask (single file `ZEN_CALENDAR.py`, version 0.0.1) is a
desktop calendar/task tracker built on Python's Tkinter toolkit. It
renders one month at a time in a Win95-dark themed grid, lets the user
attach tasks to days, and persists everything to a JSON file next to
the executable.

- Application class: `CompactCalendarApp` (defined in `ZEN_CALENDAR.py`).
- Data file: `CalendarTask_data.json` in the application directory
  (resolved by `app_dir()`).
- Default window: 1280x860, minsize 1000x680, starts fullscreen and
  always-on-top by default.

## Running

- `python ZEN_CALENDAR.py` (console attached), or rename/copy to `.pyw`
  or launch via `pythonw.exe` for a console-less run. The module detects
  `pythonw` / a missing stdout and redirects both streams to
  `os.devnull`.

## Feature summary

- Month grid with per-day cells: today/selected borders, weekend
  background, task count badge and up to four task dots.
- Day detail side panel: task list plus a read-only detail box.
- Task editor: title, time, kind (task/event/reminder), priority
  (low/normal/high), note. Editor drafts survive day clicks, focus
  toggles, navigation, today, and window close (W2-002); Esc/Cancel is
  the explicit discard path.
- Focus mode: hides chrome, forces fullscreen; remembers the prior
  fullscreen state for restore and updates that target when
  `fullscreen_start` changes while active (W2-006).
- Settings panel: booleans, spinboxes, font pickers, 15 color
  pickers, Apply/Default. Apply validates into a full candidate and runs
  the shared `_commit_settings` pipeline, which uses `set(changed)` for
  the diff (W2-001) and rolls back on persistence failure (CORE-003/006).
  Default submits `DEFAULT_SETTINGS` through the same pipeline (CORE-005/006).
- Live clock label, refreshed on a self-rescheduling `after` loop.
- Keyboard-driven navigation and task management (see keyboard.md).
- Single-file, stdlib-only, no third-party dependencies.
