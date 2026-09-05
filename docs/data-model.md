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
  reaching the Tk or UTF-8 output boundary. `sanitize_text` returns an ASCII
  string unchanged in O(1) (`str.isascii()`), because an ASCII string cannot
  contain a UTF-16 surrogate; non-ASCII strings still go through the
  surrogate detector and the surrogatepass/replace conversion (PERF-004).

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

## Write authorization comes first (W2-001)

Before the lock is even taken, `_save` consults `_preservation_ok()`. When a
load dropped or could not represent persisted records,
`_preservation_required` is set: an immutable quarantine snapshot MUST exist
before the reduced model may replace the original. If that snapshot could not
be created, `_write_blocked` latches and **every** write path refuses --
clean save, manual save, task mutation, settings commit and exit alike.

`_preservation_ok` retries the snapshot once per attempt, so clearing the
obstacle (freeing a backup name, fixing permissions) lets writes resume
without a restart. `_load_failed` is a warning flag and never an
authorization: the audit proved that a clean `save()` with `_dirty == False`
was enough to serialize a lossy recovered model over the only copy of the
records it had just dropped.

## Write path -- atomic replace, locked, generation-on-commit

`save()` (public) gates on dirtiness: a clean instance does not bump the
generation, so a redundant save cannot invent a conflict with another
instance; a dirty instance advances generation exactly once (W2-005). Either
way `_save` runs the whole read-check-write-replace sequence under
`_save_lock(DATA_PATH)`, a per-process re-entrant context manager that
acquires `msvcrt.locking` (`LK_NBLCK`, Windows) or `fcntl.flock`
(`LOCK_EX | LOCK_NB`, POSIX) on a sibling lock file.

The OS primitive stays **non-blocking**, but ordinary contention is
**retried with backoff** up to `LOCK_TIMEOUT_S` (0.25 s) and the eventual
timeout is **fail-closed** (PERF-002): `_save_lock` raises
`_LockAcquisitionFailure` and `_save` returns `False` without ever entering
the critical section. There is no unlocked fallback. A permanent failure
(open/permission) carries `permanent=True` and fails immediately instead of
burning the contention budget. Before the repair the lock failed on the
*first* busy result, so another instance's ordinary save window -- measured
at 283 ms for a 32 MiB dataset -- became a user-visible Save failure and a
rolled-back mutation.

On the locked path `_save_locked` does:

1. **Identity check (PERF-001).** `_snapshot_identity()` returns file id +
   device + size + nanosecond mtime/ctime. When it still equals the identity
   recorded at the last successful load/save, and no recovery state is
   active, the on-disk generation is already known:
   - a clean instance returns `True` immediately -- a true no-op: no parse,
     no serialize, no temp file, no `os.replace`;
   - a dirty instance reuses the known generation instead of decoding the
     whole payload to read one integer.
   Any doubt (unknown or changed identity, no usable filesystem id, pending
   preservation) falls through to step 2. Timestamps alone are never
   trusted: a same-size replacement inside one tick would otherwise read as
   unchanged and let an external writer escape stale detection.
2. `disk_gen = self._read_disk_generation()`. If the file is
   present-but-unreadable, `_read_disk_generation` raises
   `UnreadableDataFile`; `_save_locked` then requires preservation and treats
   the slot as `None` (CORE-004). Missing files still return `None` and start
   the generation counter cleanly.
3. If `disk_gen is not None and disk_gen != self._generation`,
   `_save_locked` raises `_StaleWriter`. `_save` catches it, calls
   `_reload_from_disk()`, and returns the `STALE_WRITER` sentinel so the
   caller reloads the winner's data instead of clobbering it.
4. Compute `next_gen = self._generation + 1` (or keep `self._generation` on a
   clean `advance=False` write) and build the payload with that generation in
   it. In-memory generation advances only after `os.replace` succeeds.
5. Reclaim crash-orphaned atomic-write candidates (PERF-005): stale
   `.cal_tmp_*.json` siblings in DATA_PATH's own directory are deleted while
   the global save lock is held, so no compliant live writer can own one.
   Best-effort, and never `DATA_PATH`, a `.corrupt*.bak` snapshot, the
   `.lock` file, an unrelated temp file, or this writer's own candidate.
