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
import sys
import os
import tempfile
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
                             "font_day_size"):
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
        self._draft_settings = None
        self._day_widgets = {}

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
        self.var_gap = tk.IntVar()
        self.var_pad = tk.IntVar()
        self.var_font_family = tk.StringVar()
        self.var_font_mono = tk.StringVar()
        self.var_title_size = tk.IntVar()
        self.var_body_size = tk.IntVar()
        self.var_small_size = tk.IntVar()
        self.var_day_size = tk.IntVar()
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
        self.root.bind("<Escape>", self.handle_escape)
        self.root.bind("<Left>", lambda e: None if self._is_editing_focused() else self.prev_month())
        self.root.bind("<Right>", lambda e: None if self._is_editing_focused() else self.next_month())
        self.root.bind("<Up>", lambda e: None if self._is_editing_focused() else self.prev_year())
        self.root.bind("<Down>", lambda e: None if self._is_editing_focused() else self.next_year())
        self.root.bind("f", lambda e: None if self._is_editing_focused() else self.toggle_focus())
        self.root.bind("a", lambda e: None if self._is_editing_focused() else self.add_task())
        self.root.bind("e", lambda e: None if self._is_editing_focused() else self.edit_task())
        self.root.bind("d", lambda e: None if self._is_editing_focused() else self.delete_task())
        self.root.bind("s", lambda e: None if self._is_editing_focused() else self.save())
        self.root.bind("<space>", lambda e: None if self._is_editing_focused() else self.toggle_done())
        self.root.bind("<Return>", self.handle_return)
        self.root.bind("<Control-k>", lambda e: self.toggle_settings())
        self.root.bind("<MouseWheel>", self._scroll_settings)
        self.root.bind("<Button-4>", self._scroll_settings_linux)
        self.root.bind("<Button-5>", self._scroll_settings_linux)

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
        detail_bg = self.settings["color_detail_bg"]
        fg = self.settings["color_detail_fg"]
        self.task_list.configure(bg=detail_bg, fg=fg)
        self.detail_lbl.configure(bg=detail_bg, fg=fg)
        for w in (self.edit_title, self.edit_time, self.edit_note):
            w.configure(bg=detail_bg, fg=fg, insertbackground=fg)

    def _render_header(self):
        self.month_lbl.configure(text=f"{self._month_name(self.current.year, self.current.month)} {self.current.year}")
        self.month_lbl.configure(font=self._font(self.settings["font_title_size"], True))
        self.sub_lbl.configure(font=self._font(self.settings["font_small_size"]))
        self.clock_lbl.configure(font=self._font(self.settings["font_body_size"], True), foreground=self.settings["color_header"])

    def _bind_day_widget(self, widget, day_num):
        widget.bind("<Button-1>", lambda e, d=day_num: self.select_day(d))

    def _render_calendar(self):
        self._day_widgets = {}  # PERF-002: Track per-day widgets for targeted updates
        for w in self.week_row.winfo_children():
            w.destroy()
        for w in self.grid_frame.winfo_children():
            w.destroy()
            
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
        today_border = self.settings["color_today_border"]
        selected_border = self.settings["color_selected_border"]
        task_dot = self.settings["color_task_dot"]
        today_text = self.settings["color_today_text"]
        cell_font = self._font(self.settings["font_day_size"], self.settings["font_day_bold"])

        for r, week in enumerate(weeks):
            col_offset = 0
            if self.settings["show_week_numbers"]:
                month_weeks = self._cal().monthdatescalendar(self.current.year, self.current.month)
                weeknum = month_weeks[r][0].isocalendar()[1]
                wn = tk.Label(
                    self.grid_frame,
                    text=str(weeknum),
                    bg=self._base_bg(),
                    fg=self._muted_fg(),
                    font=self._font(self.settings["font_small_size"]),
                )
                wn.grid(row=r, column=0, sticky="nswe", padx=(0, gap), pady=gap)
                self.grid_frame.grid_columnconfigure(0, weight=0, minsize=26)
                col_offset = 1

            for c, day_num in enumerate(week):
                col = c + col_offset
                self.grid_frame.grid_columnconfigure(col, weight=1)
                self.grid_frame.grid_rowconfigure(r, weight=1)

                cell_wrap = tk.Frame(self.grid_frame, bg=self._base_bg())
                cell_wrap.grid(row=r, column=col, sticky="nsew", padx=gap, pady=gap)

                if day_num == 0:
                    empty = tk.Frame(cell_wrap, bg=self._base_bg(), highlightthickness=0)
                    empty.pack(fill="both", expand=True)
                    continue

                is_today = day_num == today.day and self.current.month == today.month and self.current.year == today.year
                is_selected = day_num == self.selected_day
                is_weekend = (c >= 5) if self.settings["week_start_monday"] else (c == 0 or c == 6)

                bg = weekend_bg if is_weekend else self.settings["color_panel_bg"]
                border = selected_border if is_selected else (today_border if is_today else "#2a2a2a")

                cell = tk.Frame(cell_wrap, bg=bg, highlightbackground=border, highlightcolor=border, highlightthickness=2 if is_selected or is_today else 1)
                cell.pack(fill="both", expand=True)

                inner = tk.Frame(cell, bg=bg)
                inner.pack(fill="both", expand=True, padx=pad, pady=pad)

                top = tk.Frame(inner, bg=bg)
                top.pack(fill="x")

                num = tk.Label(
                    top,
                    text=str(day_num),
                    bg=bg,
                    fg=today_text if is_today else self._text_fg(),
                    font=cell_font,
                )
                num.pack(side="left")

                badge = None
                dots = None
                task_count = len(self.tasks.get(self._task_key(day_num), []))
                if task_count:
                    badge = tk.Label(
                        top,
                        text=f"{task_count}",
                        bg=bg,
                        fg=task_dot,
                        font=self._font(self.settings["font_small_size"], True),
                    )
                    badge.pack(side="right")

                    dots = tk.Label(
                        inner,
                        text="● " * min(task_count, 4),
                        bg=bg,
                        fg=task_dot,
                        font=self._font(self.settings["font_small_size"]),
                    )
                    dots.pack(anchor="w", pady=(4, 0))

                self._bind_day_widget(cell, day_num)
                self._bind_day_widget(inner, day_num)
                self._bind_day_widget(top, day_num)
                self._bind_day_widget(num, day_num)
                if task_count:
                    self._bind_day_widget(badge, day_num)
                    self._bind_day_widget(dots, day_num)

                self._day_widgets[day_num] = {
                    "cell": cell, "inner": inner, "top": top, "num": num,
                    "badge": badge, "dots": dots,
                    "bg": bg, "border": border, "is_today": is_today,
                    "is_weekend": is_weekend,
                }

    def _update_day_visuals(self, day_num):
        """Update the visual state of a single day cell (selection/today borders)."""
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
        bg = weekend_bg if is_weekend else self.settings["color_panel_bg"]
        border = selected_border if is_selected else (today_border if is_today else "#2a2a2a")
        info["cell"].configure(bg=bg, highlightbackground=border, highlightcolor=border,
                               highlightthickness=2 if is_selected or is_today else 1)
        for w in [info["inner"], info["top"]]:
            try: w.configure(bg=bg)
            except tk.TclError: pass
        try: info["num"].configure(bg=bg)
        except tk.TclError: pass
        if info.get("badge"):
            try: info["badge"].configure(bg=bg)
            except tk.TclError: pass
        if info.get("dots"):
            try: info["dots"].configure(bg=bg)
            except tk.TclError: pass

    def _render_side(self):
        try:
            dt = date(self.current.year, self.current.month, self.selected_day)
            self.side_date.config(text=dt.strftime("%A, %d %B %Y"))
        except ValueError:
            self.side_date.config(text=self._task_key())
        key = self._task_key()
        items = self.tasks.get(key, [])
        self.task_list.delete(0, "end")
        for task in items:
            mark = "✓" if task.done else "•"
            priority = "!" if task.priority == "high" else " "
            time_text = f"{task.time} " if task.time else " "
            self.task_list.insert("end", f"{mark} {time_text}{priority}{task.title}")

        self._update_detail_box()

    def _update_detail_box(self):
        key = self._task_key()
        items = self.tasks.get(key, [])
        self.detail_lbl.configure(state="normal")
        self.detail_lbl.delete("1.0", "end")
        if not items:
            self.detail_lbl.insert("end", "No tasks.\n\nA add\nE edit\nD delete\nSpace done")
        else:
            for idx, task in enumerate(items, 1):
                self.detail_lbl.insert("end", f"{idx}. {task.title}\n")
                self.detail_lbl.insert("end", f"   kind: {task.kind} | priority: {task.priority} | done: {task.done}\n")
                if task.time:
                    self.detail_lbl.insert("end", f"   time: {task.time}\n")
                if task.note:
                    self.detail_lbl.insert("end", f"   note: {task.note}\n")
                self.detail_lbl.insert("end", "\n")
        self.detail_lbl.configure(state="disabled")

    def select_day(self, day_num):
        if self.is_editing:
            self.cancel_task()
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
        if self.settings.get("focus_mode", False):
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
        if self.editing_idx is not None:
            task.done = self.tasks[key][self.editing_idx].done
            self.tasks[key][self.editing_idx] = task
        else:
            self.tasks.setdefault(key, []).append(task)

        self.save()
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
        try:
            sel = self.task_list.curselection()
        except tk.TclError:
            sel = ()
        if sel:
            idx = int(sel[0])
            if idx >= 0:
                return idx
        if self.tasks.get(self._task_key()):
            return 0
        return None

    def delete_task(self):
        if self.is_editing:
            return
        key = self._task_key()
        items = self.tasks.get(key, [])
        idx = self._selected_index()
        if idx is None or idx >= len(items):
            return
        del items[idx]
        if not items:
            self.tasks.pop(key, None)
        self.save()
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
        items[idx].done = not items[idx].done
        self.save()
        # PERF-002: Update only the affected day badge + side panel
        self._update_day_visuals(self.selected_day)
        self._render_side()

    def toggle_focus(self, event=None):
        if self.is_editing:
            self.cancel_task()
        self.settings["focus_mode"] = not self.settings.get("focus_mode", False)
        self._apply_focus_visual(self.settings["focus_mode"])
        self.save()

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
            self._sync_settings_vars()  # W2-008: sync draft only when opening
            self._show_settings_panel()
        else:
            self.settings_panel.place_forget()

    def _show_settings_panel(self):
        w = 460
        h = 560
        x = max(20, self.root.winfo_width() - w - 20)
        y = 70
        self.settings_panel.place(x=x, y=y, width=w, height=h)
        self.settings_panel.lift()

    def pick_color(self, key):
        try:
            color = colorchooser.askcolor(title=key, initialcolor=self.settings[key])
        except tk.TclError:
            color = None
        if color and color[1]:
            self.settings[key] = color[1]
            preview = self.color_previews.get(key)
            if preview is not None:
                preview.configure(bg=color[1])
            self.apply_settings(silent=True)

    def _sync_settings_vars(self):
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
        validated = normalize_settings(raw)
        candidate.update(validated)
        self.settings = candidate
        
        self.root.attributes("-topmost", self.settings["always_on_top"])
        
        if not self.settings.get("focus_mode", False):
            self.root.attributes("-fullscreen", self.settings["fullscreen_start"])
            
        self._build_style()
        self._save()
        self._refresh_all()
        if not silent and self.show_settings_panel:
            self._show_settings_panel()

    def reset_settings(self):
        self.settings = DEFAULT_SETTINGS.copy()
        # W2-004: Reconcile focus visuals when resetting
        self._apply_focus_visual(self.settings.get("focus_mode", False))
        self._sync_settings_vars()
        self.apply_settings()

    def prev_month(self):
        y, m = self.current.year, self.current.month
        if m == 1:
            y -= 1
            m = 12
        else:
            m -= 1
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._refresh_all()

    def next_month(self):
        y, m = self.current.year, self.current.month
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._refresh_all()

    def prev_year(self):
        y = self.current.year - 1
        if y < date.min.year: return
        m = self.current.month
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._refresh_all()

    def next_year(self):
        y = self.current.year + 1
        if y > date.max.year: return
        m = self.current.month
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._refresh_all()

    def go_today(self):
        t = date.today()
        self.current = date(t.year, t.month, 1)
        self.selected_day = t.day
        self._refresh_all()

    def _tick_clock(self):
        if self.settings.get("show_clock", True):
            now = datetime.now()
            self.clock_lbl.config(text=now.strftime("%d %b %Y  %H:%M:%S"))
            delay_ms = (60 - now.second) * 1000
        else:
            self.clock_lbl.config(text="")
            delay_ms = 60_000
        self.root.after(delay_ms, self._tick_clock)

    def save(self):
        self._save()

    def _save(self):
        self._generation += 1
        payload = {
            "settings": self.settings,
            "tasks": {k: [t.to_dict() for t in v] for k, v in self.tasks.items()},
            "state": {
                "year": self.current.year,
                "month": self.current.month,
                "selected_day": self.selected_day,
            },
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
            for k, v in raw_tasks.items():
                if not isinstance(k, str):
                    continue
                if not isinstance(v, list):
                    continue
                loaded_tasks[k] = [CalendarTask.from_dict(x) for x in v if isinstance(x, dict)]
            self.tasks = loaded_tasks
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
        self._generation = payload.get("generation", 0)

    def exit_app(self, event=None):
        self._save()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CompactCalendarApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()