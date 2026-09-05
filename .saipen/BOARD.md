# Board

<!-- Ticket shape is RFC § 1.2's, exactly: a checkbox, the T-### id, a
     description, then only the fields that apply, space-pipe separated.
     Shown here WITHOUT its leading "- " on purpose (see below):

       [ ] T-001 short description | verify: pytest -q

     Other legal fields (RFC § 1.2): the dependency one, taking a
     comma-separated list of T-### this ticket waits on; owner and
     claim_time for claims (§ 1.4); blocker for facts + dead ends; verify as
     shown above. Named rather than shown here on purpose -- see below.

     A real line starts with "- ". Checkbox: [ ] open, [/] in progress
     (## DOING), [x] done (## DONE). A status change MOVES the line between
     sections -- cut and paste, never copy, or the same id ends up under two
     headings. All four headings below are required, even while empty.

     Why the example is de-fanged: neither validator skips HTML comments, so
     anything ticket-shaped in here is read as a real ticket on a brand-new,
     untouched board. Two separate traps, both hit for real while writing
     this very file: a full checkbox line parses as a live ticket, and the
     dependency field followed by an id is flagged as a dangling reference
     even without a leading dash -- tests/validate.sh scans for that field
     across the whole file, not only ticket lines, making it stricter here
     than tools/validate.py. So: no leading dash on any example, and never
     write that field name next to a concrete id anywhere in this file. -->

## DOING

## TODO

## DONE
- [x] T-24 [P1] Execute external audit inbox layer audit/1.md (SRC-002); source_receipt=SRC-002 | verify: every actionable clause of SRC-002 is terminal with evidence; linked Work DONE; source closure succeeds; audit/1.md consumed by the journaled audit inbox cleanup; source_receipt=SRC-002 | source_receipts: SRC-002 | owner: opencode | claim_time: 2026-09-05T17:37:46Z
- [x] T-20 [P1] README.md EN beauty: badges (build, license, version, python, code size, lines), tagline, hero screenshot slot, 3-col feature grid, keyboard cheatsheet, docs/ table, install/usage minimal, contributor CTA, license footer | verify: 181 lines; all gh-relative links resolve to existing tracked files; badges shields.io dynamic; screenshot slot HTML-commented for later | owner: opencode | claim_time: 2026-09-01T12:00:00Z
- [x] T-21 [P1] README.et.md beauty: full ET translation of T-20 structure, native phrasing, estonian tech terms (kalender, ülesanne, fookus, sätted, otsetee) | verify: 181 lines; structure section-for-section with README.md; estonian grammar checked; all real gh-relative links present | owner: opencode | claim_time: 2026-09-01T12:05:00Z
- [x] T-22 [P1] README.ru.md beauty: full RU translation of T-20 structure, native phrasing | verify: 181 lines; structure matches README.md section-for-section; russian grammar checked; all real gh-relative links resolve | owner: opencode | claim_time: 2026-09-01T12:07:00Z
- [x] T-23 [P2] gh repo metadata: description, topics, homepage, slug | verify: gh repo view returns description set, 8 topics live, homepageUrl set, name+slug intact, 423 total README lines (181*3) | owner: opencode | claim_time: 2026-09-01T12:10:00Z
- [x] T-19 [P2] PERF-005: lazy-construct Settings panel on first toggle_settings() open; enumerate font families once; retain cache; guard unconstructed-panel callers | verify: regression: cold startup with Settings never opened -- 76-control subtree absent; first open uses current settings/theme/colors/fonts; close/reopen widget identity stable; _font_families not re-enumerated | owner: opencode | claim_time: 2026-08-28T08:00:44Z
- [x] T-18 [P2] PERF-004: _update_detail_box builds text in buffer, single Text.insert; preserve ordering, fields, separators, disabled state | verify: regression: Text.get(1.0, end-1c) byte-equal to current renderer for zero tasks and combinations; 100/500/1000 task Xvfb benchmark materially reduced | owner: opencode | claim_time: 2026-08-28T08:00:43Z
- [x] T-17 [P1] PERF-003: _save streams via json.dump(payload, f, ...) instead of json.dumps + f.write; preserve atomic-replace + generation + locking | verify: regression: round-trip empty/normal/multi-MB notes byte-for-byte; tracemalloc on 8MB payload materially below 18MB; save latency preserved; lock/atomic/recovery unchanged | owner: opencode | claim_time: 2026-08-28T08:00:42Z
- [x] T-16 [P1] PERF-002: preallocate 7 weekday headers + 6x7 cell pool + up to 6 week-number labels; regrid/reconfigure on nav; bind once with mutable cell metadata | verify: regression: profile 20 alternating month/year nav before/after -- steady-state no longer ~170 widget constructions and ~122 binds per nav; 4/5/6-row months + week-start/iso-num variants render correctly; targeted select/task-badge updates work after repeated nav | owner: opencode | claim_time: 2026-08-28T08:00:28Z
- [x] T-15 [P1] PERF-001: remove root <Configure> binding; use place(relx=1.0, x=-20, anchor=ne) for Settings panel right margin | verify: regression: 20+ month navigations with Settings closed -- zero descendant reposition callbacks; resize 1100/1280/1500 -- 20px right margin preserved; Xvfb nav benchmark not regressed | owner: opencode | claim_time: 2026-08-28T08:00:07Z
- [x] T-14 [P1] W2-006: fullscreen_start during Focus updates _pre_focus_fs to validated candidate; _apply_focus_visual(False) restores newly requested state | verify: regression: non-FS + Focus + set FS-on + exit Focus -> FS stays on; FS-on + Focus + set FS-off + exit -> FS off; repeated Focus toggles; reset-to-defaults | owner: opencode | claim_time: 2026-08-28T07:53:20Z
- [x] T-13 [P1] W2-005: single authoritative task selection state; store selection+date key; update from <<ListboxSelect>>; clear/reinit on day/month/year change | verify: regression: select non-zero row, force same-day rerender -- same task selected; switch days/months -- stale idx does not migrate; Edit/Delete/Toggle Done always targets visibly selected task | owner: opencode | claim_time: 2026-08-28T07:53:19Z
- [x] T-12 [P1] W2-004: persisted text sanitizer/validator for task title/time/note and string settings; reject/replace lone surrogates; preserve all legitimate Unicode | verify: regression: round-trip ASCII/Cyrillic/Estonian/Japanese/emoji/combining; load lone high/low surrogate in title/time/note/font -- no UnicodeEncodeError; deterministic recovery | owner: opencode | claim_time: 2026-08-28T07:53:18Z
- [x] T-11 [P1] W2-003: load validates task keys; parser/normalizer shared with _task_key; canonical YYYY-MM-DD; impossible dates quarantined; collisions merge deterministically | verify: regression: load canonical keys, non-padded, leap-day, impossible dates, junk keys, two-collisions; valid tasks visible; collisions deterministic; impossible keys never silently survive | owner: opencode | claim_time: 2026-08-28T07:53:17Z
- [x] T-10 [P1] W2-002: centralize editor-transition guard; day click/Focus/Today/month-year/WM-close cannot silently discard active editor draft | verify: regression: open Add/Edit, modify title/time/note; test day click, month-year keys, Focus, Today, WM close, normal exit -- no path silently destroys draft; commit saves once; Esc/Cancel discards | owner: opencode | claim_time: 2026-08-28T07:53:16Z
- [x] T-9 [P1] W2-001: apply_settings uses set(changed) for &-intersections; preserve candidate through validation; do not commit self.settings before transaction succeeds | verify: regression: change one geometry, one style/color, always_on_top, fullscreen_start, show_clock independently + combined; no TypeError, exactly required runtime/render/persist runs; second Apply after first succeeds | owner: opencode | claim_time: 2026-08-28T07:53:15Z
- [x] T-8 [P2] CORE-007: docs match final ZEN_CALENDAR.py (architecture, data-model, canonical-ids, keyboard, overview, settings, ui-and-rendering) | verify: docs/architecture.md reports correct line count; canonical-ids markers point to live source; data-model persistence semantics match final _save | owner: opencode | claim_time: 2026-08-28T07:01:12Z
- [x] T-7 [P1] CORE-006: _save uses interprocess lock around read-check-write-replace; stale-writer rejection, two writers can't both commit | verify: regression: two writers from same gen: exactly one commits, loser reloads and next save succeeds; lock cleanup on error paths | owner: opencode | claim_time: 2026-08-28T05:01:47Z
- [x] T-6 [P1] CORE-005: reset_settings runs change pipeline against pre-reset state; persists defaults and applies window attributes/focus/style/grid refresh | verify: regression: reset from non-default topmost/fullscreen/colors/cell_gap leaves attrs==defaults, focus reconciled, _save called, reload restores defaults | owner: opencode | claim_time: 2026-08-28T05:01:46Z
- [x] T-5 [P1] CORE-004: _read_disk_generation distinguishes missing vs unreadable; unreadable existing file must be preserved via recovery/quarantine before overwriting | verify: regression: missing file saves; malformed/non-UTF-8 file fails without overwrite or succeeds only after backup | owner: opencode | claim_time: 2026-08-28T05:01:45Z
- [x] T-4 [P1] CORE-003: save() returns _save() result; commit_task/delete_task/toggle_done/toggle_focus/apply_settings surface failure and roll back or stay dirty; exit cannot discard unsaved state | verify: regression: forced _save=False across add/edit/delete/done/focus/settings Apply; no false durably-saved claim | owner: opencode | claim_time: 2026-08-28T05:01:44Z
- [x] T-3 [P0] CORE-002: _save generation transition: write next_generation+1, only advance memory after os.replace succeeds | verify: regression: 3 sequential saves all return True, disk gen advances 1->2->3, forced replace failure leaves gen unchanged | owner: opencode | claim_time: 2026-08-28T04:54:16Z
- [x] T-2 [P0] CORE-001: remove duplicate _load/exit_app definitions; single authoritative impl routing through _apply_state with quarantine; save-result-aware exit | verify: regression: exactly one _load and one exit_app in class | owner: opencode | claim_time: 2026-08-28T04:52:59Z

## BLOCKED
