# CalendarTask -- Data Model and Persistence

## CalendarTask

A `@dataclass` with six fields. Defined in `ZEN_CALENDAR.py`; the class
itself does not pin a line number because the section is short and
stable.

| Field | Type | Default |
|---|---|---|
| `title` | str | (required, coerced to str) |
| `time` | str | `""` |
| `note` | str | `""` |
| `done` | bool | `False` |
| `kind` | str | `"task"` (in `{task, event, reminder}`) |
| `priority` | str | `"normal"` (in `{low, normal, high}`) |

- `to_dict()` returns the plain dict form for JSON serialization.
- `from_dict(d)` is defensive: non-dict input becomes an empty task,
  every field is coerced (`str`/`bool`) with defaults for missing
  values. Text fields are sanitized for lone surrogates (W2-004) before
  reaching the Tk or UTF-8 output boundary.

## Storage layout

File: `CalendarTask_data.json`, in `app_dir()` -- the directory of the
frozen executable when packaged (`sys.frozen`), else of the source file
(defined near the top of `ZEN_CALENDAR.py`).

JSON payload written by `_save`:

```json
{
  "settings": { "...": "merged settings dict" },
  "tasks": {
    "YYYY-MM-DD": [
      { "title": "...", "time": "", "note": "",
        "done": false, "kind": "task", "priority": "normal" }
    ]
  },
  "state": { "year": 2026, "month": 8, "selected_day": 23 },
  "generation": 1
}
```

Task keys are built by `_task_key` as zero-padded
`{year:04d}-{month:02d}-{day:02d}` for the displayed month and the
selected or given day. Days with no tasks are simply absent.

## Write path -- atomic replace, locked, generation-on-commit (CORE-002 + CORE-006)

`_save` runs the entire read-check-write-replace sequence under
`_save_lock(DATA_PATH)`, a per-process re-entrant context manager that
acquires `msvcrt.locking` (Windows) or `fcntl.flock` (POSIX) on a
sibling `CalendarTask_data.json.lock` file. On the locked path the
method does:

1. `disk_gen = self._read_disk_generation()`. If the file is
   present-but-unreadable, `_read_disk_generation` raises
   `UnreadableDataFile`; `_save` then calls `_quarantine_file` and
   treats the slot as `None` (CORE-004). Missing files still return
   `None` and start the generation counter cleanly.
2. If `disk_gen is not None and disk_gen != self._generation`, refuse
   with `return False` -- the stale-writer guard.
3. Compute `next_gen = self._generation + 1` and build the payload with
   that generation in it (CORE-002). In-memory generation is only
   advanced after `os.replace` succeeds.
4. Write the JSON to a temp file in the data directory and atomically
   replace it onto `DATA_PATH`. On any failure, the temp file is
   unlinked and the in-memory generation stays where it was.

`save()` (public) returns the bool from `_save` so mutation callers
can detect persistence failure and roll back (CORE-003).

## Load path -- independent section parsing (CORE-001)

`_load` parses each top-level section on its own so one corrupt section
cannot poison the others:

1. Missing file -> no-op (defaults remain).
2. Present but unreadable (OSError, UnicodeError, JSON error, wrong
   top-level shape, non-int generation) -> `_load_failed = True`,
   attempt quarantine, and start fresh.
3. `settings`: validated through `normalize_settings`; only keys
   present in `DEFAULT_SETTINGS` are merged.
4. `tasks`: every key must be a string and every value a list; each
   entry is filtered through `CalendarTask.from_dict`. Task keys are
   not currently canonicalized at load time -- keys that survive are
   stored as-is.
5. `state`: year/month/day coerced with per-field try/except; month
   must be 1..12; day clamped into the month's length via
   `calendar.monthrange`. Routed through `_apply_state`.
6. `generation`: restored raw, default 0.

## Editor draft lifetime (W2-002)

Editor drafts (`edit_title` / `edit_time` / `edit_note` widget values)
are never written to `self.tasks` until `commit_task` succeeds and
persists. A day click, focus toggle, month/year nav, today, or
window-close while the editor is active therefore does NOT silently
discard the draft. Esc/Cancel is the only path that discards.
