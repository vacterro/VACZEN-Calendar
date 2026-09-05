# CalendarTask -- Canonical ID Registry

Every in-source audit/fix marker found in `ZEN_CALENDAR.py`, mirrored by
ID with its current location(s) and meaning. A fix that removes or moves
a marker must update this page; the page is rebuilt from these IDs, not
from line positions.

## Open findings implemented in the current build

| ID | Meaning | Where it lives |
|---|---|---|
| CORE-001 | Load path parses sections independently so one corrupt section cannot poison others | `_load` -- see data-model.md |
| CORE-002 | Generation written as `self._generation + 1`; in-memory only advances after `os.replace` succeeds | `_save` -- see data-model.md |
| CORE-003 | `save()` returns `_save()` (`True`/`False`/`STALE_WRITER`); `commit_task`, `delete_task`, `toggle_done`, `toggle_focus`, and the `_commit_settings` pipeline rollback on failure; `manual_save` surfaces exactly one message | `_save`, `_save_locked`, `_reload_from_disk`, `manual_save`, `_commit_settings`, `commit_task` |
| CORE-004 | `_read_disk_generation` distinguishes missing vs unreadable; `_save_locked` quarantines unreadable files before overwriting | `UnreadableDataFile`, `_quarantine_file` -- see data-model.md |
| CORE-005 | `reset_settings` submits the complete `DEFAULT_SETTINGS` through the shared `_commit_settings` pipeline (not a preassignment); focus/fullscreen/clock/style/grid reconcile to defaults and roll back on failure | `reset_settings` -> `_commit_settings(DEFAULT_SETTINGS.copy())` |
| CORE-006 | `_save_lock` is a non-blocking, fail-closed interprocess lock; `_commit_settings` is the single shared settings transaction (apply + reset) with rollback | `_save_lock` (raises `_LockAcquisitionFailure`), `_commit_settings`, `apply_settings`, `reset_settings` |
| CORE-007 | Generation parser shared by load and save sides; docs kept in sync with live symbols (CORE-011) | `_parse_generation`, `_read_disk_generation`, docs/* |
| CORE-008 | Settings change pipeline reconciles the clock on `show_clock` rollback so exactly one pending callback remains | `_commit_settings` (clock reconcile branch) |
| CORE-009 | Dead duplicate `_bind_day_widget` removed; exactly one authoritative definition remains (AST-verified) | `_bind_day_widget` |
| CORE-010 | Regression suite expanded to assert the full recorded invariant for every completed ticket (edit-done, reset/focus, pooled indicators, structural load, lock fail-closed, stale-writer, generation, clock rollback) | `.saipen/kitchen/regression_core_010.py` + existing probes |
| CORE-011 | Project-local docs regenerated from the final source/tests; no stale line counts, no "accepted as-is" key claims, no AST-disproved duplicate-method claims | docs/* |
| W2-001 | `apply_settings` uses `set(changed)` for intersections, not `dict & set` | `apply_settings` / `_commit_settings` |
| W2-002 | Editor drafts are not silently discarded by day click, focus, nav, today, or window close; impossible task keys are quarantined, not stored | `commit_task`, `cancel_task`, `select_day`, `toggle_focus`, `exit_app`, `_load` |
| W2-003 | Persisted task keys ARE canonicalized at load via `_canonical_task_key`; impossible/non-date keys are quarantined (original preserved), never stored as-is (W2-002 complete) | `_load`, `_canonical_task_key`, data-model.md |
| W2-004 | Persisted text is sanitized for lone UTF-16 surrogates before reaching Tk/UTF-8 | `CalendarTask.from_dict._text` (sanitizer) |
| W2-005 | Single authoritative task selection state owned by the Listbox + the `_selected_task_idx` cache, kept consistent via `_render_side` and `_selected_index` | `_render_side`, `_selected_index`, `select_day` |
| W2-006 | `fullscreen_start` changes during Focus update `_pre_focus_fs` to the validated candidate | `apply_settings` |
| PERF-001 | Root `<Configure>` binding removed; Settings panel uses `place(relx=1.0, x=-20, anchor="ne")` for the right margin | `_show_settings_panel`, `_bind_keys` |
| PERF-002 | Preallocated calendar widget pool: 7 weekday headers, up to 6 week numbers, 6x7 day-cell slots; one-time binds resolve the day from slot metadata; `_day_widgets` map enables targeted per-day visual updates | `_ensure_calendar_pool`, `_render_calendar`, `_slot_for_day`, `_update_day_visuals` |
| PERF-003 | `_save` streams the encoded JSON into the temp file via `json.dump` instead of materializing a full string first | `_save_locked` |
| PERF-004 | `_update_detail_box` builds the full text in a buffer, then inserts once | `_update_detail_box` |
| PERF-005 | Settings panel contents built lazily on first open (`_ensure_settings_built`); `_build_ui` no longer calls `_build_settings_panel` eagerly | `_ensure_settings_built`, `toggle_settings`, `_build_ui` |
| PERF-006 | `_load` releases the decoded source string before materializing tasks to cap startup memory | `_load` |
| W2-008 | Settings widget vars synced from live settings only when the panel is freshly opened, so mid-session refreshes do not clobber draft edits | `toggle_settings` / `_sync_settings_vars` |
| W2-010 | Clock loop advances exactly every second (1000 - microsecond offset) so it does not drift | `_tick_clock` |

## Second audit campaign (RUN acb-mtk31tg9, 2026-09-02)

The IDs above are the FIRST campaign's. The second campaign reused the same
`CORE-00n` / `W2-00n` / `PERF-00n` shape for different findings, so its rows
are namespaced here by campaign to keep both readable. Source markers for
this campaign name the wave in the comment ("CORE-003 (wave 3)",
"PERF-004 (wave 3)", "W2-001", ...) where a bare ID would collide.

| ID (campaign 2) | Meaning | Where it lives |
|---|---|---|
| C2/CORE-001 | `STALE_WRITER` is never success: every mutation and shutdown caller branches `is True` / `is STALE_WRITER` / otherwise; the editor draft survives a conflict; exit routes through the dirty-aware `save()`; a clean exit does not advance the generation | `commit_task`, `delete_task`, `toggle_done`, `toggle_focus`, `manual_save`, `exit_app`, `_notify_stale_reload`, `_editor_draft`, `_restore_editor_draft` |
| C2/CORE-002 | One idempotent runtime reconciliation derives window attrs, style, focus packing/fullscreen, the single clock callback and the render from the model; shared by startup, reload and both settings-rollback paths; a mid-edit reload defers the render half | `reconcile_runtime_from_settings`, `_flush_pending_reconcile`, `_apply_focus_visual(capture=…)`, `_reload_from_disk`, `__init__` |
| C2/CORE-003 | Generation validated before conversion: real `int`, `bool` excluded, `>= 0`; floats, numeric strings and NaN/Inf are rejected into the quarantine path instead of coerced | `_parse_generation`, `_read_disk_generation`, `_decode_snapshot` |
| C2/CORE-004 | A present-but-malformed `settings`/`state` section is partial-load corruption requiring preservation, not silent defaulting; missing stays distinct from malformed | `_decode_snapshot`, `_require_preservation` |
| C2/CORE-005 | A real `selected_day` change marks the model dirty so the next save advances the generation; selecting the same day is a no-op | `select_day` |
| C2/W2-001 | Failed preservation is a hard write barrier: `_preservation_required` + `_write_blocked` latch fail-closed and every write path refuses; retried per save attempt; a quarantine path is never recorded or displayed unless it was created | `_preservation_ok`, `_require_preservation`, `_latch_write_block`, `_save`, `_save_locked`, `_warn_recovery_state`, `_save_failure_text` |
| C2/W2-002 | Loading is decode-then-commit and history-independent: a complete fresh candidate is built from disk bytes alone and committed atomically; startup and reload share the decoder | `_decode_snapshot`, `_load`, `_decode_state` |
| C2/W2-003 | A blank/whitespace-only title is validation failure, not an implicit Cancel: the editor and every field survive and `edit_msg` says why | `commit_task`, `_set_edit_message`, `edit_msg` |
| C2/W2-004 | Every non-successful settings transaction (False, `STALE_WRITER`, or a mid-staging exception) restores the model and reconciles the full runtime through one path before re-raising | `_commit_settings` |
| C2/W2-005 | Navigation validates the domain first and marks dirty only after `current`/`selected_day` actually changed, so boundary and `go_today` no-ops cannot advance the generation | `_navigate_to`, `prev_month`, `next_month`, `prev_year`, `next_year`, `go_today` |
| C2/PERF-001 | Validated-snapshot-identity fast path: a clean save over an unchanged file is a true no-op and a dirty save skips the full payload parse; any doubt or active recovery state falls back to the authoritative path | `_snapshot_identity`, `_save_locked` |
| C2/PERF-002 | Bounded lock-acquisition retry with backoff to `LOCK_TIMEOUT_S`, fail-closed at the deadline, permanent errors flagged and failed immediately | `_save_lock`, `_LockAcquisitionFailure.permanent`, `LOCK_TIMEOUT_S` |
| C2/PERF-003 | Bounded batched detail rendering: fragments accumulate to `DETAIL_BATCH_CHARS` then one `Text.insert`; large notes stream through the same buffer; output byte-identical | `_update_detail_box`, `DETAIL_BATCH_CHARS` |
| C2/PERF-004 | `sanitize_text` returns ASCII strings unchanged in O(1) before the surrogate scan; non-ASCII handling untouched | `sanitize_text` |
| C2/PERF-005 | Crash-orphaned `.cal_tmp_*.json` candidates are reclaimed only while the interprocess save lock is held, matching the exact prefix/suffix in DATA_PATH's directory | `_reclaim_orphan_temps`, `TMP_PREFIX`, `TMP_SUFFIX` |

Campaign-2 regression coverage lives in
`.saipen/kitchen/regression_audit2_core.py`,
`regression_audit2_w2.py` and `regression_audit2_perf.py` (shared harness in
`regression_audit2_common.py`), including the PERF-004 detail-render probe the
first campaign's `regression_perf.py` docstring claimed but never contained.

Registry coverage note: IDs were discovered by scanning all `NAME-###`
markers in the source tree (`ZEN_CALENDAR.py` is the only source file).
All audit findings in this registry are implemented in the current
build; line positions are intentionally omitted in favor of symbol
anchors so the page survives refactors.
