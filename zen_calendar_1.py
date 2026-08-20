import calendar
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, font as tkfont, colorchooser

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
        return CalendarTask(
            title=str(d.get("title", "")),
            time=str(d.get("time", "")),
            note=str(d.get("note", "")),
            done=bool(d.get("done", False)),
            kind=str(d.get("kind", "task")),
            priority=str(d.get("priority", "normal")),
        )

DEFAULT_SETTINGS = {
    "week_start_monday": True,
    "show_week_numbers": False,
    "show_clock": True,
    "fullscreen_start": True,
    "always_on_top": True,
    "theme": "dark",
    "cell_gap": 1,
    "cell_padding": 4,
    "compact_header": True,
    "lang": "ru",
    "font_family": "Consolas",
    "font_mono": "Consolas",
    "font_title_size": 14,
    "font_body_size": 10,
    "font_small_size": 9,
    "font_day_size": 11,
    "font_day_bold": False,
    "font_task_size": 9,
    "color_app_bg": "#121212",
    "color_theme_bg": "#1e1e1e",
    "color_panel_bg": "#1a1a1a",
    "color_text": "#e0d4c3",
    "color_muted": "#888888",
    "color_header": "#d4c4a8",
    "color_button_bg": "#2a2a2a",
    "color_button_fg": "#e0d4c3",
    "color_button_active": "#3a3a3a",
    "color_weekend_bg": "#2c221a",
    "color_today_border": "#555555",
    "color_selected_border": "#888888",
    "color_task_default": "#d0d0d0",
    "color_task_event": "#81c784",
    "color_task_reminder": "#ffd54f",
    "color_today_text": "#ffffff",
    "color_detail_bg": "#1a1a1a",
    "color_detail_fg": "#e0d4c3",
}


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
                elif isinstance(val, (int, float)):
                    out[key] = bool(val)
                elif isinstance(val, str) and val.lower() in ("true", "1", "yes"):
                    out[key] = True
                elif isinstance(val, str) and val.lower() in ("false", "0", "no"):
                    out[key] = False
                else:
                    out[key] = default
            elif isinstance(default, int):
                iv = int(val)
                if key == "cell_gap":
                    out[key] = max(0, min(iv, 12))
                elif key == "cell_padding":
                    out[key] = max(0, min(iv, 20))
                elif key in ("font_title_size", "font_body_size", "font_small_size",
                             "font_day_size", "font_task_size"):
                    out[key] = max(6, min(iv, 72))
                else:
                    out[key] = iv
            elif isinstance(default, str):
                sv = str(val).strip()
                if key == "lang":
                    out[key] = sv if sv in ("ru", "en", "uk") else default
                elif key == "theme":
                    out[key] = sv if sv in ("dark", "light", "win95dark") else default
                elif key.startswith("color_"):
                    if sv.startswith("#") and len(sv) in (4, 7):
                        out[key] = sv
                    else:
                        out[key] = default
                else:
                    out[key] = sv if sv else default
        except (ValueError, TypeError, AttributeError):
            out[key] = default
    return out


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.title("Settings")
        self.app = app
        self.settings = app.settings.copy()
        self.geometry("450x650")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=app._base_bg())

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        self._build_general(general_frame)

        fonts_frame = ttk.Frame(notebook)
        notebook.add(fonts_frame, text="Fonts")
        self._build_fonts(fonts_frame)

        colors_frame = ttk.Frame(notebook)
        notebook.add(colors_frame, text="Colors")
        self._build_colors(colors_frame)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Save & Apply", command=self.save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)

    def _build_general(self, parent):
        self.vars = {}
        
        window_lf = ttk.LabelFrame(parent, text="Window", padding=10)
        window_lf.pack(fill="x", padx=10, pady=5)
        bools_window = ["fullscreen_start", "always_on_top"]
        for i, key in enumerate(bools_window):
            var = tk.BooleanVar(value=self.settings.get(key, False))
            self.vars[key] = var
            ttk.Checkbutton(window_lf, text=key.replace("_", " ").title(), variable=var).grid(row=i, column=0, sticky="w", pady=2)

        layout_lf = ttk.LabelFrame(parent, text="Layout & Logic", padding=10)
        layout_lf.pack(fill="x", padx=10, pady=5)
        bools_layout = ["week_start_monday", "show_week_numbers", "show_clock", "compact_header"]
        for i, key in enumerate(bools_layout):
            var = tk.BooleanVar(value=self.settings.get(key, False))
            self.vars[key] = var
            ttk.Checkbutton(layout_lf, text=key.replace("_", " ").title(), variable=var).grid(row=i//2, column=i%2, sticky="w", padx=10, pady=2)

        misc_lf = ttk.LabelFrame(parent, text="Miscellaneous", padding=10)
        misc_lf.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(misc_lf, text="Language").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        lang_var = tk.StringVar(value=self.settings.get("lang", "ru"))
        self.vars["lang"] = lang_var
        ttk.Entry(misc_lf, textvariable=lang_var, width=10).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(misc_lf, text="Theme").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        theme_var = tk.StringVar(value=self.settings.get("theme", "dark"))
        self.vars["theme"] = theme_var
        ttk.Entry(misc_lf, textvariable=theme_var, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        int_keys = ["cell_gap", "cell_padding"]
        for i, key in enumerate(int_keys, start=2):
            ttk.Label(misc_lf, text=key.replace("_", " ").title()).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            var = tk.IntVar(value=self.settings.get(key, 0))
            self.vars[key] = var
            ttk.Spinbox(misc_lf, from_=0, to=100, textvariable=var, width=8).grid(row=i, column=1, sticky="w", padx=5, pady=2)

    def _build_fonts(self, parent):
        lf = ttk.LabelFrame(parent, text="Font Configuration", padding=10)
        lf.pack(fill="both", expand=True, padx=10, pady=10)
        
        families = CompactCalendarApp._font_families()
        r = 0
        for key in ["font_family", "font_mono"]:
            ttk.Label(lf, text=key.replace("_", " ").title()).grid(row=r, column=0, sticky="w", padx=5, pady=5)
            var = tk.StringVar(value=self.settings.get(key, "Consolas"))
            self.vars[key] = var
            cb = ttk.Combobox(lf, textvariable=var, values=families, state="readonly", width=25)
            cb.grid(row=r, column=1, sticky="w", padx=5, pady=5)
            r += 1

        for key in ["font_title_size", "font_body_size", "font_small_size", "font_day_size", "font_task_size"]:
            ttk.Label(lf, text=key.replace("_", " ").title()).grid(row=r, column=0, sticky="w", padx=5, pady=5)
            var = tk.IntVar(value=self.settings.get(key, 10))
            self.vars[key] = var
            ttk.Spinbox(lf, from_=6, to=72, textvariable=var, width=8).grid(row=r, column=1, sticky="w", padx=5, pady=5)
            r += 1

        var = tk.BooleanVar(value=self.settings.get("font_day_bold", False))
        self.vars["font_day_bold"] = var
        ttk.Checkbutton(lf, text="Font Day Bold", variable=var).grid(row=r, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    def _build_colors(self, parent):
        lf = ttk.LabelFrame(parent, text="Color Palette", padding=5)
        lf.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(lf, highlightthickness=0, bg=self.app._base_bg())
        scrollbar = ttk.Scrollbar(lf, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        color_keys = sorted([k for k in self.settings.keys() if k.startswith("color_")])
        self.color_vars = {}
        for i, key in enumerate(color_keys):
            label_text = key.replace("color_", "").replace("_", " ").title()
            ttk.Label(scrollable_frame, text=label_text, width=20).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            var = tk.StringVar(value=self.settings.get(key, "#ffffff"))
            self.color_vars[key] = var
            
            preview = tk.Label(scrollable_frame, bg=var.get(), width=4, relief="solid", borderwidth=1)
            preview.grid(row=i, column=1, padx=5, pady=2)
            
            btn = ttk.Button(scrollable_frame, text="Pick Color", command=lambda k=key, p=preview: self._pick_color(k, p))
            btn.grid(row=i, column=2, padx=5, pady=2)

    def _pick_color(self, key, preview_label):
        current = self.color_vars[key].get()
        color = colorchooser.askcolor(initialcolor=current, parent=self)[1]
        if color:
            self.color_vars[key].set(color)
            preview_label.config(bg=color)

    def reset_to_defaults(self):
        if messagebox.askyesno("Confirm", "Reset all settings to defaults?", parent=self):
            self.app.settings = DEFAULT_SETTINGS.copy()
            self.app.save()
            self.app.apply_settings()
            self.destroy()
            self.app.open_settings()

    def save(self):
        # W2-006: Build candidate settings and validate before applying
        candidate = self.app.settings.copy()
        raw = {}
        for k, v in self.vars.items():
            raw[k] = v.get()
        for k, v in self.color_vars.items():
            raw[k] = v.get()
        candidate.update(normalize_settings(raw))
        self.app.settings = candidate
        self.app.save()
        self.app.apply_settings()
        self.destroy()

class CompactCalendarApp:
    _FONT_FAMILIES_CACHE = None

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1280x860")
        self.root.minsize(1000, 680)
        self.settings = DEFAULT_SETTINGS.copy()
        self.tasks = {}
        self.current = date.today().replace(day=1)
        self.selected_day = date.today().day
        self.cells_by_day = {}
        self._generation = 0
        self._load()
        self._apply_window_mode()
        self._build_style()
        self._build_ui()
        self._bind_keys()
        self._rebuild_month()
        self._tick_clock()

    # ---------- helper properties ----------
    def _base_bg(self): return self.settings["color_app_bg"]
    def _panel_bg(self): return self.settings["color_panel_bg"]
    def _text_fg(self): return self.settings["color_text"]
    def _muted_fg(self): return self.settings["color_muted"]

    def open_settings(self):
        SettingsDialog(self.root, self)

    def apply_settings(self):
        self._apply_window_mode()
        self._build_style()
        self._rebuild_month()

    def _apply_window_mode(self):
        self.root.attributes("-fullscreen", self.settings.get("fullscreen_start", True))
        self.root.attributes("-topmost", self.settings.get("always_on_top", True))

    def _font(self, size, bold=False, mono=False):
        fam = self.settings["font_mono"] if mono else self.settings["font_family"]
        try: size = int(size)
        except (TypeError, ValueError): size = 10
        return (fam, size, "bold" if bold else "normal")

    def _build_style(self):
        style = ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        bg = self._base_bg()
        panel = self._panel_bg()
        fg = self._text_fg()
        muted = self._muted_fg()
        btn_bg = self.settings.get("color_button_bg", panel)
        btn_fg = self.settings.get("color_button_fg", fg)
        btn_active = self.settings.get("color_button_active", bg)

        self.root.configure(bg=bg)
        
        # Base ttk elements
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        
        # Label elements
        style.configure("TLabel", background=bg, foreground=fg, font=self._font(self.settings["font_body_size"]))
        style.configure("Panel.TLabel", background=panel, foreground=fg, font=self._font(self.settings["font_body_size"]))
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("PanelMuted.TLabel", background=panel, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("Title.TLabel", background=bg, foreground=fg, font=self._font(self.settings["font_title_size"], True))
        style.configure("Small.TLabel", background=bg, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("Header.TLabel", background=bg, foreground=self.settings.get("color_header", fg), font=self._font(self.settings["font_body_size"], True))
        
        # Form & Control elements
        style.configure("TButton", background=btn_bg, foreground=btn_fg, font=self._font(self.settings["font_small_size"]), padding=(8, 4), borderwidth=0)
        style.map("TButton", background=[("active", btn_active), ("pressed", btn_active)])
        
        style.configure("Compact.TButton", font=self._font(self.settings["font_small_size"]), padding=(5, 2))
        
        # Entry, Spinbox, Combobox styling to avoid white backgrounds in dark mode
        for widget in ["TEntry", "TSpinbox", "TCombobox"]:
            style.configure(widget, fieldbackground=panel, foreground=fg, background=panel, bordercolor=bg, lightcolor=bg, darkcolor=bg, arrowcolor=fg)
        
        style.configure("TCheckbutton", background=bg, foreground=fg, indicatorcolor=panel)
        style.map("TCheckbutton", background=[("active", bg)], indicatorcolor=[("selected", btn_fg), ("pressed", bg)])
        
        # Notebook styling
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=panel, foreground=muted, padding=(10, 4), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", bg)], foreground=[("selected", fg)])
        
        # LabelFrame
        style.configure("TLabelframe", background=bg, foreground=fg, bordercolor=panel)
        style.configure("TLabelframe.Label", background=bg, foreground=fg, font=self._font(self.settings["font_body_size"], True))

    @classmethod
    def _font_families(cls):
        if cls._FONT_FAMILIES_CACHE is not None:
            return cls._FONT_FAMILIES_CACHE
        try:
            fams = sorted(set(tkfont.families()))
            preferred = ["Segoe UI", "Arial", "Tahoma", "Verdana", "Calibri", "Consolas", "Cascadia Mono", "JetBrains Mono"]
            out = [f for f in preferred if f in fams] + [f for f in fams if f not in preferred]
        except Exception:
            out = ["Segoe UI", "Arial", "Tahoma", "Verdana", "Consolas"]
        cls._FONT_FAMILIES_CACHE = out
        return out

    # ---------- layout ----------
    def _build_ui(self):
        # top bar: month/year + clock
        self.top_bar = ttk.Frame(self.root)
        self.top_bar.pack(fill="x", padx=10, pady=(8, 4))

        self.month_lbl = ttk.Label(self.top_bar, text=" ", style="Title.TLabel")
        self.month_lbl.pack(side="left")

        self.clock_lbl = ttk.Label(self.top_bar, text=" ", style="Header.TLabel")
        self.clock_lbl.pack(side="left", padx=(20, 0))

        self.settings_btn = ttk.Button(self.top_bar, text="⚙", style="Compact.TButton", width=3, command=self.open_settings)
        self.settings_btn.pack(side="right", anchor="e")

        # calendar grid area
        self.calendar_frame = ttk.Frame(self.root)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.week_row = ttk.Frame(self.calendar_frame)
        self.week_row.pack(fill="x", pady=(0, 4))

        self.grid_frame = ttk.Frame(self.calendar_frame)
        self.grid_frame.pack(fill="both", expand=True)

    # ---------- key bindings ----------
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
        self.root.bind("<Escape>", self.exit_app)
        self.root.bind("<Left>", lambda e: None if self._is_editing_focused() else self.prev_month())
        self.root.bind("<Right>", lambda e: None if self._is_editing_focused() else self.next_month())
        self.root.bind("<Up>", lambda e: None if self._is_editing_focused() else self.prev_year())
        self.root.bind("<Down>", lambda e: None if self._is_editing_focused() else self.next_year())
        self.root.bind("a", lambda e: None if self._is_editing_focused() else self.add_task())
        self.root.bind("e", lambda e: None if self._is_editing_focused() else self.edit_task())
        self.root.bind("d", lambda e: None if self._is_editing_focused() else self.delete_task())
        self.root.bind("s", lambda e: None if self._is_editing_focused() else self.save())
        self.root.bind("o", lambda e: None if self._is_editing_focused() else self.open_settings())
        self.root.bind("<space>", lambda e: None if self._is_editing_focused() else self.toggle_done())
        self.root.bind("<Delete>", lambda e: None if self._is_editing_focused() else self.delete_task())

    # ---------- task key & helpers ----------
    def _task_key(self, day_num=None):
        if day_num is None:
            day_num = self.selected_day
        try: day_num = int(day_num)
        except (TypeError, ValueError): day_num = self.selected_day
        return f"{self.current.year:04d}-{self.current.month:02d}-{day_num:02d}"

    def _month_name(self, y, m):
        if self.settings.get("lang", "ru") == "ru":
            ru_months = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
            try: return ru_months[int(m)]
            except: pass
        try: return calendar.month_name[int(m)]
        except Exception: return str(m)

    def _weekday_labels(self):
        lang = self.settings.get("lang", "ru")
        start_mon = self.settings.get("week_start_monday", True)
        if lang == "ru":
            return ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"] if start_mon else ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
        if start_mon:
            return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    def _cal(self):
        return calendar.Calendar(firstweekday=0 if self.settings["week_start_monday"] else 6)

    # ---------- month navigation ----------
    def _set_current_date(self, year, month, day=None):
        max_day = calendar.monthrange(year, month)[1]
        if day is None:
            day = self.selected_day
        self.current = date(year, month, 1)
        self.selected_day = max(1, min(day, max_day))
        self._rebuild_month()

    def _rebuild_month(self):
        self._render_header()
        self._build_calendar_grid()

    def _render_header(self):
        self.month_lbl.configure(
            text=f"{self._month_name(self.current.year, self.current.month)} {self.current.year}",
            font=self._font(self.settings["font_title_size"], True)
        )

    def _build_calendar_grid(self):
        # destroy existing widgets
        for w in self.week_row.winfo_children():
            w.destroy()
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.cells_by_day.clear()

        # week day headers
        labels = self._weekday_labels()
        for i, text in enumerate(labels):
            lbl = ttk.Label(self.week_row, text=text, style="Header.TLabel", anchor="center")
            lbl.grid(row=0, column=i, sticky="ew", padx=1)
            self.week_row.grid_columnconfigure(i, weight=1)

        weeks = self._cal().monthdayscalendar(self.current.year, self.current.month)
        today = date.today()
        gap = int(self.settings["cell_gap"])
        pad = int(self.settings["cell_padding"])
        weekend_bg = self.settings["color_weekend_bg"]
        cell_font = self._font(self.settings["font_day_size"], self.settings["font_day_bold"])
        task_dot_color = self.settings.get("color_task_dot", "#d7d7d7")
        theme_bg = self.settings.get("color_theme_bg", "#0f0f0f" if self.settings.get("theme", "dark") == "dark" else "#ffffff")

        for r, week in enumerate(weeks):
            col_offset = 0
            if self.settings["show_week_numbers"]:
                month_dates = self._cal().monthdatescalendar(self.current.year, self.current.month)
                if r < len(month_dates):
                    weeknum = month_dates[r][0].isocalendar()[1]
                    wn = tk.Label(
                        self.grid_frame, text=str(weeknum),
                        bg=self._base_bg(), fg=self._muted_fg(),
                        font=self._font(self.settings["font_small_size"])
                    )
                    wn.grid(row=r, column=0, sticky="nswe", padx=(0, gap), pady=gap)
                    self.grid_frame.grid_columnconfigure(0, weight=0, minsize=26)
                    col_offset = 1

            for c, day_num in enumerate(week):
                col = c + col_offset
                self.grid_frame.grid_columnconfigure(col, weight=1)
                self.grid_frame.grid_rowconfigure(r, weight=1)

                if day_num == 0:
                    continue

                is_weekend = (c >= 5) if self.settings["week_start_monday"] else (c == 0 or c == 6)
                bg = weekend_bg if is_weekend else theme_bg

                # outer container for padding/gap
                cell_wrap = tk.Frame(self.grid_frame, bg=self._base_bg())
                cell_wrap.grid(row=r, column=col, sticky="nsew", padx=gap, pady=gap)

                # main cell frame with highlight border
                cell = tk.Frame(cell_wrap, bg=bg, highlightbackground=bg, highlightcolor=bg, highlightthickness=1)
                cell.pack(fill="both", expand=True)

                inner = tk.Frame(cell, bg=bg)
                inner.pack(fill="both", expand=True, padx=pad, pady=pad)

                top = tk.Frame(inner, bg=bg)
                top.pack(fill="x")

                num = tk.Label(top, text=str(day_num), bg=bg, fg=self._text_fg(), font=cell_font)
                num.pack(side="left", anchor="nw")

                top_right_frame = tk.Frame(top, bg=bg)
                top_right_frame.pack(side="left", fill="x", expand=True, padx=(4, 0))

                tasks_frame = tk.Frame(inner, bg=bg)
                tasks_frame.pack(fill="both", expand=True)

                # bind click to all sub-widgets
                for wgt in (cell_wrap, cell, inner, top, num, top_right_frame, tasks_frame):
                    wgt.bind("<Button-1>", lambda e, d=day_num: self.select_day(d))

                self.cells_by_day[day_num] = {
                    "container": cell_wrap,
                    "cell": cell,
                    "inner": inner,
                    "num_label": num,
                    "top_right_frame": top_right_frame,
                    "tasks_frame": tasks_frame,
                    "bg": bg,
                    "is_weekend": is_weekend,
                }

        # populate task dots and initial highlights
        max_day = calendar.monthrange(self.current.year, self.current.month)[1]
        for d in range(1, max_day + 1):
            self._update_cell_task_count(d)
        self._refresh_day_borders()

    # ---------- day selection and highlighting ----------
    def select_day(self, day_num):
        try: day_num = int(day_num)
        except (TypeError, ValueError): return
        max_day = calendar.monthrange(self.current.year, self.current.month)[1]
        day_num = max(1, min(day_num, max_day))
        if day_num == self.selected_day:
            return
        previous = self.selected_day
        self.selected_day = day_num
        self._refresh_day_borders(previous)

    def _refresh_day_borders(self, previous_day=None):
        if previous_day is not None and previous_day in self.cells_by_day:
            self._update_day_border(previous_day)
        if self.selected_day in self.cells_by_day:
            self._update_day_border(self.selected_day)
        # also refresh today's border if it exists in the current month
        today = date.today()
        if today.year == self.current.year and today.month == self.current.month:
            if today.day in self.cells_by_day:
                self._update_day_border(today.day)

    def _update_day_border(self, day_num):
        info = self.cells_by_day.get(day_num)
        if not info:
            return
        today = date.today()
        is_today = (day_num == today.day and self.current.month == today.month and self.current.year == today.year)
        is_selected = (day_num == self.selected_day)

        if is_selected:
            border = self.settings["color_selected_border"]
        elif is_today:
            border = self.settings["color_today_border"]
        else:
            border = info["bg"]

        thickness = 2 if is_today and not is_selected else 1
        info["cell"].configure(highlightbackground=border, highlightcolor=border, highlightthickness=thickness)
        info["num_label"].configure(fg=self.settings["color_today_text"] if is_today else self._text_fg())

    # ---------- task count per cell ----------
    def _update_cell_task_count(self, day_num):
        info = self.cells_by_day.get(day_num)
        if not info:
            return
        tasks = self.tasks.get(self._task_key(day_num), [])
        
        # PERF-001: Access frames directly to avoid widget leak
        for w in info["top_right_frame"].winfo_children():
            w.destroy()
        for w in info["tasks_frame"].winfo_children():
            w.destroy()

        for t in tasks[:6]:
            color = self.settings.get("color_task_default", "#e0e0e0")
            if t.kind == "event": color = self.settings.get("color_task_event", "#00aa00")
            elif t.kind == "reminder": color = self.settings.get("color_task_reminder", "#ffcc00")
            
            # W2-005: Show done-state visually
            if t.done:
                text = f"✓ {t.title}"
                fg = self._muted_fg()
            elif t.kind == "task":
                text = f"• {t.title}"
                fg = color
            else:
                text = t.title
                fg = color

            is_top = (t.kind in ["event", "reminder"])
            parent = info["top_right_frame"] if is_top else info["tasks_frame"]
            
            lbl = tk.Label(
                parent, text=text, bg=info["bg"], fg=fg,
                font=self._font(self.settings.get("font_task_size", 9)),
                anchor="nw", justify="left"
            )
            if is_top:
                lbl.pack(side="left", padx=(4, 0))
            else:
                lbl.pack(fill="x", pady=(2, 0))
            lbl.bind("<Button-1>", lambda e, d=day_num: self.select_day(d))

    # ---------- task CRUD (keyboard-driven) ----------
    def add_task(self):
        title = simpledialog.askstring("Add task", "Task title:", parent=self.root)
        if title is None: return
        title = title.strip()
        if not title: return
        time_str = simpledialog.askstring("Time", "Time (optional):", parent=self.root)
        if time_str is None: return
        note = simpledialog.askstring("Note", "Note (optional):", parent=self.root)
        if note is None: return
        kind = simpledialog.askstring("Kind", "task / event / reminder:", parent=self.root)
        if kind is None: return
        priority = simpledialog.askstring("Priority", "low / normal / high:", parent=self.root)
        if priority is None: return

        task = CalendarTask(
            title=title, time=time_str.strip(), note=note.strip(),
            kind=kind.strip().lower() if kind.strip() else "task",
            priority=priority.strip().lower() if priority.strip() else "normal",
        )
        key = self._task_key()
        self.tasks.setdefault(key, []).append(task)
        self._update_cell_task_count(self.selected_day)
        self.save()

    def _choose_task_index(self, key):
        tasks = self.tasks.get(key, [])
        if not tasks:
            messagebox.showinfo("Info", "No tasks on this day.", parent=self.root)
            return None
        if len(tasks) == 1:
            return 0
        # prompt for index
        idx = simpledialog.askinteger(
            "Select task",
            f"Choose task number (1-{len(tasks)}):",
            parent=self.root,
            minvalue=1, maxvalue=len(tasks)
        )
        if idx is None:
            return None
        return idx - 1

    def edit_task(self):
        key = self._task_key()
        idx = self._choose_task_index(key)
        if idx is None:
            return
        items = self.tasks.get(key, [])
        if idx >= len(items):
            return
        task = items[idx]
        title = simpledialog.askstring("Edit title", "Task title:", initialvalue=task.title, parent=self.root)
        if title is None: return
        title = title.strip()
        if not title: return
        time_str = simpledialog.askstring("Edit time", "Time:", initialvalue=task.time, parent=self.root)
        if time_str is None: return
        note = simpledialog.askstring("Edit note", "Note:", initialvalue=task.note, parent=self.root)
        if note is None: return
        kind = simpledialog.askstring("Edit kind", "task / event / reminder:", initialvalue=task.kind, parent=self.root)
        if kind is None: return
        priority = simpledialog.askstring("Edit priority", "low / normal / high:", initialvalue=task.priority, parent=self.root)
        if priority is None: return

        items[idx] = CalendarTask(
            title=title, time=time_str.strip(), note=note.strip(), done=task.done,
            kind=kind.strip().lower(), priority=priority.strip().lower(),
        )
        self._update_cell_task_count(self.selected_day)
        self.save()

    def delete_task(self):
        key = self._task_key()
        idx = self._choose_task_index(key)
        if idx is None:
            return
        items = self.tasks.get(key, [])
        if idx >= len(items):
            return
        del items[idx]
        if not items:
            self.tasks.pop(key, None)
        self._update_cell_task_count(self.selected_day)
        self.save()

    def toggle_done(self):
        key = self._task_key()
        items = self.tasks.get(key, [])
        idx = self._choose_task_index(key)
        if idx is None or idx >= len(items):
            return
        items[idx].done = not items[idx].done
        self._update_cell_task_count(self.selected_day)
        self.save()

    # ---------- navigation ----------
    def prev_month(self):
        y, m = self.current.year, self.current.month
        if m == 1:
            y, m = y - 1, 12
        else:
            m -= 1
        self._set_current_date(y, m)

    def next_month(self):
        y, m = self.current.year, self.current.month
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
        self._set_current_date(y, m)

    def prev_year(self):
        y = self.current.year - 1
        if y < date.min.year: return
        m = self.current.month
        self._set_current_date(y, m)

    def next_year(self):
        y = self.current.year + 1
        if y > date.max.year: return
        m = self.current.month
        self._set_current_date(y, m)

    def go_today(self):
        t = date.today()
        self._set_current_date(t.year, t.month, t.day)

    # ---------- clock ----------
    def _tick_clock(self):
        if self.settings.get("show_clock", True):
            now = datetime.now()
            if self.settings.get("lang", "ru") == "ru":
                ru_months_nom = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
                ru_weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
                day = now.day
                suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
                m_name = ru_months_nom[now.month] if 1 <= now.month <= 12 else str(now.month)
                w_name = ru_weekdays[now.weekday()]
                self.clock_lbl.config(text=f"Сегодня {day}{suffix} {m_name}, {now.year} {w_name}")
            else:
                self.clock_lbl.config(text=now.strftime("%d %b %Y  %H:%M:%S"))
            delay_ms = (60 - now.second) * 1000
        else:
            self.clock_lbl.config(text="")
            delay_ms = 60_000
        self.root.after(delay_ms, self._tick_clock)

    # ---------- persistence ----------
    def save(self):
        self._save()

    def _save(self):
        try: geom = self.root.geometry()
        except: geom = ""
        self._generation += 1
        payload = {
            "settings": self.settings,
            "tasks": {k: [t.to_dict() for t in v] for k, v in self.tasks.items()},
            "state": {
                "year": self.current.year,
                "month": self.current.month,
                "selected_day": self.selected_day,
            },
            "window_geometry": geom,
            "generation": self._generation,
        }
        # CORE-003 + W2-001: Atomic write via temp file + rename
        try:
            DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=str(DATA_PATH.parent), prefix=".cal_tmp_", suffix=".json"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, str(DATA_PATH))
            except Exception:
                try: os.unlink(tmp_path)
                except OSError: pass
        except (OSError, TypeError, ValueError):
            pass

    def _load(self):
        if not DATA_PATH.exists():
            return

        raw_text = None
        try:
            raw_text = DATA_PATH.read_text(encoding="utf-8")
        except OSError:
            return

        payload = None
        try:
            payload = json.loads(raw_text)
        except (json.JSONDecodeError, ValueError):
            return

        if not isinstance(payload, dict):
            return

        # CORE-001 + CORE-002: Parse each section independently
        # Settings - normalize per-key
        raw_settings = payload.get("settings", {})
        if isinstance(raw_settings, dict):
            new_settings = normalize_settings(raw_settings)
            if new_settings:
                for k, v in new_settings.items():
                    if k in DEFAULT_SETTINGS:
                        self.settings[k] = v

        # Tasks - keep even if state fails
        raw_tasks = payload.get("tasks", {})
        if isinstance(raw_tasks, dict):
            loaded_tasks = {}
            for k, v in raw_tasks.items():
                if not isinstance(k, str): continue
                if not isinstance(v, list): continue
                loaded_tasks[k] = [CalendarTask.from_dict(x) for x in v if isinstance(x, dict)]
            self.tasks = loaded_tasks

        # State - recover gracefully from partial/malformed data
        st = payload.get("state", {})
        if isinstance(st, dict):
            try: y = int(st.get("year", date.today().year))
            except (TypeError, ValueError): y = date.today().year
            try: m = int(st.get("month", date.today().month))
            except (TypeError, ValueError): m = date.today().month
            try: d = int(st.get("selected_day", date.today().day))
            except (TypeError, ValueError): d = date.today().day
            if 1 <= m <= 12:
                self.current = date(y, m, 1)
                self.selected_day = min(max(1, d), calendar.monthrange(y, m)[1])

        # Generation counter
        self._generation = payload.get("generation", 0)

        geom = payload.get("window_geometry", "")
        if geom and not self.settings.get("fullscreen_start"):
            try: self.root.geometry(geom)
            except: pass

    def exit_app(self, event=None):
        self._save()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CompactCalendarApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()