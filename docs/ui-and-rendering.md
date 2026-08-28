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

- `_render_calendar` rebuilds the weekday header row, optional ISO week
  numbers, and the 6x7 day-cell pool on month/year navigation. Day
  cells are recorded in `self._day_widgets`.
- `_update_day_visuals(day)` restyles a single day cell (borders, day
  number color, badge/dots) without rebuilding the whole grid (PERF-002).
- `_render_side` repopulates the Listbox from `self.tasks` for the
  selected day and restores the selection invariant.
- `_update_detail_box` renders the read-only detail pane (PERF-004
  builds the full text then inserts it in one call).

## Focus mode

`toggle_focus` flips `settings["focus_mode"]`;
`_apply_focus_visual` packs/unpacks top/btns/right/help, forces
fullscreen while active, and remembers the prior fullscreen state in
`_pre_focus_fs` for restore. When Focus is active and the user changes
`fullscreen_start` in Settings, the change updates `_pre_focus_fs` so
exiting Focus restores the newly requested state (W2-006). Add/edit are
no-ops while focus mode is on.

## Settings panel placement (PERF-001)

The Settings panel is placed once on show with
`place(relx=1.0, x=-20, y=70, width=460, height=560, anchor="ne")`,
which pins a 20 px right margin through Tk geometry itself. There is no
root-level `<Configure>` binding, so descendant widget geometry changes
do not generate Python reposition callbacks (PERF-001).

## Editor drafts (W2-002)

While `is_editing` is true, calendar navigation (month/year/today), day
clicks, Focus toggle, and window close refuse to silently discard the
draft or run `cancel_task` as an invisible prerequisite. Esc/Cancel is
the explicit discard path.
