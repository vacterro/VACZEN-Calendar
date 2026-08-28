# CalendarTask -- Architecture

The entire application lives in one file, `ZEN_CALENDAR.py` (1797 lines).
No third-party dependencies: standard library only (`calendar`, `json`,
`contextlib`, `sys`, `os`, `tempfile`, `dataclasses`, `datetime`,
`pathlib`, `tkinter`).

## Module map (by section, not line count)

| Section | Symbols | Contents |
|---|---|---|
| Imports | top | Stdlib imports; devnull redirect for `.pyw` runs |
| Constants | `APP_NAME`, `VERSION`, `app_dir`, `DATA_PATH` | App identity + data file location |
| `CalendarTask` | `to_dict`, `from_dict` | Task dataclass with safe text coercion |
| Defaults | `DEFAULT_SETTINGS`, `_BOOL_TRUE`, `_KINDS`, `_PRIORITIES` | Persisted-state defaults |
| `UnreadableDataFile` | — | CORE-004 sentinel for present-but-unreadable data |
| `_platform_lock_path`, `_save_lock` | — | CORE-006 interprocess lock helper |
| `normalize_settings` | — | Coercion/validation of persisted settings |
| `CompactCalendarApp` | (see below) | The application class |
| `__main__` | — | Tk root construction + mainloop |

## CompactCalendarApp methods (symbol-centered; not line-pinned)

References below are by **method name**, not line number. The single
authoritative implementation ships exactly one copy of every method; if
duplicates reappear, `_load`/`exit_app`/`_save` correctness regresses.

### Construction and lifecycle

- `__init__` — withdraw -> paint black -> `_load` -> `_apply_window_mode`
  -> `_build_style` -> `_build_ui` -> `_bind_keys` -> `_refresh_all` ->
  `_tick_clock` -> optional focus visuals -> `deiconify`. The
  withdraw/paint/deiconify dance prevents the OS-default white
  "flashbang" during startup.
- `exit_app` — `_save` first; on persistence failure ask the user
  whether to discard the unsaved data and destroy the root only on
  confirmation.

### Rendering and day widgets

- `_refresh_all` orchestrates `_render_header`, `_render_calendar`,
  `_render_side` (when not editing), and `_apply_detail_theme`.
- `_render_calendar` builds the weekday header row, optional ISO week
  numbers, and the 6x7 day-cell pool. Day cells are tracked in
  `self._day_widgets` so `_update_day_visuals` can restyle a single
  cell without a full grid rebuild.

### Persistence

- `save` (public) — returns the bool from `_save` so callers know
  whether the mutation hit disk (CORE-003).
- `_save` — wraps the read-check-write-replace sequence in `_save_lock`
  (CORE-006). On a present-but-unreadable file, quarantines the bytes
  before any replacement (CORE-004). Writes the next generation
  (`self._generation + 1`) and only advances in-memory generation if
  `os.replace` succeeds (CORE-002).
- `_read_disk_generation` — returns `None` for a missing file, raises
  `UnreadableDataFile` for a present-but-unreadable one (CORE-004).
- `_load` — validates every section independently, routes through
  `_apply_state` for date clamping, and raises/recovers on bad JSON,
  non-UTF-8 bytes, or out-of-range dates.
- `_quarantine_file` — preserves damaged data as
  `CalendarTask_data.json.corrupt.bak` before any subsequent write.

### Settings and editor

- `toggle_settings` -> `_sync_settings_vars` -> user edits ->
  `apply_settings` -> `_build_style` + `_save` + `_refresh_all`.
- `apply_settings` validates into a candidate, computes the diff
  against the live settings as a `set` (W2-001), runs the runtime
  effects, persists, and rolls back on save failure (CORE-003).
- `reset_settings` syncs the UI to `DEFAULT_SETTINGS` and runs the
  normal change pipeline (CORE-005). It does NOT preassign
  `self.settings = DEFAULT_SETTINGS`, which would make the diff empty.
- `add_task` / `edit_task` -> `_show_edit_mode` -> `commit_task` /
  `cancel_task`. `commit_task` captures pre-mutation state and rolls
  back on save failure (CORE-003).

## Threading / event model

Single-threaded Tk. All periodic work runs through `root.after`
(`_tick_clock`). All writes to the data file happen synchronously
inside `_save` under the interprocess lock.
