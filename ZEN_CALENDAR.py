"""
Слушай сюда, мамкин хакер. Какого хера у тебя на скриншоте комбобоксы белые, как задница привидения? Выглядит как кусок дерьма. Я выжег этот свет нахуй. Теперь всё в строгом Win95 Dark, как приборная панель ебаного стелс-бомбардировщика. 

Твои "светошумовые гранаты" (flashbangs) при ресайзе — это потому что Tkinter по дефолту рендерит белую подложку ОС, пока виджеты не успели перерисоваться. Ты наслаждался этим дерьмом каждый раз, дергая окно. Я залил корень абсолютно черным цветом до того, как главное окно вообще появляется на экране (через withdraw/deiconify), и заставил фреймы плотно жрать пространство. Больше твои нежные глазки не вытекут на клавиатуру.

Кнопки в кнопках? Это конфликт бордеров классической темы, когда ты пихаешь raised элементы в sunken фреймы без отступов. Я снес лишние рамки и выровнял геометрию. Теперь это четкие, суровые кнопки из девяностых, которые хочется нажимать, а не плакать, глядя на них.

А чтобы убрать ебаную консоль — сохраняй этот файл с расширением `.pyw`, а не `.py`. Либо запускай через `pythonw.exe`. Машина не читает твои мысли, ей нужны четкие инструкции. Я обернул код так, чтобы он не крашился при попытке высрать ошибки в несуществующий stdout.

Белая вспышка бьет,
Смерть глазам в ночной тиши.
Тьма спасет твой код.
"""

import calendar
import json
import re
import sys
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, font as tkfont

# Redirect stderr/stdout to null if running as .pyw without a console
if sys.executable.endswith("pythonw.exe") or sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

APP_NAME = "CalendarTask"
VERSION = "0.0.1"

def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

DATA_PATH = app_dir() / "CalendarTask_data.json"

@dataclass
class CalendarTask:
    title: str
    time: str = ""
    note: str = ""
    done: bool = False
    kind: str = "task"
    priority: str = "normal"

    def to_dict(self):
        return {
            "title": self.title,
            "time": self.time,
            "note": self.note,
            "done": self.done,
            "kind": self.kind,
            "priority": self.priority,
        }

    @staticmethod
    def from_dict(d):
        if not isinstance(d, dict):
            d = {}

        def _text(v):
            return "" if v is None else sanitize_text(str(v))

        def _done(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float)):
                return bool(v)
            if isinstance(v, str):
                s = v.strip().lower()
                if s in _BOOL_TRUE:
                    return True
                return False
            return False

        done = _done(d.get("done", False))
        kind = _text(d.get("kind", "task")).strip().lower()
        if kind not in _KINDS:
            kind = "task"
        priority = _text(d.get("priority", "normal")).strip().lower()
        if priority not in _PRIORITIES:
            priority = "normal"
        return CalendarTask(
            title=_text(d.get("title")),
            time=_text(d.get("time")),
            note=_text(d.get("note")),
            done=done,
            kind=kind,
            priority=priority,
        )

DEFAULT_SETTINGS = {
    "week_start_monday": True,
    "show_week_numbers": False,
    "show_clock": True,
    "fullscreen_start": True,
    "always_on_top": True,
    "focus_mode": False,
    "theme": "win95dark",
    "cell_gap": 1,
    "cell_padding": 4,
    "compact_header": True,
    "lang": "en",
    "font_family": "Verdana",
    "font_mono": "Courier New",
    "font_title_size": 16,
    "font_body_size": 10,
    "font_small_size": 9,
    "font_day_size": 10,
    "font_day_bold": True,
    "color_app_bg": "#000000",
    "color_panel_bg": "#141414",
    "color_text": "#c0c0c0",
    "color_muted": "#808080",
    "color_header": "#9DD9F9",
    "color_button_bg": "#1e1e1e",
    "color_button_fg": "#c0c0c0",
    "color_button_active": "#141414",
    "color_weekend_bg": "#0a0a0a",
    "color_today_border": "#9DD9F9",
    "color_selected_border": "#c0c0c0",
    "color_task_dot": "#9DD9F9",
    "color_today_text": "#ffffff",
    "color_detail_bg": "#111111",
    "color_detail_fg": "#c0c0c0",
}


_BOOL_TRUE = {"true", "1", "yes", "y", "on", "1.0"}
_KINDS = {"task", "event", "reminder"}
_PRIORITIES = {"low", "normal", "high"}


def sanitize_text(s):
    """W2-004: strip isolated UTF-16 surrogate code points from a Python str.

    Preserves every legitimate Unicode scalar value (ASCII, Cyrillic,
    Estonian diacritics, Japanese, emoji, combining marks). An isolated
    high or low surrogate has no corresponding scalar value and crashes
    `tkinter.Tcl` / UTF-8 output with `UnicodeEncodeError`; replace each
    with the official U+FFFD replacement character instead of letting it
    through to Tk or the disk writer.
    """
    if not isinstance(s, str):
        return s
    return s.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


class UnreadableDataFile(Exception):
    """CORE-004: DATA_PATH exists but cannot be read/decoded/parsed.

    Distinct from a missing file: a missing file may be safely created
    fresh, while a present-but-unreadable file MUST be preserved
    (quarantined) before any subsequent write.
    """


def _platform_lock_path(data_path):
    return data_path.with_name(data_path.name + ".lock")


@contextmanager
def _save_lock(data_path):
    """CORE-006: interprocess file lock spanning the entire read-check-write-
    replace sequence. The lock is best-effort: when the platform exposes a
    usable stdlib mechanism we use it; when it does not we still get a
    per-process mutex (so re-entrant calls inside one process serialize)
    and the stale-writer check still rejects out-of-process races that beat
    us to the disk after we missed the lock.
    """
    lock_path = _platform_lock_path(data_path)
    in_process = _save_lock._held
    if in_process:
        # Same process: re-entrant serialization.
        yield
        return
    fd = None
    locked = False
    try:
        try:
            data_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
            if os.name == "nt":
                try:
                    import msvcrt  # type: ignore
                    msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
                    locked = True
                except (OSError, ImportError):
                    locked = False
            else:
                try:
                    import fcntl  # type: ignore
                    fcntl.flock(fd, fcntl.LOCK_EX)
                    locked = True
                except (OSError, ImportError):
                    locked = False
            _save_lock._held = True
            yield
        except BaseException:
            raise
    finally:
        _save_lock._held = False
        if fd is not None:
            if locked and os.name == "nt":
                try:
                    import msvcrt  # type: ignore
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                except (OSError, ImportError):
                    pass
            elif locked:
                try:
                    import fcntl  # type: ignore
                    fcntl.flock(fd, fcntl.LOCK_UN)
                except (OSError, ImportError):
                    pass
            try:
                os.close(fd)
            except OSError:
                pass


_save_lock._held = False  # type: ignore[attr-defined]


_TASK_KEY_RE = re.compile(r"^\s*(\d{1,4})-(\d{1,2})-(\d{1,2})\s*$")


def _canonical_task_key(raw):
    """W2-003: shared parser/normalizer for task keys.

    Returns the canonical `YYYY-MM-DD` string for a real, addressable
    date, or `None` if the key cannot be interpreted as a real date.
    Keys are accepted loosely (any whitespace, unpadded month/day,
    up-to-4-digit year) so existing data migrates; impossible dates
    (2026-02-31, year 10000, etc.) are rejected.
    """
    if not isinstance(raw, str):
        return None
    m = _TASK_KEY_RE.match(raw)
    if not m:
        return None
    try:
        y = int(m.group(1))
        mo = int(m.group(2))
        d = int(m.group(3))
    except ValueError:
        return None
    if not (date.min.year <= y <= date.max.year):
        return None
    if not (1 <= mo <= 12):
        return None
    try:
        dmax = calendar.monthrange(y, mo)[1]
    except (ValueError, OverflowError):
        return None
    if not (1 <= d <= dmax):
        return None
    return f"{y:04d}-{mo:02d}-{d:02d}"


def _is_non_finite(v):
    if isinstance(v, float):
        return v != v or v in (float("inf"), float("-inf"))
    return False


def _is_hex_color(s):
    if not isinstance(s, str):
        return False
    if len(s) not in (4, 7):
        return False
    if not s.startswith("#"):
        return False
    try:
        int(s[1:], 16)
        return True
    except ValueError:
        return False


def normalize_settings(raw):
    """Validate and coerce persisted settings to safe runtime values."""
    out = {}
    for key, default in DEFAULT_SETTINGS.items():
        if key not in raw:
            continue
        val = raw[key]
        try:
            if isinstance(default, bool):
                if isinstance(val, bool):
                    out[key] = val
                elif isinstance(val, (int, float)) and not _is_non_finite(val):
                    out[key] = bool(val)
                elif isinstance(val, str) and val.strip().lower() in ("true", "1", "yes"):
                    out[key] = True
                elif isinstance(val, str) and val.strip().lower() in ("false", "0", "no"):
                    out[key] = False
                else:
                    out[key] = default
            elif isinstance(default, int):
                if _is_non_finite(val):
                    out[key] = default
                    continue
                iv = int(val)
                if key == "cell_gap":
                    out[key] = max(0, min(iv, 12))
                elif key == "cell_padding":
                    out[key] = max(0, min(iv, 20))
                elif key in ("font_title_size", "font_body_size", "font_small_size",
                             "font_day_size"):
                    out[key] = max(6, min(iv, 72))
                else:
                    out[key] = iv
            elif isinstance(default, str):
                sv = sanitize_text(str(val).strip())
                if key == "lang":
                    out[key] = sv if sv in ("ru", "en", "uk") else default
                elif key == "theme":
                    out[key] = sv if sv in ("dark", "light", "win95dark") else default
                elif key.startswith("color_"):
                    out[key] = sv if _is_hex_color(sv) else default
                else:
                    out[key] = sv if sv else default
        except (ValueError, TypeError, AttributeError, OverflowError):
            out[key] = default
    return out


