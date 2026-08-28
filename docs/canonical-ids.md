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
| CORE-003 | `save()` returns `_save()` bool; `commit_task` / `delete_task` / `toggle_done` / `toggle_focus` / `apply_settings` rollback on failure | see settings.md, data-model.md |
| CORE-004 | `_read_disk_generation` distinguishes missing vs unreadable; `_save` quarantines unreadable files before overwriting | `UnreadableDataFile`, `_quarantine_file` -- see data-model.md |
| CORE-005 | `reset_settings` runs the normal change pipeline via `apply_settings`; does not preassign defaults | `reset_settings` -> `_sync_settings_vars_to_defaults` -> `apply_settings` |
| CORE-006 | `_save` runs the entire read-check-write-replace under `_save_lock` (interprocess file lock) | `_save` -> `_save_locked` |
| CORE-007 | This documentation matches the live implementation | docs/* |
| W2-001 | `apply_settings` uses `set(changed)` for intersections, not `dict & set` | `apply_settings` |
| W2-002 | Editor drafts are not silently discarded by day click, focus, nav, today, or window close | `commit_task`, `cancel_task`, `select_day`, `toggle_focus`, `exit_app` |
| W2-003 | Persisted task keys (WIP) are accepted as-is; canonicalization and impossible-date quarantine are documented in data-model.md | data-model.md |
| W2-004 | Persisted text is sanitized for lone UTF-16 surrogates before reaching Tk/UTF-8 | `CalendarTask.from_dict._text` (sanitizer) |
| W2-005 | Single authoritative task selection state owned by the Listbox + the `_selected_task_idx` cache, kept consistent via `_render_side` and `_selected_index` | `_render_side`, `_selected_index`, `select_day` |
| W2-006 | `fullscreen_start` changes during Focus update `_pre_focus_fs` to the validated candidate | `apply_settings` |
| PERF-001 | Root `<Configure>` binding removed; Settings panel uses `place(relx=1.0, x=-20, anchor="ne")` for the right margin | `_show_settings_panel`, `_bind_keys` |
| PERF-002 | Preallocated calendar widget pool: 7 weekday headers, up to 6 week numbers, 6x7 day-cell slots; one-time binds resolve the day from slot metadata; `_day_widgets` map enables targeted per-day visual updates | `_ensure_calendar_pool`, `_render_calendar`, `_slot_for_day`, `_update_day_visuals` |
| PERF-003 | `_save` streams the encoded JSON into the temp file via `json.dump` instead of materializing a full string first | `_save_locked` |
| PERF-004 | `_update_detail_box` builds the full text in a buffer, then inserts once | `_update_detail_box` |
| PERF-005 | Settings panel contents built lazily on first open (`_ensure_settings_built`); `_build_ui` no longer calls `_build_settings_panel` eagerly | `_ensure_settings_built`, `toggle_settings`, `_build_ui` |

Registry coverage note: IDs were discovered by scanning all `NAME-###`
markers in the source tree (`ZEN_CALENDAR.py` is the only source file).
All audit findings in this registry are implemented in the current
build; line positions are intentionally omitted in favor of symbol
anchors so the page survives refactors.
