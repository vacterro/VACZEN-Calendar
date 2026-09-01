# VACZEN Calendar

> Distraction-free, single-file Tk calendar + task tracker.
> Win95-dark by default. One Python file, zero dependencies.

<p align="center">
  <img alt="License" src="https://img.shields.io/github/license/vacterro/VACZEN-Calendar?style=for-the-badge&color=9DD9F9">
  <img alt="Version" src="https://img.shields.io/badge/version-0.0.1-9DD9F9?style=for-the-badge">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-9DD9F9?style=for-the-badge&logo=python&logoColor=black">
  <img alt="Single file" src="https://img.shields.io/badge/single%20file-yes-9DD9F9?style=for-the-badge">
  <img alt="Dependencies" src="https://img.shields.io/badge/dependencies-stdlib%20only-9DD9F9?style=for-the-badge">
</p>

<p align="center">
  <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/vacterro/VACZEN-Calendar?style=flat-square">
  <img alt="Code size" src="https://img.shields.io/github/languages/code-size/vacterro/VACZEN-Calendar/ZEN_CALENDAR.py?style=flat-square&label=ZEN_CALENDAR.py">
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/vacterro/VACZEN-Calendar?style=flat-square">
  <img alt="Issues" src="https://img.shields.io/github/issues/vacterro/VACZEN-Calendar?style=flat-square">
</p>

<p align="center">
  <a href="https://buymeacoffee.com/vacuum34"><img alt="Support" src="https://img.shields.io/badge/%E2%9D%A4%EF%B8%8F%20Support-9DD9F9?style=for-the-badge"></a>
  <a href="docs/overview.md"><img alt="Docs" src="https://img.shields.io/badge/%F0%9F%93%9D%20Docs-9DD9F9?style=for-the-badge"></a>
  <a href="#-keyboard"><img alt="Keys" src="https://img.shields.io/badge/%E2%9C%A8%20Shortcuts-9DD9F9?style=for-the-badge"></a>
</p>

---

## 📸 Screenshot

```
┌──────────────────────────────────────────────────────────────┐
│  Tue 01 Sep 2026  14:23:07   ◀ ▶   September 2026   ⌂ Today  │
├──────────────────────────────────────────────────────────────┤
│  Mo  Tu  We  Th  Fr  Sa  Su                                  │
│       [ 1] [ 2] [ 3] [ 4] [ 5] [ 6]                          │
│   [ 7] [ 8] [ 9][10] [11] [12] [13]                          │
│  [14] [15] [16] [17] [18] [19] [20]                          │
│  [21] [22] [23] [24] [25] [26] [27]                          │
│  [28] [29] [30] [ 1] [ 2] [ 3] [ 4]                          │
│                                                              │
│            ┌─ Selected: Wed 16 Sep ─────────────┐            │
│            │ • 09:00  Team standup     [done]   │            │
│            │ • 14:00  Review PR #142            │            │
│            │ • 19:30  🏃 Run, you lazy sack   │            │
│            └────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
   Ctrl+K settings   f   focus   s   save   Esc   quit
```

> ASCII rendition — the real thing is dark by default, golden-on-black, and
> pixel-clean. Drop a real screenshot into `docs/screenshot.png` and uncomment
> below when you have one.

<!-- ![VACZEN Calendar running on Windows](docs/screenshot.png) -->

---

## ✨ Features

