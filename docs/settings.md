# CalendarTask -- Settings

## Defaults

`DEFAULT_SETTINGS` defines every setting and its type: booleans
(fullscreen_start, always_on_top, week_start_monday,
show_week_numbers, show_clock, focus_mode, compact_header,
font_day_bold), ints (cell_gap=1, cell_padding=4, font sizes
16/10/9/10), strings (lang="en", theme="win95dark",
font_family="Verdana", font_mono="Courier New"), and fifteen
`color_*` hex strings. The default palette is the Win95 Dark theme:
black app background #000000, #141414 panels, #c0c0c0 text,
#9DD9F9 header/accents.

## Validation contract -- normalize_settings

Every persisted/UI-supplied value passes through `normalize_settings`,
which walks `DEFAULT_SETTINGS` key by key:

- Unknown keys are dropped (only known keys can enter `out`).
- Booleans: accept real bools, numeric 0/1, or the strings
  true/1/yes and false/0/no; anything else falls back to the default.
- Ints: `cell_gap` clamped 0..12, `cell_padding` clamped 0..20, font
  sizes clamped 6..72; other ints unclamped.
- Strings: `lang` restricted to ru/en/uk, `theme` to
  dark/light/win95dark, `color_*` keys must be `#` followed by exactly
  3 or 6 hex digits, remaining strings must be non-empty.
- Any raise inside coercion falls back to that key's default.

## Settings panel flow

- Toggle: `toggle_settings` flips `show_settings_panel`, syncing widget
  vars from live settings **only when opening** (W2-008). Mid-session
  refreshes do not clobber draft edits.
- Apply: `apply_settings` collects raw widget values, runs them through
  `normalize_settings` into a **candidate copy first** (W2-006), computes
  the diff against the live settings as a **set** (W2-001), reapplies
  topmost/fullscreen attributes, rebuilds style, saves, and rerenders.
  The candidate is committed to `self.settings` only after `_save`
  succeeds; on persistence failure the runtime effects and in-memory
  settings are rolled back (CORE-003).
- Color picks: `pick_color` stages the color in `self._draft_colors`;
  only Apply commits it. The staged colors join the same candidate
  transaction in `apply_settings`.
- Default: `reset_settings` syncs the Settings UI to `DEFAULT_SETTINGS`
  via `_sync_settings_vars_to_defaults`, then runs the normal
  `apply_settings` pipeline so the diff runs defaults against the
  current live settings (CORE-005). It does not preassign
  `self.settings = DEFAULT_SETTINGS` (that would make the diff empty and
  skip the reset).
- While Focus mode is active, a `fullscreen_start` change updates the
  deferred restore target `_pre_focus_fs` instead of forcing the live
  fullscreen attribute (W2-006).