6. Write the JSON to a temp file in the data directory and atomically replace
   it onto `DATA_PATH`. On any failure the temp file is unlinked and the
   in-memory generation stays where it was. On success the new snapshot
   identity is recorded for step 1.

`save()` returns `True` / `False` / `STALE_WRITER`. **`STALE_WRITER` is a
distinct outcome, never success** (CORE-001). It is truthy, so the former
`if not self.save():` checks in `commit_task` / `delete_task` /
`toggle_done` / `toggle_focus` fell through as though the write had
committed -- verified data loss in which a typed editor draft vanished and
the editor closed. Every caller now branches on `is True` /
`is STALE_WRITER` / otherwise, surfaces the conflict, and (for the editor)
restores the draft over the reloaded snapshot. `exit_app` routes through the
same public `save()` and requires an explicit user decision before
destroying the root on either a conflict or a failure; a clean exit does not
advance the generation.

## Load path -- decode then commit (W2-002 + CORE-004)

`_load` is two stages: `_decode_snapshot` builds a COMPLETE candidate model
from the file alone, then `_load` commits it atomically. Decoding touches no
instance state, so **identical bytes always decode to an identical model**
regardless of what the instance was holding. Before the repair `_load` merged
into the live settings, which made it history-dependent: a stale-writer
reload kept the *losing* instance's `cell_gap`/font sizes for any key the
winning snapshot omitted, and the next save wrote them back over the newer
file.

1. Missing file -> no-op (defaults remain).
2. Unreadable / undecodable / non-object payload -> `_load_failed`,
   preservation required, fresh dataset. The original bytes are preserved, or
   saving is latched closed if they cannot be.
3. `settings`: absent -> `DEFAULT_SETTINGS.copy()` unchanged; a dict ->
   validated through `normalize_settings` over that fresh copy; **present but
   not a dict** -> partial recovery requiring preservation (CORE-004). The
   old code skipped a malformed section as if absent, and the next save
   rewrote it as a normalized dict with no backup.
4. `tasks`: every key must be a string and every value a list; each entry is
   filtered through `CalendarTask.from_dict`. Task keys ARE canonicalized at
   load via `_canonical_task_key` (W2-003): recoverable keys are normalized
   to zero-padded `YYYY-MM-DD`; impossible / non-date keys are rejected from
   live `tasks`, recorded in `_invalid_task_keys` for forensics, and
   preserved in the quarantined original -- never stored as-is.
5. `state`: decoded by the pure `_decode_state` helper -- year/month/day
   coerced per field, month clamped to 1..12, day clamped into the month's
   length via `calendar.monthrange`. A present-but-malformed section is
   partial recovery; a missing one is the documented default.
6. `generation`: parsed via `_parse_generation` (CORE-003). Validation
   happens **before** conversion: an actual `int` (never `bool`), value >= 0.
   `1.5`, `"7"`, `True`, NaN/Infinity and every other type are rejected and
   routed through quarantine + reset to 0. The old parser called `int(raw)`
   first, so `1.5` became generation 1 and `True` became 1 -- coercing
   invalid values into ownership tokens no writer ever committed and
   collapsing distinct invalid values onto one generation.

A missing section and a present-but-malformed section are never conflated:
the first is backward compatibility, the second is recovery.

## Editor draft lifetime (W2-002 + W2-003)

Editor drafts (`edit_title` / `edit_time` / `edit_note` widget values)
are never written to `self.tasks` until `commit_task` succeeds and
persists. A day click, focus toggle, month/year nav, today, or
window-close while the editor is active therefore does NOT silently
discard the draft. Esc/Cancel is the only path that discards.

A blank or whitespace-only title is a **validation failure**, not an implicit
Cancel (W2-003): the editor stays open with time/note/kind/priority intact,
focus returns to the title field, and `edit_msg` states the reason. Pressing
the normal commit action used to call `cancel_task()`, which destroyed a
fully typed draft with no warning. A `STALE_WRITER` outcome also keeps the
draft, re-entering the editor over the winner's snapshot.