class CompactCalendarApp:
    _FONT_FAMILIES_CACHE = None

    def __init__(self, root: tk.Tk):
        self.root = root
        # PREVENT FLASHBANGS: Hide instantly, paint black, then show
        self.root.withdraw()
        self.root.configure(bg="#000000")
        
        self.root.title(APP_NAME)
        self.root.geometry("1280x860")
        self.root.minsize(1000, 680)
        self.settings = DEFAULT_SETTINGS.copy()
        self.tasks = {}
        self.current = date.today().replace(day=1)
        self.selected_day = date.today().day
        self.show_settings_panel = False
        self.is_editing = False
        self.editing_idx = None
        self._pre_focus_fs = True
        self._generation = 0
        self._loaded_generation = 0
        self._load_failed = False
        self._quarantine_path = None
        self._draft_settings = None
        self._day_widgets = {}
        self._last_observed_date = None
        self._clock_after_id = None
        self._selected_task_idx = None

        self._load()
        self._apply_window_mode()
        self._build_style()
        self._build_ui()
        self._bind_keys()
        self._refresh_all()
        self._tick_clock()
        
        if self.settings.get("focus_mode", False):
            self._apply_focus_visual(True)
            
        self.root.update_idletasks()
        self.root.deiconify()
        if self._load_failed:
            self.root.after(200, lambda: messagebox.showwarning(
                "Data file was corrupt",
                "The data file could not be read and was quarantined as\n"
                f"{self._quarantine_path or DATA_PATH.name + '.corrupt.bak'}.\n"
                "A fresh dataset has been started.",
                parent=self.root,
            ))

    def _base_bg(self):
        return self.settings["color_app_bg"]

    def _panel_bg(self):
        return self.settings["color_panel_bg"]

    def _text_fg(self):
        return self.settings["color_text"]

    def _muted_fg(self):
        return self.settings["color_muted"]

    def _apply_window_mode(self):
        self.root.attributes("-fullscreen", self.settings.get("fullscreen_start", True))
        self.root.attributes("-topmost", self.settings.get("always_on_top", True))
        self._pre_focus_fs = self.settings.get("fullscreen_start", True)

    def _font(self, size, bold=False, mono=False):
        fam = self.settings["font_mono"] if mono else self.settings["font_family"]
        try:
            size = int(size)
        except (TypeError, ValueError):
            size = 10
        return (fam, size, "bold" if bold else "normal")

    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("classic")
        except tk.TclError:
            pass

        bg = self._base_bg()
        panel = self._panel_bg()
        fg = self._text_fg()
        muted = self._muted_fg()
        btn_bg = self.settings["color_button_bg"]
        btn_fg = self.settings["color_button_fg"]
        btn_act = self.settings["color_button_active"]
        detail_bg = self.settings["color_detail_bg"]

        self.root.configure(bg=bg)
        
        # Kill Combobox white dropdown listboxes natively
        self.root.option_add('*TCombobox*Listbox.background', detail_bg)
        self.root.option_add('*TCombobox*Listbox.foreground', fg)
        self.root.option_add('*TCombobox*Listbox.selectBackground', '#3c3c3c')
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')
        self.root.option_add('*TCombobox*Listbox.font', self._font(self.settings["font_body_size"]))

        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=bg, foreground=fg, font=self._font(self.settings["font_body_size"]))
        style.configure("Panel.TLabel", background=panel, foreground=fg, font=self._font(self.settings["font_body_size"]))
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("PanelMuted.TLabel", background=panel, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("Title.TLabel", background=bg, foreground=fg, font=self._font(self.settings["font_title_size"], True))
        style.configure("Small.TLabel", background=bg, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("Header.TLabel", background=bg, foreground=self.settings["color_header"], font=self._font(self.settings["font_body_size"], True))
        
        # Win95 Dark Buttons - single raised edge
        style.configure("TButton", font=self._font(self.settings["font_small_size"]), padding=(6, 2), background=btn_bg, foreground=btn_fg, borderwidth=2, relief="raised")
        style.map("TButton", background=[("active", btn_act), ("pressed", "#000000")], relief=[("pressed", "sunken")])
        
        style.configure("Compact.TButton", font=self._font(self.settings["font_small_size"]), padding=(5, 1))
        
        # Win95 Dark Combobox
        style.configure("TCombobox", selectbackground="#3c3c3c", fieldbackground=detail_bg, background=btn_bg, foreground=fg, arrowcolor=fg)
        style.map("TCombobox", fieldbackground=[("readonly", detail_bg)], selectbackground=[("readonly", "#3c3c3c")], selectforeground=[("readonly", "#ffffff")])
        
        style.configure("TLabelframe", background=panel, foreground=fg)
        style.configure("TLabelframe.Label", background=panel, foreground=fg)
        style.configure("TCheckbutton", background=panel, foreground=fg)
        style.map("TCheckbutton", background=[("active", panel)])

    @classmethod
    def _font_families(cls):
        if cls._FONT_FAMILIES_CACHE is not None:
            return cls._FONT_FAMILIES_CACHE
        try:
            fams = sorted(set(tkfont.families()))
            preferred = [
                "Verdana", "Segoe UI", "Arial", "Tahoma", "Calibri", 
                "Consolas", "Courier New", "Cascadia Mono", "JetBrains Mono",
            ]
            out = [f for f in preferred if f in fams] + [f for f in fams if f not in preferred]
        except Exception:
            out = ["Verdana", "Segoe UI", "Arial", "Tahoma", "Consolas", "Courier New"]
        cls._FONT_FAMILIES_CACHE = out
        return out

    def _build_ui(self):
        self.top = ttk.Frame(self.root)
        self.top.pack(fill="x", padx=10, pady=(8, 4))
        self.title_wrap = ttk.Frame(self.top)
        self.title_wrap.pack(side="left", fill="x", expand=True)

        self.title_lbl = ttk.Label(self.title_wrap, text="CalendarTask", style="Title.TLabel")
        self.title_lbl.pack(side="left")

        self.sub_lbl = ttk.Label(self.title_wrap, text="  focus, plan, ignore the noise", style="Small.TLabel")
        self.sub_lbl.pack(side="left", padx=(8, 0))

        self.clock_lbl = ttk.Label(self.top, text=" ", style="Header.TLabel")
        self.clock_lbl.pack(side="right", padx=(8, 0))

        self.btns = ttk.Frame(self.root)
        self.btns.pack(fill="x", padx=10, pady=(0, 6))

        self.nav_btns = ttk.Frame(self.btns)
        self.nav_btns.pack(side="left")
        self.btn_prev_year = ttk.Button(self.nav_btns, text="<< Year", style="Compact.TButton", command=self.prev_year)
        self.btn_prev_month = ttk.Button(self.nav_btns, text="< Month", style="Compact.TButton", command=self.prev_month)
        self.btn_today = ttk.Button(self.nav_btns, text="Today", style="Compact.TButton", command=self.go_today)
        self.btn_next_month = ttk.Button(self.nav_btns, text="Month >", style="Compact.TButton", command=self.next_month)
        self.btn_next_year = ttk.Button(self.nav_btns, text="Year >>", style="Compact.TButton", command=self.next_year)

        for w in [self.btn_prev_year, self.btn_prev_month, self.btn_today, self.btn_next_month, self.btn_next_year]:
            w.pack(side="left", padx=(0, 4))

        self.act_btns = ttk.Frame(self.btns)
        self.act_btns.pack(side="right")
        self.btn_add = ttk.Button(self.act_btns, text="Add", style="Compact.TButton", command=self.add_task)
        self.btn_edit = ttk.Button(self.act_btns, text="Edit", style="Compact.TButton", command=self.edit_task)
        self.btn_del = ttk.Button(self.act_btns, text="Del", style="Compact.TButton", command=self.delete_task)
        self.btn_focus = ttk.Button(self.act_btns, text="Focus (F)", style="Compact.TButton", command=self.toggle_focus)
        self.btn_settings = ttk.Button(self.act_btns, text="Settings", style="Compact.TButton", command=self.toggle_settings)
        self.btn_save = ttk.Button(self.act_btns, text="Save", style="Compact.TButton", command=self.save)
        
        import webbrowser
        self.btn_bmac = ttk.Button(self.act_btns, text="🤍 Support developer", style="Compact.TButton", command=lambda: webbrowser.open("https://buymeacoffee.com/vacuum34"))

        for w in [self.btn_add, self.btn_edit, self.btn_del, self.btn_focus, self.btn_settings, self.btn_save, self.btn_bmac]:
            w.pack(side="left", padx=(4, 0))

        self.main = ttk.Frame(self.root)
        self.main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.left = ttk.Frame(self.main)
        self.left.pack(side="left", fill="both", expand=True)

        self.right = ttk.Frame(self.main, style="Panel.TFrame", width=340)
        self.right.pack(side="right", fill="y", padx=(8, 0))
        self.right.pack_propagate(False)

        self.month_lbl = ttk.Label(self.left, text=" ", style="Title.TLabel")
        self.month_lbl.pack(anchor="w", pady=(0, 6))

        self.week_row = ttk.Frame(self.left)
        self.week_row.pack(fill="x", pady=(0, 4))

        self.grid_frame = ttk.Frame(self.left)
        self.grid_frame.pack(fill="both", expand=True)

        self.side_title = ttk.Label(self.right, text="Day details", style="Panel.TLabel")
        self.side_title.pack(anchor="w", padx=10, pady=(10, 2))

        self.side_date = ttk.Label(self.right, text=" ", style="PanelMuted.TLabel")
        self.side_date.pack(anchor="w", padx=10, pady=(0, 8))

        # View Mode Container
        self.view_frame = ttk.Frame(self.right, style="Panel.TFrame")
        self.view_frame.pack(fill="both", expand=True)

        self.task_list = tk.Listbox(
            self.view_frame,
            bg=self.settings["color_detail_bg"],
            fg=self.settings["color_detail_fg"],
            selectbackground="#3c3c3c",
            selectforeground="#ffffff",
            relief="sunken",
            borderwidth=1,
            highlightthickness=0,
            activestyle="none",
            font=self._font(self.settings["font_body_size"]),
        )
        self.task_list.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.task_list.bind("<Double-Button-1>", lambda e: self.toggle_done())
        # W2-005: keep the selection cache in sync with ordinary user-driven
        # row clicks. Without this, `_selected_task_idx` only catches up
        # when an action queries selection, leaving Edit/Delete/Space
        # vulnerable to a stale cache.
        self.task_list.bind("<<ListboxSelect>>", self._on_task_select)

        self.detail_lbl = tk.Text(
            self.view_frame,
            height=8,
            wrap="word",
            bg=self.settings["color_detail_bg"],
            fg=self.settings["color_detail_fg"],
            relief="sunken",
            borderwidth=1,
            highlightthickness=0,
            font=self._font(self.settings["font_small_size"], mono=True),
        )
        self.detail_lbl.pack(fill="x", padx=10, pady=(0, 10))
        self.detail_lbl.configure(state="disabled")

        # Edit Mode Container
        self.edit_frame = ttk.Frame(self.right, style="Panel.TFrame")
        
        detail_bg = self.settings["color_detail_bg"]
        fg = self.settings["color_detail_fg"]
        
        ttk.Label(self.edit_frame, text="Title:", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(10, 5), pady=4)
        self.edit_title = tk.Entry(self.edit_frame, bg=detail_bg, fg=fg, insertbackground=fg, relief="sunken", bd=1)
        self.edit_title.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=4)

        ttk.Label(self.edit_frame, text="Time:", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=(10, 5), pady=4)
        self.edit_time = tk.Entry(self.edit_frame, bg=detail_bg, fg=fg, insertbackground=fg, relief="sunken", bd=1)
        self.edit_time.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=4)

        ttk.Label(self.edit_frame, text="Kind:", style="Panel.TLabel").grid(row=2, column=0, sticky="w", padx=(10, 5), pady=4)
        self.edit_kind = ttk.Combobox(self.edit_frame, values=["task", "event", "reminder"], state="readonly")
        self.edit_kind.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=4)

        ttk.Label(self.edit_frame, text="Pri:", style="Panel.TLabel").grid(row=3, column=0, sticky="w", padx=(10, 5), pady=4)
        self.edit_priority = ttk.Combobox(self.edit_frame, values=["low", "normal", "high"], state="readonly")
        self.edit_priority.grid(row=3, column=1, sticky="ew", padx=(0, 10), pady=4)

        ttk.Label(self.edit_frame, text="Note:", style="Panel.TLabel").grid(row=4, column=0, sticky="nw", padx=(10, 5), pady=4)
        self.edit_note = tk.Text(self.edit_frame, height=5, bg=detail_bg, fg=fg, insertbackground=fg, relief="sunken", bd=1)
        self.edit_note.grid(row=4, column=1, sticky="ew", padx=(0, 10), pady=4)

        self.edit_btns = ttk.Frame(self.edit_frame, style="Panel.TFrame")
        self.edit_btns.grid(row=5, column=0, columnspan=2, pady=(15, 0), padx=10, sticky="e")
        ttk.Button(self.edit_btns, text="Save (Enter)", style="Compact.TButton", command=self.commit_task).pack(side="left", padx=(0, 5))
        ttk.Button(self.edit_btns, text="Cancel (Esc)", style="Compact.TButton", command=self.cancel_task).pack(side="left")

        self.edit_frame.columnconfigure(1, weight=1)

        self.help_lbl = ttk.Label(
            self.root,
            text="Esc exit/cancel | F focus | A add | E edit | D del | Space toggle done | Arrows navigate",
            style="Small.TLabel",
        )
        self.help_lbl.pack(fill="x", padx=10, pady=(0, 6))

        self.settings_panel = ttk.Frame(self.root, style="Panel.TFrame")
        self.settings_panel.place_forget()
        # PERF-005: the panel contents are built lazily on first open; see
        # _ensure_settings_built / toggle_settings.

    def _ensure_settings_built(self):
        if hasattr(self, "settings_canvas"):
            return
        self._build_settings_panel()

    def _build_settings_panel(self):
        self.settings_canvas = tk.Canvas(self.settings_panel, bg=self._panel_bg(), highlightthickness=0)
        self.settings_scroll = ttk.Scrollbar(self.settings_panel, orient="vertical", command=self.settings_canvas.yview)
        self.settings_inner = ttk.Frame(self.settings_canvas, style="Panel.TFrame")
        self.settings_inner.bind(
            "<Configure>",
            lambda e: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all")),
        )
        self.settings_canvas.create_window((0, 0), window=self.settings_inner, anchor="nw")
        self.settings_canvas.configure(yscrollcommand=self.settings_scroll.set)

        self.settings_canvas.pack(side="left", fill="both", expand=True)
        self.settings_scroll.pack(side="right", fill="y")

        inner = self.settings_inner

        ttk.Label(inner, text="Quick settings", style="Panel.TLabel").grid(
            row=0, column=0, sticky="w", columnspan=3, pady=(0, 10)
        )

        self.var_fullscreen = tk.BooleanVar()
        self.var_topmost = tk.BooleanVar()
        self.var_week_monday = tk.BooleanVar()
        self.var_weeknums = tk.BooleanVar() 
        self.var_clock = tk.BooleanVar()
        self.var_focus = tk.BooleanVar()
        self.var_gap = tk.StringVar()
        self.var_pad = tk.StringVar()
        self.var_font_family = tk.StringVar()
        self.var_font_mono = tk.StringVar()
        self.var_title_size = tk.StringVar()
        self.var_body_size = tk.StringVar()
        self.var_small_size = tk.StringVar()
        self.var_day_size = tk.StringVar()
        self.var_day_bold = tk.BooleanVar()

        row = 1
        for text, var in [
            ("Fullscreen on start", self.var_fullscreen),
            ("Always on top", self.var_topmost),
            ("Week starts Monday", self.var_week_monday),
            ("Show week numbers", self.var_weeknums),
            ("Show clock", self.var_clock),
        ]:
            ttk.Checkbutton(inner, text=text, variable=var).grid(
                row=row, column=0, sticky="w", pady=3, columnspan=2
            )
            row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        row += 1

        self._add_spin(inner, row, "Cell gap", self.var_gap, 0, 12)
        row += 1
        self._add_spin(inner, row, "Cell padding", self.var_pad, 0, 20)
        row += 1
        self._add_font(inner, row, "Font family", self.var_font_family, self._font_families(), width=22)
        row += 1
        self._add_font(inner, row, "Mono font", self.var_font_mono, self._font_families(), width=22)
        row += 1
        self._add_spin(inner, row, "Title size", self.var_title_size, 10, 28)
        row += 1
        self._add_spin(inner, row, "Body size", self.var_body_size, 8, 20)
        row += 1
        self._add_spin(inner, row, "Small size", self.var_small_size, 7, 16)
        row += 1
        self._add_spin(inner, row, "Day size", self.var_day_size, 8, 20)
        row += 1
        ttk.Checkbutton(inner, text="Bold day numbers", variable=self.var_day_bold).grid(
            row=row, column=0, sticky="w", pady=3, columnspan=2
        )
        row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        row += 1

        color_rows = [
            ("App bg", "color_app_bg"),
            ("Panel bg", "color_panel_bg"),
            ("Text", "color_text"),
            ("Muted text", "color_muted"),
            ("Header", "color_header"),
            ("Button bg", "color_button_bg"),
            ("Button fg", "color_button_fg"),
            ("Button active", "color_button_active"),
            ("Weekend bg", "color_weekend_bg"),
            ("Today border", "color_today_border"),
            ("Selected border", "color_selected_border"),
            ("Task dot", "color_task_dot"),
            ("Today text", "color_today_text"),
            ("Detail bg", "color_detail_bg"),
            ("Detail fg", "color_detail_fg"),
        ]

        self.color_previews = {}
        for label, key in color_rows:
            ttk.Label(inner, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=2)
            preview = tk.Label(inner, text="    ", bg=self.settings[key], relief="sunken", bd=1, width=8)
            preview.grid(row=row, column=1, sticky="w", padx=(10, 6))
            ttk.Button(
                inner,
                text="Pick",
                style="Compact.TButton",
                command=lambda k=key: self.pick_color(k),
            ).grid(row=row, column=2, sticky="e")
            self.color_previews[key] = preview
            row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        row += 1

        ttk.Button(inner, text="Apply", style="Compact.TButton", command=self.apply_settings).grid(
            row=row, column=0, sticky="w"
        )
        ttk.Button(inner, text="Default", style="Compact.TButton", command=self.reset_settings).grid(
            row=row, column=1, sticky="e"
        )

    def _add_spin(self, parent, row, label, variable, minv, maxv):
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Spinbox(parent, from_=minv, to=maxv, textvariable=variable, width=8).grid(
            row=row, column=1, sticky="w", padx=(10, 0)
        )

    def _add_font(self, parent, row, label, variable, values, width=22):
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Combobox(parent, textvariable=variable, values=values, width=width, state="readonly").grid(
            row=row, column=1, sticky="w", padx=(10, 0)
        )

    def _is_editing_focused(self):
        """Check if focus is in an editable widget that needs normal key handling."""
        try:
            w = self.root.focus_get()
            if w is None:
                return False
            return isinstance(w, (tk.Entry, tk.Text, ttk.Spinbox, ttk.Combobox))
        except (tk.TclError, RuntimeError):
            return False

    def _bind_keys(self):
        def _blocked():
            # W2-002: suppress app shortcuts while Settings owns the keyboard
            return self._is_editing_focused() or self.show_settings_panel
        self.root.bind("<Escape>", self.handle_escape)
        self.root.bind("<Left>", lambda e: None if _blocked() else self.prev_month())
        self.root.bind("<Right>", lambda e: None if _blocked() else self.next_month())
        self.root.bind("<Up>", lambda e: None if _blocked() else self.prev_year())
        self.root.bind("<Down>", lambda e: None if _blocked() else self.next_year())
        self.root.bind("f", lambda e: None if _blocked() else self.toggle_focus())
        self.root.bind("a", lambda e: None if _blocked() else self.add_task())
        self.root.bind("e", lambda e: None if _blocked() else self.edit_task())
        self.root.bind("d", lambda e: None if _blocked() else self.delete_task())
        self.root.bind("s", lambda e: None if _blocked() else self.save())
        self.root.bind("<space>", lambda e: None if _blocked() else self.toggle_done())
        self.root.bind("<Return>", self.handle_return)
        self.root.bind("<Control-k>", lambda e: self.toggle_settings())
        self.root.bind("<MouseWheel>", self._scroll_settings)
        self.root.bind("<Button-4>", self._scroll_settings_linux)
        self.root.bind("<Button-5>", self._scroll_settings_linux)
        # PERF-001: no root <Configure> binding. Settings panel is pinned
        # to the right edge through place geometry itself, so descendant
        # geometry events no longer fan out into Python reposition
        # callbacks.

    def handle_escape(self, event=None):
        if self.show_settings_panel:
            self.toggle_settings()
        elif self.is_editing:
            self.cancel_task()
        else:
            self.exit_app()

    def handle_return(self, event=None):
        if self.is_editing:
            self.commit_task()
        elif self.show_settings_panel:
            return
        else:
            self.open_selected_day()

    def _scroll_settings(self, event):
        if self.show_settings_panel and hasattr(event, "delta") and event.delta:
            self.settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _scroll_settings_linux(self, event):
        if not self.show_settings_panel:
            return
        if getattr(event, "num", None) == 4:
            self.settings_canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.settings_canvas.yview_scroll(1, "units")

    def _task_key(self, day_num=None):
        if day_num is None:
            day_num = self.selected_day
        try:
            day_num = int(day_num)
        except (TypeError, ValueError):
            day_num = self.selected_day
        return f"{self.current.year:04d}-{self.current.month:02d}-{day_num:02d}"

    def _month_name(self, y, m):
        try:
            return calendar.month_name[int(m)]
        except Exception:
            return str(m)

    def _weekday_labels(self):
        if self.settings["week_start_monday"]:
            return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    def _cal(self):
        return calendar.Calendar(firstweekday=0 if self.settings["week_start_monday"] else 6)

    def _refresh_all(self):
        self.root.configure(bg=self._base_bg())
        self._render_header()
        self._render_calendar()
        if not self.is_editing:
            self._render_side()
        # W2-008: Only sync settings vars when panel is freshly opened/reset
        self._apply_detail_theme()
        if self.show_settings_panel:
            self._show_settings_panel()
        else:
            self.settings_panel.place_forget()

    def _apply_detail_theme(self):
        # CORE-011: keep plain tk widgets in sync with the active settings,
        # not just at construction time.
        detail_bg = self.settings["color_detail_bg"]
        fg = self.settings["color_detail_fg"]
        self.task_list.configure(bg=detail_bg, fg=fg, font=self._font(self.settings["font_body_size"]))
        self.detail_lbl.configure(bg=detail_bg, fg=fg, font=self._font(self.settings["font_small_size"], mono=True))
        for w in (self.edit_title, self.edit_time, self.edit_note):
            w.configure(bg=detail_bg, fg=fg, insertbackground=fg, font=self._font(self.settings["font_body_size"]))
        try:
            self.settings_canvas.configure(bg=self._panel_bg())
        except (AttributeError, tk.TclError):
            pass

    def _render_header(self):
        self.month_lbl.configure(text=f"{self._month_name(self.current.year, self.current.month)} {self.current.year}")
        self.month_lbl.configure(font=self._font(self.settings["font_title_size"], True))
        self.sub_lbl.configure(font=self._font(self.settings["font_small_size"]))
        self.clock_lbl.configure(font=self._font(self.settings["font_body_size"], True), foreground=self.settings["color_header"])

    def _bind_day_widget(self, widget, day_num):
        widget.bind("<Button-1>", lambda e, d=day_num: self.select_day(d))

    def _ensure_calendar_pool(self):
        """PERF-002: build the calendar presentation once.

        Preallocates the 7 weekday-header labels, up to 6 ISO week-number
        labels, and a 6-row x 7-column pool of day-cell stacks. Month
        navigation re-grids/reconfigures these widgets instead of
        destroying and recreating them. Empty (out-of-month) slots hide
        their cell and show a plain filler frame. Click bindings are
        installed exactly once and resolve the current day from the slot's
        mutable metadata, so no stale day number can survive navigation.
        """
        if getattr(self, "_calendar_pool", None):
            return
        pool = {"weekdays": [], "weeknums": [], "slots": []}
        for _ in range(7):
            lbl = ttk.Label(self.week_row, text=" ", style="Header.TLabel", anchor="center")
            pool["weekdays"].append(lbl)
        for _ in range(6):
            wn = tk.Label(
                self.grid_frame,
                text="",
                bg=self._base_bg(),
                fg=self._muted_fg(),
                font=self._font(self.settings["font_small_size"]),
            )
            pool["weeknums"].append(wn)
        for r in range(6):
            row = []
            for c in range(7):
                wrap = tk.Frame(self.grid_frame, bg=self._base_bg())
                empty = tk.Frame(wrap, bg=self._base_bg(), highlightthickness=0)
                cell = tk.Frame(wrap)
                inner = tk.Frame(cell)
                top = tk.Frame(inner)
                num = tk.Label(top)
                slot = {
                    "wrap": wrap, "empty": empty, "cell": cell,
                    "inner": inner, "top": top, "num": num,
                    "badge": None, "dots": None, "day_num": None,
                    "row": r, "col": c,
                }
                self._bind_day_widget(cell, slot)
                self._bind_day_widget(inner, slot)
                self._bind_day_widget(top, slot)
                self._bind_day_widget(num, slot)
                row.append(slot)
            pool["slots"].append(row)
        self._calendar_pool = pool

    def _bind_day_widget(self, widget, slot):
        # PERF-002: single binding resolving the day from slot metadata.
        widget.bind("<Button-1>", lambda e: self.select_day(slot["day_num"]) if slot["day_num"] else None)

    def _slot_for_day(self, day_num):
        """PERF-002: return the pool slot whose current day matches day_num."""
        pool = getattr(self, "_calendar_pool", None)
        if not pool:
            return None
        for row in pool["slots"]:
            for slot in row:
                if slot["day_num"] == day_num:
                    return slot
        return None

    def _render_calendar(self):
        self._day_widgets = {}  # PERF-002: Track per-day widgets for targeted updates
        self._ensure_calendar_pool()
        pool = self._calendar_pool
        # CORE-010 / W2-008: reset ALL grid config each full render so stale
        # columns/rows never survive navigation or week-number toggles.
        for c in range(8):
            self.grid_frame.grid_columnconfigure(c, weight=0, minsize=0)
            self.week_row.grid_columnconfigure(c, weight=0, minsize=0)
        for r in range(6):
            self.grid_frame.grid_rowconfigure(r, weight=0)

        show_wn = self.settings["show_week_numbers"]
        col_offset = 1 if show_wn else 0
        labels = self._weekday_labels()
        if show_wn:
            spacer = pool["weekdays"][0]
            spacer.configure(text=" ")
            spacer.grid(row=0, column=0, sticky="ew", padx=1)
            self.week_row.grid_columnconfigure(0, weight=0, minsize=26)
        for i, text in enumerate(labels):
            col = i + col_offset
            lbl = pool["weekdays"][i]
            lbl.configure(text=text)
            lbl.grid(row=0, column=col, sticky="ew", padx=1)
            self.week_row.grid_columnconfigure(col, weight=1)
        for i in range(len(labels), 7):
            pool["weekdays"][i].grid_forget()

        weeks = self._cal().monthdayscalendar(self.current.year, self.current.month)
        today = date.today()
        gap = int(self.settings["cell_gap"])
        pad = int(self.settings["cell_padding"])
        weekend_bg = self.settings["color_weekend_bg"]
        today_border = self.settings["color_today_border"]
        selected_border = self.settings["color_selected_border"]
        task_dot = self.settings["color_task_dot"]
        today_text = self.settings["color_today_text"]
        cell_font = self._font(self.settings["font_day_size"], self.settings["font_day_bold"])

        # W2-009: derive a representative in-month day number per row without
        # constructing out-of-range spillover dates at datetime boundaries.
        fw = 0 if self.settings["week_start_monday"] else 6
        first_wd = calendar.monthrange(self.current.year, self.current.month)[0]
        offset = first_wd if fw == 0 else (first_wd + 1) % 7
        dim = calendar.monthrange(self.current.year, self.current.month)[1]

        num_rows = len(weeks)
        # Hide any pool row not used this month (4/5/6-row months).
        for r in range(num_rows, 6):
            wn = pool["weeknums"][r]
            wn.grid_forget()
            for c in range(7):
                slot = pool["slots"][r][c]
                slot["wrap"].grid_forget()

        for r, week in enumerate(weeks):
            if show_wn:
                base = 1 - offset + r * 7
                rep_c = 0
                for c in range(7):
                    dn = base + c
                    if 1 <= dn <= dim:
                        rep_c = c
                        break
                weeknum = date(self.current.year, self.current.month, base + rep_c).isocalendar()[1]
                wn = pool["weeknums"][r]
                wn.configure(text=str(weeknum))
                wn.grid(row=r, column=0, sticky="nswe", padx=(0, gap), pady=gap)
                self.grid_frame.grid_columnconfigure(0, weight=0, minsize=26)
            else:
                pool["weeknums"][r].grid_forget()

            for c, day_num in enumerate(week):
                col = c + col_offset
                self.grid_frame.grid_columnconfigure(col, weight=1)
                self.grid_frame.grid_rowconfigure(r, weight=1)

                slot = pool["slots"][r][c]
                wrap = slot["wrap"]
                wrap.configure(bg=self._base_bg())
                wrap.grid(row=r, column=col, sticky="nsew", padx=gap, pady=gap)

                # Reset the slot to a fresh state.
                slot["day_num"] = day_num
                slot["badge"] = None
                slot["dots"] = None
                try:
                    slot["cell"].pack_forget()
                    slot["empty"].pack_forget()
                except tk.TclError:
                    pass

                if day_num == 0:
                    slot["empty"].pack(fill="both", expand=True)
                    continue

                is_today = day_num == today.day and self.current.month == today.month and self.current.year == today.year
                is_selected = day_num == self.selected_day
                is_weekend = (c >= 5) if self.settings["week_start_monday"] else (c == 0 or c == 6)

                bg = weekend_bg if is_weekend else self.settings["color_panel_bg"]
                border = selected_border if is_selected else (today_border if is_today else "#2a2a2a")

                cell = slot["cell"]
                cell.configure(bg=bg, highlightbackground=border, highlightcolor=border, highlightthickness=2 if is_selected or is_today else 1)
                cell.pack(fill="both", expand=True)

                inner = slot["inner"]
                inner.configure(bg=bg)
                inner.pack(fill="both", expand=True, padx=pad, pady=pad)

                top = slot["top"]
                top.configure(bg=bg)
                top.pack(fill="x")

                num = slot["num"]
                num.configure(
                    text=str(day_num),
                    bg=bg,
                    fg=today_text if is_today else self._text_fg(),
                    font=cell_font,
                )
                num.pack(side="left")

                task_count = len(self.tasks.get(self._task_key(day_num), []))
                if task_count:
                    badge = slot["badge"]
                    if badge is None:
                        badge = tk.Label(top, text="", bg=bg, fg=task_dot, font=self._font(self.settings["font_small_size"], True))
                        badge.pack(side="right")
                        self._bind_day_widget(badge, slot)
                        slot["badge"] = badge
                    badge.configure(text=f"{task_count}", bg=bg, fg=task_dot, font=self._font(self.settings["font_small_size"], True))
                    badge.pack(side="right")

                    dots = slot["dots"]
                    if dots is None:
                        dots = tk.Label(inner, text="", bg=bg, fg=task_dot, font=self._font(self.settings["font_small_size"]))
                        dots.pack(anchor="w", pady=(4, 0))
                        self._bind_day_widget(dots, slot)
                        slot["dots"] = dots
                    dots.configure(text="● " * min(task_count, 4), bg=bg, fg=task_dot, font=self._font(self.settings["font_small_size"]))
                    dots.pack(anchor="w", pady=(4, 0))

                self._day_widgets[day_num] = {
                    "cell": cell, "inner": inner, "top": top, "num": num,
                    "badge": slot["badge"], "dots": slot["dots"],
                    "bg": bg, "border": border, "is_today": is_today,
                    "is_weekend": is_weekend,
                }

    def _update_day_visuals(self, day_num):
        """Update the visual state of a single day cell.

        Reconciles selection/today borders, the day-number foreground and the
        task-count badge/dots so the derived indicators always match self.tasks
        (CORE-005, CORE-013) without rebuilding the whole grid.
        """
        info = self._day_widgets.get(day_num)
        if not info:
            return
        today = date.today()
        is_today = day_num == today.day and self.current.month == today.month and self.current.year == today.year
        is_selected = day_num == self.selected_day
        is_weekend = info["is_weekend"]
        weekend_bg = self.settings["color_weekend_bg"]
        today_border = self.settings["color_today_border"]
        selected_border = self.settings["color_selected_border"]
        today_text = self.settings["color_today_text"]
        bg = weekend_bg if is_weekend else self.settings["color_panel_bg"]
        border = selected_border if is_selected else (today_border if is_today else "#2a2a2a")
        info["is_today"] = is_today
        info["cell"].configure(bg=bg, highlightbackground=border, highlightcolor=border,
                               highlightthickness=2 if is_selected or is_today else 1)
        for w in [info["inner"], info["top"]]:
            try: w.configure(bg=bg)
            except tk.TclError: pass
        try:
            info["num"].configure(bg=bg, fg=today_text if is_today else self._text_fg())
        except tk.TclError:
            pass

        task_count = len(self.tasks.get(self._task_key(day_num), []))
        task_dot = self.settings["color_task_dot"]
        small_bold = self._font(self.settings["font_small_size"], True)
        small = self._font(self.settings["font_small_size"])
        badge = info.get("badge")
        dots = info.get("dots")
        slot = self._slot_for_day(day_num)
        if task_count:
            if badge is None:
                badge = tk.Label(info["top"], text="", bg=bg, fg=task_dot, font=small_bold)
                badge.pack(side="right")
                if slot is not None:
                    self._bind_day_widget(badge, slot)
                info["badge"] = badge
            badge.configure(text=f"{task_count}", bg=bg, fg=task_dot, font=small_bold)
            if dots is None:
                dots = tk.Label(info["inner"], text="", bg=bg, fg=task_dot, font=small)
                dots.pack(anchor="w", pady=(4, 0))
                if slot is not None:
                    self._bind_day_widget(dots, slot)
                info["dots"] = dots
            dots.configure(text="● " * min(task_count, 4), bg=bg, fg=task_dot, font=small)
        else:
            if badge is not None:
                badge.destroy()
                info["badge"] = None
            if dots is not None:
                dots.destroy()
                info["dots"] = None

    def _render_side(self):
        try:
            dt = date(self.current.year, self.current.month, self.selected_day)
            self.side_date.config(text=dt.strftime("%A, %d %B %Y"))
        except ValueError:
            self.side_date.config(text=self._task_key())
        key = self._task_key()
        items = self.tasks.get(key, [])
        rows = []
        for task in items:
            mark = "✓" if task.done else "•"
            priority = "!" if task.priority == "high" else " "
            time_text = f"{task.time} " if task.time else " "
            rows.append(f"{mark} {time_text}{priority}{task.title}")
        self.task_list.delete(0, "end")
        if rows:
            self.task_list.insert("end", *rows)  # PERF-003: one variadic insert
        # W2-005: only restore the selection when the cached index belongs
        # to THIS day; never migrate a stale index from another day's list.
        if (
            items
            and self._selected_task_idx is not None
            and 0 <= self._selected_task_idx < len(items)
            and self._selection_owner_key == key
        ):
            self.task_list.selection_set(self._selected_task_idx)
            self.task_list.activate(self._selected_task_idx)
        elif not items:
            self._selected_task_idx = None
            self._selection_owner_key = None
        self._selection_owner_key = None
        self._invalid_task_keys = []

        self._update_detail_box()

    def _update_detail_box(self):
        key = self._task_key()
        items = self.tasks.get(key, [])
        self.detail_lbl.configure(state="normal")
        self.detail_lbl.delete("1.0", "end")
        if not items:
            self.detail_lbl.insert("end", "No tasks.\n\nA add\nE edit\nD delete\nSpace done")
        else:
            # PERF-004: build the full text in a buffer, then insert once.
            # Converts ~5 Tcl/Tk crossings per task into one.
            lines = []
            for idx, task in enumerate(items, 1):
                lines.append(f"{idx}. {task.title}")
                lines.append(f"   kind: {task.kind} | priority: {task.priority} | done: {task.done}")
                if task.time:
                    lines.append(f"   time: {task.time}")
                if task.note:
                    lines.append(f"   note: {task.note}")
                lines.append("")
            self.detail_lbl.insert("end", "\n".join(lines))
        self.detail_lbl.configure(state="disabled")

    def select_day(self, day_num):
        # W2-002: refuse day change while an editor draft is active; Esc is
        # the explicit discard path. Cancellation would otherwise silently
        # drop the user's typed title/time/note.
        if self.is_editing:
            return
        try:
            day_num = int(day_num)
        except (TypeError, ValueError):
            return
        max_day = calendar.monthrange(self.current.year, self.current.month)[1]
        day_num = max(1, min(day_num, max_day))
        if day_num == self.selected_day:
            return
        old_day = self.selected_day
        self.selected_day = day_num
        # W2-005: the cache belongs to the previous day; clear it before
        # the new day's listbox is rendered so stale indexes cannot
        # migrate.
        self._reset_selection_cache()
        # PERF-002: Update only affected day visuals + side panel instead of full rebuild
        self._update_day_visuals(old_day)
        self._update_day_visuals(day_num)
        if not self.is_editing:
            self._render_side()
        self._apply_detail_theme()

    def open_selected_day(self):
        if not self.is_editing:
            self._update_detail_box()

    def _show_edit_mode(self, idx=None):
        self.is_editing = True
        self.editing_idx = idx
        self.view_frame.pack_forget()
        self.edit_frame.pack(fill="both", expand=True)
        
        self.edit_title.delete(0, "end")
        self.edit_time.delete(0, "end")
        self.edit_note.delete("1.0", "end")
        self.edit_kind.set("task")
        self.edit_priority.set("normal")

        if idx is not None:
            key = self._task_key()
            task = self.tasks[key][idx]
            self.edit_title.insert(0, task.title)
            self.edit_time.insert(0, task.time)
            self.edit_note.insert("1.0", task.note)
            self.edit_kind.set(task.kind)
            self.edit_priority.set(task.priority)
            self.side_title.config(text="Edit Task")
        else:
            self.side_title.config(text="Add Task")
            
        self.edit_title.focus_set()

    def add_task(self):
        if self.settings.get("focus_mode", False) or self.is_editing:
            return
        self._show_edit_mode(None)

    def edit_task(self):
        if self.settings.get("focus_mode", False) or self.is_editing:
            return
        idx = self._selected_index()
        if idx is None:
            return
        self._show_edit_mode(idx)

    def commit_task(self):
        title = self.edit_title.get().strip()
        if not title:
            self.cancel_task()
            return

        time_str = self.edit_time.get().strip()
        note = self.edit_note.get("1.0", "end-1c").strip()
        kind = self.edit_kind.get().strip().lower() or "task"
        priority = self.edit_priority.get().strip().lower() or "normal"

        task = CalendarTask(title=title, time=time_str, note=note, kind=kind, priority=priority)

        key = self._task_key()
        # CORE-003: capture pre-mutation state so a failed save can roll back
        # the in-memory change rather than present a successful edit that
        # never reached disk.
        if self.editing_idx is not None:
            prev = self.tasks[key][self.editing_idx]
            self.tasks[key][self.editing_idx] = task
            rollback = lambda: self.tasks[key].__setitem__(self.editing_idx, prev)
        else:
            self.tasks.setdefault(key, []).append(task)
            rollback = lambda: self.tasks[key].pop()

        if not self.save():
            rollback()
            try:
                messagebox.showerror(
                    "Save failed",
                    "Could not write data to disk; the change was rolled back.",
                    parent=self.root,
                )
            except tk.TclError:
                pass
            return
        self.cancel_task()
        # PERF-002: Update only the affected day badge + side panel
        self._update_day_visuals(self.selected_day)
        self._render_side()

    def cancel_task(self):
        self.is_editing = False
        self.editing_idx = None
        self.edit_frame.pack_forget()
        self.view_frame.pack(fill="both", expand=True)
        self.side_title.config(text="Day details")
        self.root.focus_set()

    def _selected_index(self):
        items = self.tasks.get(self._task_key(), [])
        # W2-005: the cache is scoped to the current day key; a stale
        # index from another day is never returned.
        if self._selection_owner_key != self._task_key():
            self._selected_task_idx = None
        try:
            sel = self.task_list.curselection()
        except tk.TclError:
            sel = ()
        if sel:
            idx = int(sel[0])
            if 0 <= idx < len(items):
                self._selected_task_idx = idx
                self._selection_owner_key = self._task_key()
                return idx
        if self._selected_task_idx is not None and 0 <= self._selected_task_idx < len(items) \
                and self._selection_owner_key == self._task_key():
            return self._selected_task_idx
        if items:
            # No explicit selection: visibly select the intended default row
            # rather than silently targeting row 0 from an invisible state.
            self._selected_task_idx = 0
            self._selection_owner_key = self._task_key()
            try:
                self.task_list.selection_set(0)
                self.task_list.activate(0)
            except tk.TclError:
                pass
            return 0
        return None

    def _on_task_select(self, event=None):
        """W2-005: sync the selection cache from the Listbox virtual event."""
        try:
            sel = self.task_list.curselection()
        except tk.TclError:
            return
        if sel:
            idx = int(sel[0])
            self._selected_task_idx = idx
            self._selection_owner_key = self._task_key()

    def _reset_selection_cache(self):
        """W2-005: invalidate the selection cache when the day/month changes."""
        self._selected_task_idx = None
        self._selection_owner_key = None

    def delete_task(self):
        if self.is_editing:
            return
        key = self._task_key()
        items = self.tasks.get(key, [])
        idx = self._selected_index()
        if idx is None or idx >= len(items):
            return
        # CORE-003: capture the removed task so a save failure can restore it.
        removed = items[idx]
        del items[idx]
        if not items:
            self.tasks.pop(key, None)
        if self._selected_task_idx == idx:
            self._selected_task_idx = min(idx, len(items) - 1) if items else None
        elif self._selected_task_idx is not None and self._selected_task_idx > idx:
            self._selected_task_idx -= 1
        if not self.save():
            # Roll back the in-memory deletion.
            self.tasks.setdefault(key, []).insert(idx, removed)
            try:
                messagebox.showerror(
                    "Save failed",
                    "Could not write data to disk; the deletion was rolled back.",
                    parent=self.root,
                )
            except tk.TclError:
                pass
            return
        # PERF-002: Update only the affected day badge + side panel
        self._update_day_visuals(self.selected_day)
        self._render_side()

    def toggle_done(self):
        if self.is_editing:
            return
        key = self._task_key()
        items = self.tasks.get(key, [])
        idx = self._selected_index()
        if idx is None or idx >= len(items):
            return
        # CORE-003: flip with a guarded rollback on persistence failure.
        prev_done = items[idx].done
        items[idx].done = not prev_done
        if not self.save():
            items[idx].done = prev_done
            try:
                messagebox.showerror(
                    "Save failed",
                    "Could not write data to disk; the change was rolled back.",
                    parent=self.root,
                )
            except tk.TclError:
                pass
            return
        # PERF-002: Update only the affected day badge + side panel
        self._update_day_visuals(self.selected_day)
        self._render_side()

    def toggle_focus(self, event=None):
        # W2-002: refuse focus toggle while an editor draft is active.
        if self.is_editing:
            return
        prev = self.settings.get("focus_mode", False)
        new = not prev
        # CORE-003: stage the runtime visual first, then persist; on save
        # failure revert both the in-memory setting AND the live visual.
        self.settings["focus_mode"] = new
        self._apply_focus_visual(new)
        if not self.save():
            self.settings["focus_mode"] = prev
            self._apply_focus_visual(prev)
            try:
                messagebox.showerror(
                    "Save failed",
                    "Could not write data to disk; focus mode was rolled back.",
                    parent=self.root,
                )
            except tk.TclError:
                pass

    def _apply_focus_visual(self, active: bool):
        if active:
            self._pre_focus_fs = self.root.attributes("-fullscreen")
            self.top.pack_forget()
            self.btns.pack_forget()
            self.right.pack_forget()
            self.help_lbl.pack_forget()
            self.root.attributes("-fullscreen", True)
        else:
            self.top.pack(fill="x", padx=10, pady=(8, 4), before=self.main)
            self.btns.pack(fill="x", padx=10, pady=(0, 6), before=self.main)
            self.right.pack(side="right", fill="y", padx=(8, 0))
            self.help_lbl.pack(fill="x", padx=10, pady=(0, 6))
            self.root.attributes("-fullscreen", self._pre_focus_fs)

    def toggle_settings(self):
        self.show_settings_panel = not self.show_settings_panel
        if self.show_settings_panel:
            self._ensure_settings_built()  # PERF-005: build on first open
            self._sync_settings_vars()  # W2-008: sync draft only when opening
            self._show_settings_panel()
        else:
            self.settings_panel.place_forget()
            # W2-002: release the hidden focus Settings may have left behind
            try:
                self.root.focus_set()
            except tk.TclError:
                pass

    def _show_settings_panel(self):
        # PERF-001: pin the panel to the right edge with relx/x/anchor
        # geometry. Tk handles the resize math, so we never need a
        # <Configure> callback to reposition it.
        w = 460
        h = 560
        self.settings_panel.place(
            relx=1.0, x=-20, y=70, width=w, height=h, anchor="ne"
        )
        self.settings_panel.lift()

    def pick_color(self, key):
        try:
            color = colorchooser.askcolor(title=key, initialcolor=self.settings[key])
        except tk.TclError:
            color = None
        if color and color[1]:
            # W2-006: stage the color in the draft; only Apply commits it
            self._draft_colors[key] = color[1]
            preview = self.color_previews.get(key)
            if preview is not None:
                preview.configure(bg=color[1])

    def _sync_settings_vars(self):
        self._draft_colors = {}
        self.var_fullscreen.set(self.settings.get("fullscreen_start", True))
        self.var_topmost.set(self.settings.get("always_on_top", True))
        self.var_week_monday.set(self.settings.get("week_start_monday", True))
        self.var_weeknums.set(self.settings.get("show_week_numbers", False))
        self.var_clock.set(self.settings.get("show_clock", True))
        self.var_focus.set(self.settings.get("focus_mode", False))
        self.var_gap.set(self.settings.get("cell_gap", 1))
        self.var_pad.set(self.settings.get("cell_padding", 4))
        self.var_font_family.set(self.settings.get("font_family", "Verdana"))
        self.var_font_mono.set(self.settings.get("font_mono", "Courier New"))
        self.var_title_size.set(self.settings.get("font_title_size", 16))
        self.var_body_size.set(self.settings.get("font_body_size", 10))
        self.var_small_size.set(self.settings.get("font_small_size", 9))
        self.var_day_size.set(self.settings.get("font_day_size", 10))
        self.var_day_bold.set(self.settings.get("font_day_bold", True))
        for k, p in self.color_previews.items():
            try:
                p.configure(bg=self.settings.get(k, DEFAULT_SETTINGS[k]))
            except tk.TclError:
                pass

    def _sync_settings_vars_to_defaults(self):
        # CORE-005: point the Settings UI at DEFAULT_SETTINGS so the normal
        # apply_settings diff runs defaults against the current live settings.
        self._draft_colors = {}
        for var, key in [
            (self.var_fullscreen, "fullscreen_start"),
            (self.var_topmost, "always_on_top"),
            (self.var_week_monday, "week_start_monday"),
            (self.var_weeknums, "show_week_numbers"),
            (self.var_clock, "show_clock"),
            (self.var_focus, "focus_mode"),
        ]:
            try:
                var.set(DEFAULT_SETTINGS[key])
            except tk.TclError:
                pass
        for var, key in [
            (self.var_gap, "cell_gap"),
            (self.var_pad, "cell_padding"),
            (self.var_font_family, "font_family"),
            (self.var_font_mono, "font_mono"),
            (self.var_title_size, "font_title_size"),
            (self.var_body_size, "font_body_size"),
            (self.var_small_size, "font_small_size"),
            (self.var_day_size, "font_day_size"),
        ]:
            try:
                var.set(DEFAULT_SETTINGS[key])
            except tk.TclError:
                pass
        try:
            self.var_day_bold.set(DEFAULT_SETTINGS["font_day_bold"])
        except tk.TclError:
            pass
        for k, p in self.color_previews.items():
            try:
                p.configure(bg=DEFAULT_SETTINGS.get(k, DEFAULT_SETTINGS[k]))
            except tk.TclError:
                pass

    def apply_settings(self, silent=False):
        # W2-006: Validate all settings into a temporary candidate before committing
        candidate = self.settings.copy()
        raw = {
            "fullscreen_start": bool(self.var_fullscreen.get()),
            "always_on_top": bool(self.var_topmost.get()),
            "week_start_monday": bool(self.var_week_monday.get()),
            "show_week_numbers": bool(self.var_weeknums.get()),
            "show_clock": bool(self.var_clock.get()),
            "cell_gap": self.var_gap.get(),
            "cell_padding": self.var_pad.get(),
            "font_family": self.var_font_family.get(),
            "font_mono": self.var_font_mono.get(),
            "font_title_size": self.var_title_size.get(),
            "font_body_size": self.var_body_size.get(),
            "font_small_size": self.var_small_size.get(),
            "font_day_size": self.var_day_size.get(),
            "font_day_bold": bool(self.var_day_bold.get()),
        }
        # stage any picked colors into the same transaction
        for k, v in self._draft_colors.items():
            raw[k] = v
        validated = normalize_settings(raw)
        candidate.update(validated)
        # PERF-004: skip the entire pipeline when nothing actually changed
        changed = {k: v for k, v in candidate.items() if self.settings.get(k) != v}
        changed_keys = set(changed)  # W2-001: use the set for membership tests

        if not changed:
            self._draft_colors = {}
            return

        style_keys = (
            {"theme", "compact_header", "font_family", "font_mono",
             "font_title_size", "font_body_size", "font_small_size",
             "font_day_size", "font_day_bold"}
            | {k for k in candidate if k.startswith("color_")}
        )
        geom_keys = {"week_start_monday", "show_week_numbers", "cell_gap", "cell_padding"}
        need_style = bool(changed_keys & style_keys)
        need_geom = bool(changed_keys & geom_keys)

        # CORE-003: commit the candidate transaction only after persistence
        # succeeds. Apply the live visual/runtime side effects against the
        # candidate first, then persist; on save failure revert every piece.
        prev_settings = self.settings
        prev_focus_fs = self._pre_focus_fs
        self.settings = candidate
        try:
            if "always_on_top" in changed_keys:
                self.root.attributes("-topmost", candidate["always_on_top"])
            if "fullscreen_start" in changed_keys:
                # W2-006: while Focus is active, focus mode owns the live
                # fullscreen attribute. A fullscreen_start change updates
                # the deferred restore target so exiting Focus restores
                # the user's newly requested state, not the pre-focus
                # snapshot.
                if candidate.get("focus_mode", False):
                    self._pre_focus_fs = bool(candidate["fullscreen_start"])
                else:
                    self.root.attributes("-fullscreen", candidate["fullscreen_start"])
            if "show_clock" in changed_keys:
                self._start_clock()
            if need_style:
                self._build_style()
            if not self._save():
                # Persistence failed: revert runtime effects + in-memory state.
                self.settings = prev_settings
                if "always_on_top" in changed_keys:
                    self.root.attributes("-topmost", prev_settings.get("always_on_top", True))
                if "fullscreen_start" in changed_keys:
                    self._pre_focus_fs = prev_focus_fs
                    if not prev_settings.get("focus_mode", False):
                        self.root.attributes("-fullscreen", prev_settings.get("fullscreen_start", True))
                if need_style:
                    self._build_style()
                if need_geom or need_style:
                    self._refresh_all()
                try:
                    messagebox.showerror(
                        "Save failed",
                        "Could not write settings to disk; the change was rolled back.",
                        parent=self.root,
                    )
                except tk.TclError:
                    pass
                return
        finally:
            self._draft_colors = {}

        if need_geom or need_style:
            self._refresh_all()
        if not silent and self.show_settings_panel:
            self._show_settings_panel()

    def reset_settings(self):
        # CORE-005: do NOT preassign self.settings to defaults; that would
        # make the diff in apply_settings compare defaults against defaults
        # and skip the entire reset. Instead sync the UI vars to defaults and
        # let apply_settings run the normal change pipeline against the real
        # current settings.
        self._sync_settings_vars_to_defaults()
        self.apply_settings()

    def _nav_guard(self):
        """Refuse calendar-date mutation while an editor session is active."""
        return self.is_editing

    def prev_month(self):
        if self._nav_guard():
            return
        y, m = self.current.year, self.current.month
        if m == 1:
            if y <= date.min.year:
                return  # CORE-009: no-op at domain boundary
            y -= 1
            m = 12
        else:
            m -= 1
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._reset_selection_cache()  # W2-005
        self._refresh_all()

    def next_month(self):
        if self._nav_guard():
            return
        y, m = self.current.year, self.current.month
        if m == 12:
            if y >= date.max.year:
                return  # CORE-009: no-op at domain boundary
            y += 1
            m = 1
        else:
            m += 1
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._reset_selection_cache()  # W2-005
        self._refresh_all()

    def prev_year(self):
        if self._nav_guard():
            return
        y = self.current.year - 1
        if y < date.min.year: return
        m = self.current.month
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._reset_selection_cache()  # W2-005
        self._refresh_all()

    def next_year(self):
        if self._nav_guard():
            return
        y = self.current.year + 1
        if y > date.max.year: return
        m = self.current.month
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._reset_selection_cache()  # W2-005
        self._refresh_all()

    def go_today(self):
        if self._nav_guard():
            return
        t = date.today()
        self.current = date(t.year, t.month, 1)
        self.selected_day = t.day
        self._reset_selection_cache()  # W2-005
        self._refresh_all()

    def _start_clock(self):
        """(Re)start the single clock timer, canceling any pending one."""
        if self._clock_after_id is not None:
            try:
                self.root.after_cancel(self._clock_after_id)
            except tk.TclError:
                pass
            self._clock_after_id = None
        self._tick_clock()

    def _reconcile_today_rollover(self, old, new):
        if self.current.year == old.year and self.current.month == old.month:
            self._update_day_visuals(old.day)
        if self.current.year == new.year and self.current.month == new.month:
            self._update_day_visuals(new.day)

    def _tick_clock(self):
        if self._clock_after_id is not None:
            try:
                self.root.after_cancel(self._clock_after_id)
            except tk.TclError:
                pass
            self._clock_after_id = None
        show = self.settings.get("show_clock", True)
        now = datetime.now()
        if show:
            self.clock_lbl.config(text=now.strftime("%d %b %Y  %H:%M:%S"))
            delay_ms = 1000 - now.microsecond // 1000  # W2-010: advance every second
        else:
            self.clock_lbl.config(text="")
            delay_ms = 60_000
        today = date.today()
        if self._last_observed_date is not None and today != self._last_observed_date:
            self._reconcile_today_rollover(self._last_observed_date, today)
        self._last_observed_date = today
        self._clock_after_id = self.root.after(delay_ms, self._tick_clock)

    def save(self):
        # CORE-003: surface persistence success/failure to callers; mutations
        # MUST know whether their state actually hit disk.
        return self._save()

    def _read_disk_generation(self):
        """Return the generation stored on disk, or None if missing/empty.

        CORE-004: distinguish three states explicitly.
        - missing DATA_PATH: return None (caller may treat as fresh creation)
        - present but unreadable (OSError, UnicodeError, JSON error, wrong
          shape, non-int generation): raise UnreadableDataFile
        - generation parse fails: raise UnreadableDataFile
        The caller decides what to do with a present-but-unreadable file
        (quarantine it, refuse to overwrite, etc.) instead of silently
        treating it as generation-free.
        """
        if not DATA_PATH.exists():
            return None
        try:
            text = DATA_PATH.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise UnreadableDataFile(str(exc)) from exc
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise UnreadableDataFile(f"invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise UnreadableDataFile("top-level payload is not an object")
        try:
            return int(payload.get("generation", 0))
        except (TypeError, ValueError, OverflowError) as exc:
            raise UnreadableDataFile(f"invalid generation: {exc}") from exc

    def _save(self):
        """Persist state. Returns True on success, False on failure.

        Generation advances only after a successful atomic replacement. A
        stale writer (disk generation differs from the one we loaded) is
        refused so a concurrent/repeated instance cannot silently overwrite
        newer data. CORE-004: a present-but-unreadable file is first
        preserved via quarantine so a subsequent save never silently
        destroys damaged data. CORE-006: the entire read-check-write-replace
        sequence runs under an interprocess file lock so two writers cannot
        both pass the stale-writer guard before either replaces.
        """
        with _save_lock(DATA_PATH):
            return self._save_locked()

    def _save_locked(self):
        try:
            try:
                disk_gen = self._read_disk_generation()
            except UnreadableDataFile:
                if not self._quarantine_file():
                    return False
                disk_gen = None
            if disk_gen is not None and disk_gen != self._generation:
                return False
            next_gen = self._generation + 1
            payload = {
                "settings": self.settings,
                "tasks": {k: [t.to_dict() for t in v] for k, v in self.tasks.items()},
                "state": {
                    "year": self.current.year,
                    "month": self.current.month,
                    "selected_day": self.selected_day,
                },
                "generation": next_gen,
            }
            DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=str(DATA_PATH.parent), prefix=".cal_tmp_", suffix=".json"
            )
            try:
                # PERF-003: stream the encoded JSON straight into the temp
                # file instead of materializing a full string first. Same
                # payload, same indent/ordering semantics.
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                    f.flush()
                os.replace(tmp_path, str(DATA_PATH))
                self._generation = next_gen
                self._loaded_generation = next_gen
                return True
            except Exception:
                try: os.unlink(tmp_path)
                except OSError: pass
                return False
        except (OSError, TypeError, ValueError, OverflowError):
            return False

    def _quarantine_file(self):
        """Preserve a damaged/undecodable data file before any replacement."""
        if not DATA_PATH.exists():
            return True
        try:
            backup = DATA_PATH.with_name(DATA_PATH.name + ".corrupt.bak")
            import shutil
            shutil.copy2(str(DATA_PATH), str(backup))
            self._quarantine_path = backup
            return True
        except OSError:
            return False

    def _load(self):
        if not DATA_PATH.exists():
            return
        raw_text = None
        try:
            raw_text = DATA_PATH.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as e:
            # W2-003: non-UTF-8 bytes must enter the same recoverable failure flow
            self._load_failed = True
            if not self._quarantine_file():
                self._load_failed = False
            return
        payload = None
        try:
            payload = json.loads(raw_text)
        except (json.JSONDecodeError, ValueError):
            self._load_failed = True
            if not self._quarantine_file():
                self._load_failed = False
            return
        raw_text = None  # PERF-006: release the decoded source before materializing
        if not isinstance(payload, dict):
            self._load_failed = True
            if not self._quarantine_file():
                self._load_failed = False
            return
        # CORE-001 + CORE-002: Parse each section independently
        raw_settings = payload.get("settings", {})
        if isinstance(raw_settings, dict):
            new_settings = normalize_settings(raw_settings)
            if new_settings:
                for k, v in new_settings.items():
                    if k in DEFAULT_SETTINGS:
                        self.settings[k] = v
        raw_tasks = payload.get("tasks", {})
        if isinstance(raw_tasks, dict):
            loaded_tasks = {}
            quarantine_quarantine = []  # invalid keys preserved for forensics
            for k, v in raw_tasks.items():
                if not isinstance(k, str):
                    continue
                if not isinstance(v, list):
                    continue
                # W2-003: validate and canonicalize the task key. Shared with
                # _task_key so the load path and the runtime key contract
                # agree on what a real date looks like.
                canonical = _canonical_task_key(k)
                if canonical is None:
                    # Impossible / unrecoverable key. Preserve the bucket
                    # under its raw key so nothing is silently dropped.
                    quarantine_quarantine.append(k)
                    bucket_key = k
                else:
                    bucket_key = canonical
                existing = loaded_tasks.get(bucket_key, [])
                existing.extend(
                    CalendarTask.from_dict(x) for x in v if isinstance(x, dict)
                )
                loaded_tasks[bucket_key] = existing
            self.tasks = loaded_tasks
            if quarantine_quarantine:
                self._invalid_task_keys = quarantine_quarantine
            else:
                self._invalid_task_keys = []
        st = payload.get("state", {})
        if isinstance(st, dict):
            self._apply_state(st)
        gen = payload.get("generation", 0)
        try:
            self._generation = max(0, int(gen))
        except (TypeError, ValueError, OverflowError):
            self._generation = 0
        self._loaded_generation = self._generation

    def _apply_state(self, st):
        today = date.today()
        try:
            y = int(st.get("year", today.year))
            if _is_non_finite(st.get("year")):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            y = today.year
        try:
            m = int(st.get("month", today.month))
            if _is_non_finite(st.get("month")):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            m = today.month
        try:
            d = int(st.get("selected_day", today.day))
            if _is_non_finite(st.get("selected_day")):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            d = today.day
        if not (1 <= m <= 12):
            m = today.month
        if not (date.min.year <= y <= date.max.year):
            y = today.year
        try:
            max_day = calendar.monthrange(y, m)[1]
        except ValueError:
            y, m = today.year, today.month
            max_day = calendar.monthrange(y, m)[1]
        self.current = date(y, m, 1)
        self.selected_day = min(max(1, d), max_day)

    def exit_app(self, event=None):
        # W2-002: an active editor owns an uncommitted draft. WM_DELETE
        # and Esc-exit must let the user keep editing, commit, or
        # explicitly discard before destroying the root.
        if self.is_editing:
            choice = messagebox.askyesnocancel(
                "Discard edit?",
                "An unsaved task edit is in progress. Quit and discard it?",
                parent=self.root,
            )
            if choice is None or not choice:
                return
        if self._save():
            self.root.destroy()
        else:
            choice = messagebox.askyesnocancel(
                "Save failed",
                "Could not save data. Quit without saving?",
                parent=self.root,
            )
            if choice is None:
                return
            if choice:
                self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CompactCalendarApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()