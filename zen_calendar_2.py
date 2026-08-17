import calendar
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, colorchooser, font as tkfont

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
            "title": self.title, "time": self.time, "note": self.note,
            "done": self.done, "kind": self.kind, "priority": self.priority,
        }

    @staticmethod
    def from_dict(d):
        if not isinstance(d, dict):
            d = {}
        return CalendarTask(
            title=str(d.get("title", "")), time=str(d.get("time", "")),
            note=str(d.get("note", "")), done=bool(d.get("done", False)),
            kind=str(d.get("kind", "task")), priority=str(d.get("priority", "normal")),
        )

DEFAULT_SETTINGS = {
    "week_start_monday": True, "show_week_numbers": False, "show_clock": True,
    "fullscreen_start": True, "always_on_top": True, "focus_mode": False,
    "theme": "dark", "cell_gap": 1, "cell_padding": 2, "compact_header": True,
    "lang": "ru", "font_family": "Segoe UI", "font_mono": "Consolas",
    "font_title_size": 14, "font_body_size": 9, "font_small_size": 8,
    "font_day_size": 9, "font_day_bold": True, "color_app_bg": "#0a0a0a",
    "color_panel_bg": "#141414", "color_text": "#e5e5e5", "color_muted": "#666666",
    "color_header": "#888888", "color_button_bg": "#1a1a1a", "color_button_fg": "#e5e5e5",
    "color_button_active": "#252525", "color_weekend_bg": "#121212",
    "color_today_border": "#6366f1", "color_selected_border": "#3f3f46",
    "color_task_dot": "#6366f1", "color_today_text": "#ffffff",
    "color_detail_bg": "#0f0f0f", "color_detail_fg": "#e5e5e5",
    "color_accent": "#6366f1",
}