| | |
|---|---|
| 🎯 **Single file, single concern** | The whole app is `ZEN_CALENDAR.py`. No framework, no package, no vendored copies. |
| 📦 **Zero dependencies** | Python stdlib only. `tkinter`, `json`, `datetime`, `pathlib`. No `pip install`. |
| 🌑 **Win95-dark by default** | Black panels, golden accents, no animations, no antialiasing. Battery-friendly. |
| ⚡ **Keyboard-first** | Every action is one key. Mouse optional. |
| 💾 **Atomic save** | Interprocess-locked, generation-checked writes. Two instances never clobber each other. |
| 🛡️ **Self-healing load** | Bad JSON → quarantine, never overwrite the only copy. Corrupt dates are isolated, not dropped silently. |
| 🪟 **Focus mode** | One key (`f`) hides everything except the calendar. Distraction-proof. |
| ⚙️ **15-color theme** | Background, panels, text, headers, weekend, today, selected, accent — all live-tweakable. |
| 🌍 **i18n** | `lang: ru / en / uk`. Settings key, all UI strings follow. |
| 🔢 **ISO week numbers** | Optional column. |
| 🕐 **Live clock** | Bottom-right, self-rescheduling, never lags. |
| 📐 **Geometry that remembers** | Window size, position, fullscreen, always-on-top. Round-trips through the data file. |

---

## 🚀 Install

```bash
# 1. Clone
git clone https://github.com/vacterro/VACZEN-Calendar.git
cd VACZEN-Calendar

# 2. Run (no install step)
python ZEN_CALENDAR.py
```

That's it. Python 3.11 or newer. No virtualenv needed — there is nothing
to install. On Windows you can also rename to `.pyw` or launch via
`pythonw.exe` for a console-less run.

---

## ⌨️ Keyboard

Every binding below is suppressed while you type in an editor or while
the Settings panel is open, so you never lose a draft to a stray keypress.

| Key | Action |
|---|---|
| `←` / `→` | Previous / next month |
| `↑` / `↓` | Previous / next year |
| `f` | Toggle **focus mode** |
| `a` | Add task to selected day |
| `e` | Edit selected task |
| `d` | Delete selected task |
| `s` | Save now |
| `Space` | Toggle done on selected task |
| `Return` | Editor → commit; elsewhere → refresh detail box |
| `Esc` | Settings open → close; editing → cancel; else quit |
| `Ctrl+K` | Toggle settings panel |

---

## 📂 Project layout

```
VACZEN-Calendar/
├── ZEN_CALENDAR.py          ← the entire app
├── CalendarTask_data.json   ← your tasks (auto-created, gitignored)
├── ZenCalendar_data.json    ← (legacy) alt name for the same file
├── docs/                    ← architecture & reference
│   ├── overview.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── ui-and-rendering.md
│   ├── settings.md
│   ├── keyboard.md
│   └── canonical-ids.md
├── README.md                ← you are here
├── README.et.md             ← eesti
├── README.ru.md             ← русский
├── CONTRIBUTING.md
└── LICENSE                  ← MIT
```

---

## 📚 Documentation

| Doc | What it covers |
|---|---|
| [Overview](docs/overview.md) | What the app is, what it isn't. |
| [Architecture](docs/architecture.md) | Method-by-method map of `ZEN_CALENDAR.py`. No hand-waving. |
| [Data model](docs/data-model.md) | JSON shape, atomic save, quarantine, recovery. |
| [UI & rendering](docs/ui-and-rendering.md) | Theme, fonts, geometry, focus mode. |
| [Settings](docs/settings.md) | `DEFAULT_SETTINGS`, the validation contract, the apply pipeline. |
| [Keyboard](docs/keyboard.md) | The full key → handler table. |
| [Canonical IDs](docs/canonical-ids.md) | The names a refactor must not break. |

---

## 🤝 Contributing

Issues and PRs welcome. Bug reports: include your OS, Python version
(`python --version`), and the contents of the data file (or a
redacted excerpt — paths and notes can be sanitised).

For substantial changes, open an issue first so we can agree on the
shape before you spend a weekend on it. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## ❤️ Support

If this keeps you off your phone and in front of your actual schedule:

<a href="https://buymeacoffee.com/vacuum34"><img alt="Buy me a coffee" src="https://img.shields.io/badge/buyme%20a%20coffee-vacuum34-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>

---

## 📜 License

[MIT](LICENSE) — do what you want, just keep the copyright line.

---

<p align="center">
  <sub>VACZEN Calendar · v0.0.1 · single file · zero deps · keyboard-first</sub>
</p>
