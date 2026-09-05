# CalendarTask -- Architecture

The entire application lives in one file, `ZEN_CALENDAR.py` (a single
self-contained module; ~2820 lines at the last audit sync -- regenerate
with `wc -l ZEN_CALENDAR.py`, do not hard-pin the count).
No third-party dependencies: standard library only (`calendar`, `json`,
`contextlib`, `sys`, `os`, `tempfile`, `time`, `dataclasses`, `datetime`,
`pathlib`, `tkinter`).

## Module map (by section, not line count)

| Section | Symbols | Contents |
|---|---|---|
| Imports | top | Stdlib imports; devnull redirect for `.pyw` runs |
| Constants | `APP_NAME`, `VERSION`, `app_dir`, `DATA_PATH` | App identity + data file location |
| `CalendarTask` | `to_dict`, `from_dict` | Task dataclass with safe text coercion |
| Defaults | `DEFAULT_SETTINGS`, `_BOOL_TRUE`, `_KINDS`, `_PRIORITIES` | Persisted-state defaults |
| Tunables | `LOCK_TIMEOUT_S`, `LOCK_RETRY_START_S`, `LOCK_RETRY_MAX_S`, `DETAIL_BATCH_CHARS`, `TMP_PREFIX`, `TMP_SUFFIX` | PERF-002/003/005 bounds: lock contention budget, detail-render batch size, atomic-temp naming contract |
| `UnreadableDataFile` | — | CORE-004 sentinel for present-but-unreadable data |
| `_platform_lock_path`, `_save_lock` | — | Interprocess lock: non-blocking OS primitive + bounded retry, fail-closed (raises `_LockAcquisitionFailure`; `.permanent` marks a failure retrying cannot fix) |
| `_parse_generation` | — | Strict ownership-token validation (CORE-003) |
| `_decode_state` | — | Pure `state`-section decoder shared by startup and reload (W2-002) |
| `normalize_settings` | — | Coercion/validation of persisted settings |
| `CompactCalendarApp` | (see below) | The application class |
| `__main__` | — | Tk root construction + mainloop |

## CompactCalendarApp methods (symbol-centered; not line-pinned)

References below are by **method name**, not line number. The single
authoritative implementation ships exactly one copy of every method; if
duplicates reappear, `_load`/`exit_app`/`_save` correctness regresses.
CORE-009 removed a dead duplicate `_bind_day_widget`; AST confirms exactly
one copy, so the "exactly one method" contract is now enforced, not
aspirational.

### Construction and lifecycle

- `__init__` — withdraw -> paint black -> `_load` -> `_apply_window_mode`
  -> `_build_style` -> `_build_ui` -> `_bind_keys` ->
  `reconcile_runtime_from_settings` -> `deiconify`. The
  withdraw/paint/deiconify dance prevents the OS-default white
  "flashbang" during startup. Startup deliberately shares the ONE
  reconciliation path with reload, so no derived runtime state exists on
  only one of the two (CORE-002).
- `reconcile_runtime_from_settings` — the single idempotent derivation of
  runtime from model: window attributes, ttk style/fonts, focus-mode
  packing plus fullscreen ownership, one clock callback, and the render.
  Startup, stale-writer reload, settings rollback and exception rollback all
  call it. Fullscreen intent is read from the settings, never re-sampled
  from the live attribute, which is what makes repeated calls idempotent.
  A call that arrives mid-edit defers the render half; `cancel_task` flushes
  it via `_flush_pending_reconcile`.
- `exit_app` — routes through the public dirty-aware `save()`, never
  `_save()` directly (CORE-001). `True` quits; `STALE_WRITER` and failure
  both require an explicit user decision before the root is destroyed. A
  clean exit does not advance the generation.

### Rendering and day widgets

- `_refresh_all` orchestrates `_render_header`, `_render_calendar`,
  `_render_side` (when not editing), and `_apply_detail_theme`.
- `_render_calendar` builds the weekday header row, optional ISO week
  numbers, and the 6x7 day-cell pool. Day cells are tracked in
  `self._day_widgets` so `_update_day_visuals` can restyle a single
  cell without a full grid rebuild.
- `_update_detail_box` accumulates output fragments in a Python buffer and
  flushes one `Text.insert` per `DETAIL_BATCH_CHARS` (PERF-003). Tcl
  crossings therefore scale with rendered bytes, not with tasks x fields,
  while a single huge note streams through the same bounded buffer so peak
  transient memory stays capped. Output is character-for-character identical
  to the per-fragment renderer.

### Persistence

- `save` (public) — returns `True` on success, `False` on failure, or the
  `STALE_WRITER` sentinel when another instance committed newer data
  (CORE-002/003). `STALE_WRITER` is **never** success: every caller branches
  on `is True` / `is STALE_WRITER` / otherwise, because the sentinel is
  truthy and a boolean check silently treated a lost conflict as a committed
  write (CORE-001). A clean instance does not advance the generation; a
  dirty instance advances it exactly once (W2-005).
- `_save` — checks the W2-001 write barrier, then wraps the
  read-check-write-replace sequence in `_save_lock`. The OS primitive stays
  non-blocking, but ordinary contention is retried with backoff to
  `LOCK_TIMEOUT_S` before failing closed (PERF-002), so another instance's
  ordinary save window no longer turns into a user-visible Save failure.
  There is no unlocked fallback, and a waiter that acquires the lock after
  another writer committed still becomes `STALE_WRITER`.