class AddTaskDialog(tk.Toplevel):
    def __init__(self, parent, settings, task=None):
        super().__init__(parent)
        self.title("Edit Task" if task else "New Task")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.overrideredirect(False)
        
        self.settings = settings
        self.task = task
        self.result = None
        
        bg = settings.get("color_panel_bg", "#141414")
        fg = settings.get("color_text", "#e5e5e5")
        input_bg = settings.get("color_app_bg", "#0a0a0a")
        accent = settings.get("color_accent", "#6366f1")
        muted = settings.get("color_muted", "#666666")
        border = settings.get("color_selected_border", "#3f3f46")
        
        self.configure(bg=bg)
        
        self.var_title = tk.StringVar(value=task.title if task else "")
        self.var_time = tk.StringVar(value=task.time if task else "")
        self.var_kind = tk.StringVar(value=task.kind if task else "task")
        self.var_priority = tk.StringVar(value=task.priority if task else "normal")
        self.var_done = tk.BooleanVar(value=task.done if task else False)
        
        pad_x, pad_y = 16, 8
        font_lbl = (settings["font_family"], 8, "bold")
        font_inp = (settings["font_family"], 10)
        
        container = tk.Frame(self, bg=bg)
        container.pack(fill="both", expand=True, padx=1, pady=1)
        
        tk.Label(container, text="TITLE", bg=bg, fg=muted, font=font_lbl).grid(
            row=0, column=0, sticky="w", padx=pad_x, pady=(pad_y+4, 2)
        )
        self.ent_title = tk.Entry(
            container, textvariable=self.var_title, bg=input_bg, fg=fg,
            insertbackground=accent, relief="flat", font=font_inp, width=36,
            highlightthickness=1, highlightbackground=border, highlightcolor=accent,
        )
        self.ent_title.grid(row=1, column=0, columnspan=2, padx=pad_x, pady=(0, pad_y), sticky="ew")
        self.ent_title.focus_force()
        
        tk.Label(container, text="TIME", bg=bg, fg=muted, font=font_lbl).grid(
            row=2, column=0, sticky="w", padx=pad_x, pady=(pad_y, 2)
        )
        tk.Label(container, text="KIND", bg=bg, fg=muted, font=font_lbl).grid(
            row=2, column=1, sticky="w", padx=pad_x, pady=(pad_y, 2)
        )
        
        tk.Entry(
            container, textvariable=self.var_time, bg=input_bg, fg=fg,
            insertbackground=accent, relief="flat", font=font_inp, width=14,
            highlightthickness=1, highlightbackground=border, highlightcolor=accent,
        ).grid(row=3, column=0, padx=pad_x, pady=(0, pad_y), sticky="w")
        
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("Dialog.TCombobox", fieldbackground=input_bg, background=input_bg, foreground=fg, arrowcolor=fg, bordercolor=border)
        style.map("Dialog.TCombobox", fieldbackground=[("readonly", input_bg)], foreground=[("readonly", fg)])
        
        ttk.Combobox(
            container, textvariable=self.var_kind, values=["task", "event", "reminder"],
            state="readonly", style="Dialog.TCombobox", width=12,
        ).grid(row=3, column=1, padx=pad_x, pady=(0, pad_y), sticky="w")
        
        tk.Label(container, text="PRIORITY", bg=bg, fg=muted, font=font_lbl).grid(
            row=4, column=0, sticky="w", padx=pad_x, pady=(pad_y, 2)
        )
        
        ttk.Combobox(
            container, textvariable=self.var_priority, values=["low", "normal", "high"],
            state="readonly", style="Dialog.TCombobox", width=12,
        ).grid(row=5, column=0, padx=pad_x, pady=(0, pad_y), sticky="w")
        
        tk.Checkbutton(
            container, text="Done", variable=self.var_done, bg=bg, fg=fg,
            selectcolor=input_bg, activebackground=bg, activeforeground=accent,
            font=(settings["font_family"], 9), indicatoron=1,
        ).grid(row=5, column=1, padx=pad_x, pady=(0, pad_y), sticky="w")
        
        tk.Label(container, text="NOTE", bg=bg, fg=muted, font=font_lbl).grid(
            row=6, column=0, sticky="w", padx=pad_x, pady=(pad_y, 2)
        )
        self.txt_note = tk.Text(
            container, bg=input_bg, fg=fg, insertbackground=accent, relief="flat",
            height=3, width=36, font=font_inp,
            highlightthickness=1, highlightbackground=border, highlightcolor=accent,
        )
        self.txt_note.grid(row=7, column=0, columnspan=2, padx=pad_x, pady=(0, pad_y), sticky="ew")
        if task and task.note:
            self.txt_note.insert("1.0", task.note)
            
        btn_frame = tk.Frame(container, bg=bg)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=(16, pad_y+4), sticky="e", padx=pad_x)
        
        tk.Button(
            btn_frame, text="Cancel", command=self.destroy,
            bg=bg, fg=muted, relief="flat", width=8, font=(settings["font_family"], 9),
            activebackground=bg, activeforeground=fg, cursor="hand2",
        ).pack(side="left", padx=4)
        tk.Button(
            btn_frame, text="Save", command=self._save,
            bg=accent, fg="#ffffff", relief="flat", width=8,
            font=(settings["font_family"], 9, "bold"),
            activebackground="#5254cc", activeforeground="#ffffff", cursor="hand2",
        ).pack(side="left", padx=4)
        
        self.bind("<Return>", self._on_return)
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _on_return(self, event):
        if self.focus_get() == self.txt_note:
            return
        self._save()

    def _save(self):
        title = self.var_title.get().strip()
        if not title:
            self.ent_title.configure(highlightbackground="#dc2626")
            return
            
        self.result = {
            "title": title,
            "time": self.var_time.get().strip(),
            "note": self.txt_note.get("1.0", "end-1c").strip(),
            "kind": self.var_kind.get(),
            "priority": self.var_priority.get(),
            "done": self.var_done.get()
        }
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
        self.selected_task_idx = None
        self.show_settings_panel = False
        self._day_widgets = {}

        self._load()
        self._apply_window_mode()
        self._build_style()
        self._build_ui()
        self._bind_keys()
        self._refresh_all()
        self._tick_clock()

    def _base_bg(self): return self.settings["color_app_bg"]
    def _panel_bg(self): return self.settings["color_panel_bg"]
    def _text_fg(self): return self.settings["color_text"]
    def _muted_fg(self): return self.settings["color_muted"]
    def _accent(self): return self.settings.get("color_accent", "#6366f1")

    def _apply_window_mode(self):
        self.root.attributes("-fullscreen", self.settings.get("fullscreen_start", True))
        self.root.attributes("-topmost", self.settings.get("always_on_top", True))

    def _font(self, size, bold=False, mono=False):
        fam = self.settings["font_mono"] if mono else self.settings["font_family"]
        try: size = int(size)
        except (TypeError, ValueError): size = 9
        return (fam, size, "bold" if bold else "normal")

    def _build_style(self):
        style = ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        bg = self._base_bg()
        panel = self._panel_bg()
        fg = self._text_fg()
        muted = self._muted_fg()
        accent = self._accent()

        self.root.configure(bg=bg)
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=bg, foreground=fg, font=self._font(self.settings["font_body_size"]))
        style.configure("Panel.TLabel", background=panel, foreground=fg, font=self._font(self.settings["font_body_size"]))
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("PanelMuted.TLabel", background=panel, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("Title.TLabel", background=bg, foreground=fg, font=self._font(self.settings["font_title_size"], True))
        style.configure("Small.TLabel", background=bg, foreground=muted, font=self._font(self.settings["font_small_size"]))
        style.configure("Header.TLabel", background=bg, foreground=self.settings["color_header"], font=self._font(self.settings["font_small_size"], True))
        style.configure("TButton", font=self._font(self.settings["font_small_size"]), padding=(6, 2), background=bg, foreground=muted, borderwidth=0, relief="flat")
        style.map("TButton", background=[("active", bg)], foreground=[("active", fg)])
        style.configure("Compact.TButton", font=self._font(self.settings["font_small_size"]), padding=(4, 1), background=bg, foreground=muted, borderwidth=0, relief="flat")
        style.map("Compact.TButton", background=[("active", bg)], foreground=[("active", fg)])
        style.configure("Accent.TButton", font=self._font(self.settings["font_small_size"], True), padding=(8, 3), background=accent, foreground="#ffffff", borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#5254cc")])
        style.configure("TCombobox", padding=2)
        style.configure("TLabelframe", background=panel, foreground=fg, borderwidth=0)
        style.configure("TLabelframe.Label", background=panel, foreground=fg)

    @classmethod
    def _font_families(cls):
        if cls._FONT_FAMILIES_CACHE is not None:
            return cls._FONT_FAMILIES_CACHE
        try:
            fams = sorted(set(tkfont.families()))
            preferred = ["Segoe UI", "Inter", "Arial", "Tahoma", "Verdana", "Calibri", "Consolas", "Cascadia Mono", "JetBrains Mono"]
            out = [f for f in preferred if f in fams] + [f for f in fams if f not in preferred]
        except Exception:
            out = ["Segoe UI", "Arial", "Tahoma", "Verdana", "Consolas"]
        cls._FONT_FAMILIES_CACHE = out
        return out

    def _build_ui(self):
        self.top = ttk.Frame(self.root)
        self.top.pack(fill="x", padx=12, pady=(10, 6))
        
        self.month_lbl = ttk.Label(self.top, text=" ", style="Title.TLabel")
        self.month_lbl.pack(side="left")
        
        self.clock_lbl = ttk.Label(self.top, text=" ", style="Header.TLabel")
        self.clock_lbl.pack(side="right")
        
        self.nav = ttk.Frame(self.top)
        self.nav.pack(side="right", padx=(0, 16))
        
        self.btn_prev_year = ttk.Button(self.nav, text="⟪", style="Compact.TButton", command=self.prev_year)
        self.btn_prev_month = ttk.Button(self.nav, text="◀", style="Compact.TButton", command=self.prev_month)
        self.btn_today = ttk.Button(self.nav, text="Today", style="Compact.TButton", command=self.go_today)
        self.btn_next_month = ttk.Button(self.nav, text="▶", style="Compact.TButton", command=self.next_month)
        self.btn_next_year = ttk.Button(self.nav, text="⟫", style="Compact.TButton", command=self.next_year)
        for w in [self.btn_prev_year, self.btn_prev_month, self.btn_today, self.btn_next_month, self.btn_next_year]:
            w.pack(side="left", padx=1)
        
        self.main = ttk.Frame(self.root)
        self.main.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.left = ttk.Frame(self.main)
        self.left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.week_row = ttk.Frame(self.left)
        self.week_row.pack(fill="x", pady=(0, 2))

        self.grid_frame = ttk.Frame(self.left)
        self.grid_frame.pack(fill="both", expand=True)

        self.right = ttk.Frame(self.main, style="Panel.TFrame", width=240)
        self.right.pack(side="right", fill="y")
        self.right.pack_propagate(False)
        
        self.side_date = ttk.Label(self.right, text=" ", style="Panel.TLabel", font=self._font(11, bold=True))
        self.side_date.pack(anchor="w", padx=10, pady=(10, 2))
        
        self.side_weekday = ttk.Label(self.right, text=" ", style="PanelMuted.TLabel")
        self.side_weekday.pack(anchor="w", padx=10, pady=(0, 8))
        
        self.add_btn_wrap = ttk.Frame(self.right, style="Panel.TFrame")
        self.add_btn_wrap.pack(fill="x", padx=10, pady=(0, 8))
        self.btn_add = ttk.Button(self.add_btn_wrap, text="+ Add task", style="Accent.TButton", command=self.add_task)
        self.btn_add.pack(fill="x")
        
        self.tasks_container = tk.Frame(self.right, bg=self._panel_bg())
        self.tasks_container.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        self.bottom = ttk.Frame(self.root)
        self.bottom.pack(fill="x", padx=12, pady=(0, 6))
        
        self.help_lbl = ttk.Label(
            self.bottom, text="Esc · exit   F · focus   A · add   E · edit   D · del   Space · done   Arrows · nav",
            style="Small.TLabel",
        )
        self.help_lbl.pack(side="left")
        
        self.btn_settings = ttk.Button(self.bottom, text="⚙", style="Compact.TButton", command=self.toggle_settings)
        self.btn_settings.pack(side="right")
        
        self.btn_focus = ttk.Button(self.bottom, text="Focus", style="Compact.TButton", command=self.toggle_focus)
        self.btn_focus.pack(side="right", padx=(0, 4))
        
        self.settings_panel = ttk.Frame(self.root, style="Panel.TFrame")
        self.settings_panel.place_forget()
        self._build_settings_panel()

    def _build_settings_panel(self):
        self.settings_canvas = tk.Canvas(self.settings_panel, bg=self._panel_bg(), highlightthickness=0)
        self.settings_scroll = ttk.Scrollbar(self.settings_panel, orient="vertical", command=self.settings_canvas.yview)
        self.settings_inner = ttk.Frame(self.settings_canvas, style="Panel.TFrame")
        self.settings_inner.bind(
            "<Configure>", lambda e: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all")),
        )
        self.settings_canvas.create_window((0, 0), window=self.settings_inner, anchor="nw")
        self.settings_canvas.configure(yscrollcommand=self.settings_scroll.set)

        self.settings_canvas.pack(side="left", fill="both", expand=True)
        self.settings_scroll.pack(side="right", fill="y")

        inner = self.settings_inner
        ttk.Label(inner, text="Settings", style="Panel.TLabel", font=self._font(11, bold=True)).grid(
            row=0, column=0, sticky="w", columnspan=3, pady=(0, 10), padx=10
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
            ("Fullscreen on start", self.var_fullscreen), ("Always on top", self.var_topmost),
            ("Week starts Monday", self.var_week_monday), ("Show week numbers", self.var_weeknums),
            ("Show clock", self.var_clock), ("Start in focus mode", self.var_focus),
        ]:
            ttk.Checkbutton(inner, text=text, variable=var).grid(row=row, column=0, sticky="w", pady=2, columnspan=2, padx=10)
            row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        self._add_spin(inner, row, "Cell gap", self.var_gap, 0, 12); row += 1
        self._add_spin(inner, row, "Cell padding", self.var_pad, 0, 20); row += 1
        self._add_font(inner, row, "Font", self.var_font_family, self._font_families(), width=20); row += 1
        self._add_font(inner, row, "Mono", self.var_font_mono, self._font_families(), width=20); row += 1
        self._add_spin(inner, row, "Title", self.var_title_size, 10, 28); row += 1
        self._add_spin(inner, row, "Body", self.var_body_size, 8, 20); row += 1
        self._add_spin(inner, row, "Small", self.var_small_size, 7, 16); row += 1
        self._add_spin(inner, row, "Day", self.var_day_size, 8, 20); row += 1
        ttk.Checkbutton(inner, text="Bold day numbers", variable=self.var_day_bold).grid(row=row, column=0, sticky="w", pady=2, columnspan=2, padx=10)
        row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        color_rows = [
            ("App bg", "color_app_bg"), ("Panel bg", "color_panel_bg"),
            ("Text", "color_text"), ("Muted", "color_muted"), ("Header", "color_header"),
            ("Accent", "color_accent"), ("Weekend bg", "color_weekend_bg"),
            ("Today border", "color_today_border"), ("Selected border", "color_selected_border"),
            ("Task dot", "color_task_dot"), ("Today text", "color_today_text"),
        ]

        self.color_previews = {}
        for label, key in color_rows:
            ttk.Label(inner, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=1, padx=10)
            preview = tk.Label(inner, text="  ", bg=self.settings.get(key, DEFAULT_SETTINGS.get(key, "#000")), relief="solid", bd=1, width=4)
            preview.grid(row=row, column=1, sticky="w", padx=(8, 4))
            ttk.Button(inner, text="Pick", style="Compact.TButton", command=lambda k=key: self.pick_color(k)).grid(row=row, column=2, sticky="e", padx=(0, 10))
            self.color_previews[key] = preview
            row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1
        ttk.Button(inner, text="Apply", style="Compact.TButton", command=self.apply_settings).grid(row=row, column=0, sticky="w", padx=10)
        ttk.Button(inner, text="Reset", style="Compact.TButton", command=self.reset_settings).grid(row=row, column=1, sticky="e", padx=(0, 10))

    def _add_spin(self, parent, row, label, variable, minv, maxv):
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=1, padx=10)
        ttk.Spinbox(parent, from_=minv, to=maxv, textvariable=variable, width=6).grid(row=row, column=1, sticky="w", padx=(8, 0))

    def _add_font(self, parent, row, label, variable, values, width=20):
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=1, padx=10)
        ttk.Combobox(parent, textvariable=variable, values=values, width=width, state="readonly").grid(row=row, column=1, sticky="w", padx=(8, 0))

    def _bind_keys(self):
        self.root.bind("<Escape>", self.exit_app)
        self.root.bind("<Left>", lambda e: self.prev_month())
        self.root.bind("<Right>", lambda e: self.next_month())
        self.root.bind("<Up>", lambda e: self.prev_year())
        self.root.bind("<Down>", lambda e: self.next_year())
        self.root.bind("f", lambda e: self.toggle_focus())
        self.root.bind("a", lambda e: self.add_task())
        self.root.bind("e", lambda e: self.edit_task())
        self.root.bind("d", lambda e: self.delete_task())
        self.root.bind("s", lambda e: self.save())
        self.root.bind("<space>", lambda e: self.toggle_done())
        self.root.bind("<Return>", lambda e: self.edit_task())
        self.root.bind("<Control-k>", lambda e: self.toggle_settings())
        self.root.bind("<Delete>", lambda e: self.delete_task())
        self.root.bind("<Control-n>", lambda e: self.add_task())
        self.root.bind("<MouseWheel>", self._scroll_settings)
        self.root.bind("<Button-4>", self._scroll_settings_linux)
        self.root.bind("<Button-5>", self._scroll_settings_linux)

    def _scroll_settings(self, event):
        if self.show_settings_panel and hasattr(event, "delta") and event.delta:
            self.settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _scroll_settings_linux(self, event):
        if not self.show_settings_panel: return
        if getattr(event, "num", None) == 4: self.settings_canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5: self.settings_canvas.yview_scroll(1, "units")

    def _task_key(self, day_num=None):
        if day_num is None: day_num = self.selected_day
        try: day_num = int(day_num)
        except (TypeError, ValueError): day_num = self.selected_day
        return f"{self.current.year:04d}-{self.current.month:02d}-{day_num:02d}"

    def _month_name(self, y, m):
        try: return calendar.month_name[int(m)]
        except Exception: return str(m)

    def _weekday_labels(self):
        if self.settings["week_start_monday"]: return ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        return ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

    def _cal(self):
        return calendar.Calendar(firstweekday=0 if self.settings["week_start_monday"] else 6)

    def _refresh_all(self):
        self.root.configure(bg=self._base_bg())
        self._render_header()
        self._render_calendar()
        self._render_side()
        self._sync_settings_vars()
        self._apply_focus_visual(self.settings.get("focus_mode", False))
        if self.show_settings_panel: self._show_settings_panel()
        else: self.settings_panel.place_forget()

    def _render_header(self):
        self.month_lbl.configure(text=f"{self._month_name(self.current.year, self.current.month)} {self.current.year}")
        self.month_lbl.configure(font=self._font(self.settings["font_title_size"], True))
        self.clock_lbl.configure(font=self._font(self.settings["font_small_size"]), foreground=self.settings["color_header"])

    def _render_calendar(self):
        self._day_widgets = {}
        for w in self.week_row.winfo_children(): w.destroy()
        for w in self.grid_frame.winfo_children(): w.destroy()
        
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
        base_bg = self._base_bg()
        cell_font = self._font(self.settings["font_day_size"], self.settings["font_day_bold"])
        small_font = self._font(self.settings["font_small_size"])
        text_fg = self._text_fg()
        muted_fg = self._muted_fg()

        for r, week in enumerate(weeks):
            self.grid_frame.grid_rowconfigure(r, weight=1)
            for c, day_num in enumerate(week):
                self.grid_frame.grid_columnconfigure(c, weight=1)
                cell = tk.Frame(self.grid_frame, bg=base_bg)
                cell.grid(row=r, column=c, sticky="nsew", padx=gap, pady=gap)
                
                if day_num == 0:
                    continue

                is_today = day_num == today.day and self.current.month == today.month and self.current.year == today.year
                is_selected = day_num == self.selected_day
                is_weekend = (c >= 5) if self.settings["week_start_monday"] else (c == 0 or c == 6)

                if is_today:
                    bg = base_bg
                    border = today_border
                    thickness = 2
                elif is_selected:
                    bg = self.settings["color_selected_border"]
                    border = self.settings["color_selected_border"]
                    thickness = 1
                elif is_weekend:
                    bg = weekend_bg
                    border = weekend_bg
                    thickness = 0
                else:
                    bg = base_bg
                    border = base_bg
                    thickness = 0

                cell.configure(bg=bg, highlightbackground=border, highlightcolor=border, highlightthickness=thickness)
                
                inner = tk.Frame(cell, bg=bg)
                inner.pack(fill="both", expand=True, padx=pad+2, pady=pad+1)
                
                top = tk.Frame(inner, bg=bg)
                top.pack(fill="x")
                
                num_fg = today_text if is_today else (muted_fg if is_weekend else text_fg)
                num = tk.Label(top, text=str(day_num), bg=bg, fg=num_fg, font=cell_font, anchor="w")
                num.pack(side="left")

                badge = None
                task_count = len(self.tasks.get(self._task_key(day_num), []))
                if task_count:
                    badge = tk.Label(top, text=str(task_count), bg=bg, fg=task_dot, font=small_font)
                    badge.pack(side="right")
                    self._bind_day_widget(badge, day_num)
                    
                self._bind_day_widget(cell, day_num)
                self._bind_day_widget(inner, day_num)
                self._bind_day_widget(top, day_num)
                self._bind_day_widget(num, day_num)
                
                self._day_widgets[day_num] = {
                    'cell': cell, 
                    'inner': inner, 
                    'top': top,
                    'num': num,
                    'badge': badge,
                    'is_weekend': is_weekend, 
                    'is_today': is_today
                }

    def _bind_day_widget(self, widget, day_num):
        widget.bind("<Button-1>", lambda e, d=day_num: self.select_day(d))
        widget.bind("<Double-Button-1>", lambda e, d=day_num: self.select_day(d, open_add=True))

    def _update_cell_visual(self, day_num):
        info = self._day_widgets.get(day_num)
        if not info: return
        
        today = date.today()
        is_selected = day_num == self.selected_day
        is_weekend = info['is_weekend']
        is_today = info['is_today']
        
        weekend_bg = self.settings["color_weekend_bg"]
        base_bg = self._base_bg()
        
        if is_today:
            bg = base_bg
            border = self.settings["color_today_border"]
            thickness = 2
        elif is_selected:
            bg = self.settings["color_selected_border"]
            border = self.settings["color_selected_border"]
            thickness = 1
        elif is_weekend:
            bg = weekend_bg
            border = weekend_bg
            thickness = 0
        else:
            bg = base_bg
            border = base_bg
            thickness = 0
        
        widgets_to_update = [info['cell'], info['inner'], info['top'], info['num']]
        if info.get('badge'):
            widgets_to_update.append(info['badge'])
            
        for w in widgets_to_update:
            try:
                w.configure(bg=bg)
            except tk.TclError:
                pass
                
        info['cell'].configure(
            highlightbackground=border, 
            highlightcolor=border, 
            highlightthickness=thickness
        )

    def _render_side(self):
        try:
            dt = date(self.current.year, self.current.month, self.selected_day)
            self.side_date.config(text=dt.strftime("%d %B %Y"))
            self.side_weekday.config(text=dt.strftime("%A"))
        except ValueError:
            self.side_date.config(text=self._task_key())
            self.side_weekday.config(text="")
            
        for w in self.tasks_container.winfo_children():
            w.destroy()
            
        key = self._task_key()
        items = self.tasks.get(key, [])
        
        panel_bg = self._panel_bg()
        fg = self._text_fg()
        muted = self._muted_fg()
        accent = self._accent()
        
        if not items:
            lbl = tk.Label(
                self.tasks_container, text="No tasks yet",
                bg=panel_bg, fg=muted, font=self._font(self.settings["font_small_size"]),
            )
            lbl.pack(anchor="w", pady=8)
        else:
            if self.selected_task_idx is None or self.selected_task_idx >= len(items):
                self.selected_task_idx = 0
            for idx, task in enumerate(items):
                self._create_task_row(task, idx, idx == self.selected_task_idx)

    def _create_task_row(self, task, idx, is_selected):
        panel_bg = self._panel_bg()
        fg = self._text_fg()
        muted = self._muted_fg()
        accent = self._accent()
        
        row = tk.Frame(self.tasks_container, bg=panel_bg)
        row.pack(fill="x", pady=1)
        
        indicator_color = accent if is_selected else ("#444444" if task.done else "#2a2a2a")
        indicator = tk.Frame(row, bg=indicator_color, width=2)
        indicator.pack(side="left", fill="y", padx=(0, 6))
        indicator.pack_propagate(False)
        
        content = tk.Frame(row, bg=panel_bg)
        content.pack(side="left", fill="x", expand=True)
        
        title_line = tk.Frame(content, bg=panel_bg)
        title_line.pack(fill="x")
        
        if task.time:
            time_lbl = tk.Label(
                title_line, text=task.time,
                bg=panel_bg, fg=accent, font=self._font(self.settings["font_small_size"], True),
            )
            time_lbl.pack(side="left", padx=(0, 4))
        
        title_fg = muted if task.done else fg
        title_font = self._font(self.settings["font_body_size"], bold=False)
        title_text = task.title
        
        title_lbl = tk.Label(
            title_line, text=title_text, bg=panel_bg, fg=title_fg,
            font=title_font, anchor="w", justify="left",
        )
        title_lbl.pack(side="left", fill="x", expand=True)
        
        if task.priority == "high":
            prio = tk.Label(
                title_line, text="!", bg="#dc2626", fg="#ffffff",
                font=self._font(self.settings["font_small_size"], True),
                padx=3, pady=0,
            )
            prio.pack(side="right", padx=(4, 0))
        
        if task.note:
            note_preview = tk.Label(
                content, text=task.note[:40] + ("…" if len(task.note) > 40 else ""),
                bg=panel_bg, fg=muted, font=self._font(self.settings["font_small_size"]),
                anchor="w",
            )
            note_preview.pack(fill="x", pady=(1, 0))
        
        for w in (row, indicator, content, title_line, title_lbl):
            w.bind("<Button-1>", lambda e, i=idx: self._select_task(i))
            w.bind("<Double-Button-1>", lambda e, i=idx: self._edit_task_by_idx(i))
        
        if task.note:
            note_preview.bind("<Button-1>", lambda e, i=idx: self._select_task(i))
            note_preview.bind("<Double-Button-1>", lambda e, i=idx: self._edit_task_by_idx(i))

    def _select_task(self, idx):
        self.selected_task_idx = idx
        self._render_side()

    def _edit_task_by_idx(self, idx):
        key = self._task_key()
        items = self.tasks.get(key, [])
        if idx is None or idx >= len(items): return
        
        dlg = AddTaskDialog(self.root, self.settings, items[idx])
        self.root.wait_window(dlg)
        if dlg.result:
            items[idx] = CalendarTask(**dlg.result)
            self.save()
            self._refresh_all()

    def select_day(self, day_num, open_add=False):
        try: day_num = int(day_num)
        except (TypeError, ValueError): return
        max_day = calendar.monthrange(self.current.year, self.current.month)[1]
        day_num = max(1, min(day_num, max_day))
        
        old_day = self.selected_day
        if day_num == old_day:
            if open_add:
                self.add_task()
            return
            
        self.selected_day = day_num
        self.selected_task_idx = None
        
        self._update_cell_visual(old_day)
        self._update_cell_visual(day_num)
        self._render_side()
        
        if open_add:
            self.add_task()

    def add_task(self):
        dlg = AddTaskDialog(self.root, self.settings)
        self.root.wait_window(dlg)
        if dlg.result:
            task = CalendarTask(**dlg.result)
            self.tasks.setdefault(self._task_key(), []).append(task)
            self.save()
            self._refresh_all()

    def edit_task(self):
        self._edit_task_by_idx(self.selected_task_idx)

    def delete_task(self):
        key = self._task_key()
        items = self.tasks.get(key, [])
        idx = self.selected_task_idx
        if idx is None or idx >= len(items):
            return
        del items[idx]
        if not items: self.tasks.pop(key, None)
        self.selected_task_idx = None
        self.save()
        self._refresh_all()

    def toggle_done(self):
        key = self._task_key()
        items = self.tasks.get(key, [])
        idx = self.selected_task_idx
        if idx is None or idx >= len(items): return
        items[idx].done = not items[idx].done
        self.save()
        self._render_side()

    def toggle_focus(self):
        self.settings["focus_mode"] = not self.settings.get("focus_mode", False)
        self._apply_focus_visual(self.settings["focus_mode"])
        self._save()

    def _apply_focus_visual(self, active: bool):
        if active:
            if self.top.winfo_manager(): self.top.pack_forget()
            if self.bottom.winfo_manager(): self.bottom.pack_forget()
            if self.right.winfo_manager(): self.right.pack_forget()
        else:
            if not self.top.winfo_manager(): 
                self.top.pack(fill="x", padx=12, pady=(10, 6), before=self.main)
            if not self.bottom.winfo_manager(): 
                self.bottom.pack(fill="x", padx=12, pady=(0, 6), after=self.main)
            if not self.right.winfo_manager(): 
                self.right.pack(side="right", fill="y")

    def toggle_settings(self):
        self.show_settings_panel = not self.show_settings_panel
        if self.show_settings_panel: self._show_settings_panel()
        else: self.settings_panel.place_forget()

    def _show_settings_panel(self):
        w = 420
        h = 540
        x = max(20, self.root.winfo_width() - w - 20)
        y = 60
        self.settings_panel.place(x=x, y=y, width=w, height=h)
        self.settings_panel.lift()

    def pick_color(self, key):
        try: color = colorchooser.askcolor(title=key, initialcolor=self.settings.get(key, DEFAULT_SETTINGS.get(key, "#000000")))
        except tk.TclError: color = None
        if color and color[1]:
            self.settings[key] = color[1]
            preview = self.color_previews.get(key)
            if preview is not None: preview.configure(bg=color[1])
            self.apply_settings(silent=True)

    def _sync_settings_vars(self):
        self.var_fullscreen.set(self.settings.get("fullscreen_start", True))
        self.var_topmost.set(self.settings.get("always_on_top", True))
        self.var_week_monday.set(self.settings.get("week_start_monday", True))
        self.var_weeknums.set(self.settings.get("show_week_numbers", False))
        self.var_clock.set(self.settings.get("show_clock", True))
        self.var_focus.set(self.settings.get("focus_mode", False))
        self.var_gap.set(self.settings.get("cell_gap", 1))
        self.var_pad.set(self.settings.get("cell_padding", 2))
        self.var_font_family.set(self.settings.get("font_family", "Segoe UI"))
        self.var_font_mono.set(self.settings.get("font_mono", "Consolas"))
        self.var_title_size.set(self.settings.get("font_title_size", 14))
        self.var_body_size.set(self.settings.get("font_body_size", 9))
        self.var_small_size.set(self.settings.get("font_small_size", 8))
        self.var_day_size.set(self.settings.get("font_day_size", 9))
        self.var_day_bold.set(self.settings.get("font_day_bold", True))
        for k, p in self.color_previews.items():
            try: p.configure(bg=self.settings.get(k, DEFAULT_SETTINGS.get(k, "#000000")))
            except tk.TclError: pass

    def apply_settings(self, silent=False):
        self.settings["fullscreen_start"] = bool(self.var_fullscreen.get())
        self.settings["always_on_top"] = bool(self.var_topmost.get())
        self.settings["week_start_monday"] = bool(self.var_week_monday.get())
        self.settings["show_week_numbers"] = bool(self.var_weeknums.get())
        self.settings["show_clock"] = bool(self.var_clock.get())
        self.settings["focus_mode"] = bool(self.var_focus.get())
        self.settings["cell_gap"] = max(0, int(self.var_gap.get()))
        self.settings["cell_padding"] = max(0, int(self.var_pad.get()))
        self.settings["font_family"] = str(self.var_font_family.get()).strip() or DEFAULT_SETTINGS["font_family"]
        self.settings["font_mono"] = str(self.var_font_mono.get()).strip() or DEFAULT_SETTINGS["font_mono"]
        self.settings["font_title_size"] = max(8, int(self.var_title_size.get()))
        self.settings["font_body_size"] = max(6, int(self.var_body_size.get()))
        self.settings["font_small_size"] = max(6, int(self.var_small_size.get()))
        self.settings["font_day_size"] = max(6, int(self.var_day_size.get()))
        self.settings["font_day_bold"] = bool(self.var_day_bold.get())
        self.root.attributes("-topmost", self.settings["always_on_top"])
        self.root.attributes("-fullscreen", self.settings["fullscreen_start"])
        self._build_style()
        self._save()
        self._refresh_all()
        if not silent and self.show_settings_panel: self._show_settings_panel()

    def reset_settings(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self._sync_settings_vars()
        self.apply_settings()

    def prev_month(self):
        y, m = self.current.year, self.current.month
        if m == 1: y, m = y - 1, 12
        else: m -= 1
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._refresh_all()

    def next_month(self):
        y, m = self.current.year, self.current.month
        if m == 12: y, m = y + 1, 1
        else: m += 1
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._refresh_all()

    def prev_year(self):
        y = self.current.year - 1
        m = self.current.month
        self.current = date(y, m, 1)
        self.selected_day = min(self.selected_day, calendar.monthrange(y, m)[1])
        self._refresh_all()

    def next_year(self):
        y = self.current.year + 1
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
            self.clock_lbl.config(text=datetime.now().strftime("%H:%M"))
        else:
            self.clock_lbl.config(text="")
        self.root.after(1000, self._tick_clock)

    def save(self):
        self._save()

    def _save(self):
        try: geom = self.root.geometry()
        except tk.TclError: geom = ""
        payload = {
            "settings": self.settings,
            "tasks": {k: [t.to_dict() for t in v] for k, v in self.tasks.items()},
            "state": {
                "year": self.current.year,
                "month": self.current.month,
                "selected_day": self.selected_day,
            },
            "window_geometry": geom,
        }
        try:
            DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except (OSError, TypeError, ValueError):
            pass

    def _load(self):
        if not DATA_PATH.exists(): return
        try:
            payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            if not isinstance(payload, dict): return
            settings = payload.get("settings", {})
            if isinstance(settings, dict): self.settings.update(settings)
            
            raw_tasks = payload.get("tasks", {})
            if isinstance(raw_tasks, dict):
                loaded_tasks = {}
                for k, v in raw_tasks.items():
                    if not isinstance(k, str): continue
                    if not isinstance(v, list): continue
                    loaded_tasks[k] = [CalendarTask.from_dict(x) for x in v if isinstance(x, dict)]
                self.tasks = loaded_tasks

            st = payload.get("state", {})
            if isinstance(st, dict):
                y = int(st.get("year", date.today().year))
                m = int(st.get("month", date.today().month))
                d = int(st.get("selected_day", date.today().day))
                if 1 <= m <= 12:
                    self.current = date(y, m, 1)
                    self.selected_day = min(max(1, d), calendar.monthrange(y, m)[1])
            
            geom = payload.get("window_geometry", "")
            if geom and not self.settings.get("fullscreen_start"):
                try: self.root.geometry(geom)
                except tk.TclError: pass
        except Exception:
            self.settings = DEFAULT_SETTINGS.copy()
            self.tasks = {}
            self.current = date.today().replace(day=1)
            self.selected_day = date.today().day

    def exit_app(self, event=None):
        self._save()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CompactCalendarApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()