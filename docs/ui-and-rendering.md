# CalendarTask -- UI and Rendering

## Layout tree (built in _build_ui)

```
root (black bg)
+-- top        : title "CalendarTask", subtitle, clock label
+-- btns       : nav (<< Year, < Month, Today, Month >, Year >>)
|                actions (Add, Edit, Del, Focus, Settings, Save, Support)
+-- main
|   +-- left   : month label, weekday header row, month grid
|   +-- right  : 340px panel -- day details
|         +-- view_frame : task listbox + read-only detail text
|         +-- edit_frame : add/edit form (Title, Time, Kind, Pri, Note,
|                          Save/Cancel) -- swapped in place of view_frame
+-- help_lbl   : one-line key reference
+-- settings_panel : floating 460x560 placed panel, scrollable canvas
```

## Theme system

- `_build_style` selects the `classic` ttk theme and reconfigures every
  style from the current settings dict: frame/label variants
  (`Panel.*`, `Muted.*`, `Title.*`, `Header.*`), raised Win95-style
  buttons with sunken pressed state, dark comboboxes. The combobox
  dropdown listboxes are darkened globally via
  `option_add('*TCombobox*Listbox.*')`.
- Day cells are plain `tk.Frame` stacks (cell_wrap -> cell -> inner ->
  top) so borders/backgrounds are exact: weekend background
  `color_weekend_bg`, today border `color_today_border`, selection
  `color_selected_border`, others #2a2a2a; thickness 2 for
  selected/today, else 1.
- Task presence shows as a count badge plus up to four dot glyphs.

## Rendering paths

- `_render_calendar` re-grids the weekday header row, optional ISO week
  numbers, and the 6x7 day-cell pool on month/year navigation. The pool
  is built **once** by `_ensure_calendar_pool` (PERF-002) and reused across
  navigation; `_bind_day_widget` is defined exactly once (CORE-009) and
  installs one-time `<Button-1>` bindings that resolve the day from the
  slot's mutable metadata, so no stale day number survives navigation. Day
  cells are tracked in `self._day_widgets`.
- `_update_day_visuals(day)` restyles a single day cell (borders, day
  number color, badge/dots) without rebuilding the whole grid (PERF-002).
  The count badge and up to four dot glyphs are created once per slot and
  updated in place (CORE-005), never recreated each render.
- `_render_side` repopulates the Listbox from `self.tasks` for the
  selected day and restores the selection invariant.
- `_update_detail_box` renders the read-only detail pane with **bounded
  batching**: fragments accumulate in a Python buffer and are flushed with
  one `Text.insert` per `DETAIL_BATCH_CHARS` (256 KiB), so Tcl crossings
  scale with rendered bytes instead of tasks x fields, and an arbitrarily
  large note streams through the same buffer rather than becoming one
  unbounded string. Measured on this machine: 5,000 ordinary tasks render in
  2 inserts (17.5 ms) where the per-fragment version issued ~35,000. Output
  is character-for-character identical, including the empty-day help text
  and the normal-then-disabled state handling.

## Focus mode

`toggle_focus` flips `settings["focus_mode"]`;
`_apply_focus_visual` packs/unpacks top/btns/right/help, forces
fullscreen while active, and remembers the prior fullscreen state in
`_pre_focus_fs` for restore. When Focus is active and the user changes
`fullscreen_start` in Settings, the change updates `_pre_focus_fs` so
exiting Focus restores the newly requested state (W2-006). Add/edit are
no-ops while focus mode is on.

Focus packing is derived state, not a side effect: `_apply_focus_visual`
takes `capture=False` when called from `reconcile_runtime_from_settings`, so
the restore target comes from the persisted `fullscreen_start` rather than a
re-sampled live attribute. That is what makes reconciliation idempotent --
calling it twice while focus mode is active cannot latch fullscreen as the
pre-focus state. A stale-writer reload therefore leaves the packed widget
set, the fullscreen attribute and the model in agreement; before the repair
the model could report focus mode active while every panel was still packed.

## Settings panel placement (PERF-001)

The Settings panel is placed once on show with
`place(relx=1.0, x=-20, y=70, width=460, height=560, anchor="ne")`,
which pins a 20 px right margin through Tk geometry itself. There is no
root-level `<Configure>` binding, so descendant widget geometry changes
do not generate Python reposition callbacks (PERF-001).

## Editor drafts (W2-002 + W2-003)

While `is_editing` is true, calendar navigation (month/year/today), day
clicks, Focus toggle, and window close refuse to silently discard the
draft or run `cancel_task` as an invisible prerequisite. Esc/Cancel is
the explicit discard path.

Pressing the normal commit action with a blank or whitespace-only title is a
validation failure, not an implicit Cancel: the editor stays open, every
other field keeps its value, focus returns to the title entry, and the
in-panel `edit_msg` label states the reason (W2-003). A stale-writer conflict
also keeps the draft -- `_restore_editor_draft` re-enters the editor over the
winning snapshot, retargeting an edit whose row no longer exists as a new
task rather than discarding the text.