- `_save_locked` — takes the PERF-001 fast path when `_snapshot_identity()`
  still matches the snapshot this instance loaded or wrote: a clean save
  over an unchanged file is a true no-op (no parse, no serialize, no temp
  file, no replace), and a dirty save reuses the known generation instead of
  reparsing the whole payload. Any doubt -- unknown or changed identity,
  active recovery state -- falls through to the authoritative read/parse
  path, so an external writer cannot escape stale detection. Before creating
  its own temp file it reclaims crash-orphaned `TMP_PREFIX`*`TMP_SUFFIX`
  siblings (PERF-005), legal only because the global save lock is held.
- `_snapshot_identity` — file id + device + size + nanosecond mtime/ctime.
  Deliberately not `(size, mtime)`: a same-size replacement inside one
  timestamp tick would otherwise read as unchanged.
- `_read_disk_generation` — returns `None` for a missing file, raises
  `UnreadableDataFile` for a present-but-unreadable one (CORE-004).
- `_decode_snapshot` / `_load` — decode-then-commit. `_decode_snapshot`
  builds a COMPLETE fresh candidate (settings from `DEFAULT_SETTINGS.copy()`,
  fresh tasks, `_decode_state` for the view, generation 0) and touches no
  instance state, so identical bytes decode to an identical model no matter
  what the instance held (W2-002). `_load` then commits it atomically. A
  present-but-malformed `settings`/`state`/`tasks` section is partial
  recovery requiring preservation; a MISSING section is ordinary backward
  compatibility, and the two are never conflated (CORE-004).
- Write authorization (W2-001) — `_preservation_required` means the load
  dropped or could not represent persisted bytes; `_write_blocked` latches
  fail-closed when the immutable snapshot could not be created.
  `_preservation_ok` retries preservation once per save attempt, so a
  transient obstacle does not permanently brick saving, and every write path
  (clean save, manual save, mutation, settings, exit) refuses while the
  latch is set. `_load_failed` remains a warning flag only.
- `_reload_from_disk` — CORE-003 reload after a stale-writer rejection:
  resets the selection cache, re-runs `_load`, clears `_dirty`, then
  reconciles the runtime from the reloaded model. An active editor keeps its
  draft and the render half is deferred (CORE-002).
- `_quarantine_file` — preserves damaged data as an immutable, no-clobber
  snapshot (exclusive-create sequence: `DATA_PATH.corrupt.bak`, then
  `.001.bak`, `.002.bak`, ...) so a later corruption incident can never
  overwrite the only remaining copy (W2-001).
- `manual_save` — W2-004 explicit user Save (toolbar / Save key): surfaces
  exactly one message -- a `Save failed` error on `False`, a `Data
  reloaded` warning on `STALE_WRITER`, and never claims success on failure.
  A latched write barrier reports why saving is disabled instead of a
  generic failure, and `_warn_recovery_state` never names a quarantine path
  that was not actually created.

### Settings and editor

- `toggle_settings` -> `_sync_settings_vars` (only when opening, W2-008)
  -> user edits -> `apply_settings` -> `_commit_settings` (shared
  pipeline) -> `_build_style` + `_save` + `_refresh_all`.
- `apply_settings` validates the panel fields into a **full candidate
  settings dict**, runs `_commit_settings`, which diffs the candidate
  against the live settings as a `set` (W2-001), applies the changed
  runtime/visual effects, persists, and rolls back on failure. Every
  non-successful outcome -- `False`, `STALE_WRITER`, or an exception raised
  mid-staging -- restores the model and then reconciles the FULL runtime
  through `reconcile_runtime_from_settings` (W2-004). The old exception
  handler restored only `settings`/`_dirty`, leaving an already-applied
  `-topmost` contradicting the model it had just reverted; unexpected
  exceptions are still re-raised after rollback.
- `reset_settings` submits the complete `DEFAULT_SETTINGS` through
  `_commit_settings` (CORE-006) -- the same pipeline as Apply, so focus/
  fullscreen/clock/style/grid all reconcile to defaults and roll back on
  failure. It does NOT preassign `self.settings = DEFAULT_SETTINGS`, which
  would make the diff empty.
- `add_task` / `edit_task` -> `_show_edit_mode` -> `commit_task` /
  `cancel_task`. `commit_task` carries the existing task's `done` flag
  forward on edit (CORE-004), captures pre-mutation state, and rolls back
  on save failure (CORE-003). A blank or whitespace-only title is a
  **validation failure**, not an implicit Cancel: the editor stays open with
  every field intact and `edit_msg` says why (W2-003). On `STALE_WRITER` the
  typed draft is restored into the editor over the winner's snapshot rather
  than discarded (CORE-001).

### Navigation

- `_navigate_to` is the one candidate-then-commit primitive behind
  `prev_month` / `next_month` / `prev_year` / `next_year` / `go_today`.
  Domain validation runs first and `_dirty` is set only after `current` or
  `selected_day` actually changed, so a blocked boundary move (year 1,
  year 9999) or a `go_today` that lands on today is a genuine no-op and
  cannot advance the generation for an unchanged snapshot (W2-005).
- `select_day` marks the model dirty when the persisted `selected_day`
  really changes, so the next save advances the generation and two
  instances cannot overwrite the field at the same generation (CORE-005).

## Threading / event model

Single-threaded Tk. All periodic work runs through `root.after`
(`_tick_clock`). All writes to the data file happen synchronously
inside `_save` under the interprocess lock; contention waits are bounded by
`LOCK_TIMEOUT_S` so the GUI cannot block indefinitely.
