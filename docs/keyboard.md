# CalendarTask -- Keyboard Reference

Bindings installed by `_bind_keys`. Every single-key binding is
suppressed while an editable widget (Entry, Text, Spinbox, Combobox)
holds focus, via `_is_editing_focused`, AND while the Settings panel
is open (W2-002).

| Key | Action | Handler |
|---|---|---|
| Left / Right | Previous / next month | `prev_month` / `next_month` |
| Up / Down | Previous / next year | `prev_year` / `next_year` |
| f | Toggle focus mode | `toggle_focus` |
| a | Add task to selected day | `add_task` |
| e | Edit selected task | `edit_task` |
| d | Delete selected task | `delete_task` |
| s | Save now | `save` |
| Space | Toggle done on selected task | `toggle_done` |
| Return | In editor: commit; otherwise refresh detail box | `handle_return` |
| Esc | Settings open -> close; editing -> cancel; else quit | `handle_escape` |
| Ctrl-k | Toggle settings panel | `toggle_settings` |
| Mouse wheel | Scroll settings panel (Windows + Linux Button-4/5) | `_scroll_settings` / `_scroll_settings_linux` |

Mouse: clicking a day cell selects it via `_bind_day_widget`;
double-clicking a task row toggles done.

Navigation guards: year stepping stops at `date.min.year` /
`date.max.year`; month switches clamp `selected_day` into the new
month's length. Navigation is also blocked while an editor session is
active (`_nav_guard`), so month/year keys do NOT silently discard an
in-progress draft.

Editor commit rules (`commit_task`): empty title cancels the edit;
kind/priority fall back to task/normal when blank; committing reuses
the existing task's `done` flag on edit. The pre-mutation state is
captured so a `_save` failure rolls back the in-memory change
(CORE-003) and surfaces a `Save failed` message.

Exit path: window close button and Esc both route through `exit_app`,
which calls `_save` first and, on persistence failure, asks the user
whether to discard the unsaved data before destroying the root.
