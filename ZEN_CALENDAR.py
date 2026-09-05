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
import time
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

APP_NAME = "VACZEN Calendar"
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
    # PERF-004 (wave 3): an ASCII string cannot contain a UTF-16 surrogate code
    # point, and CPython already knows the answer from the string's internal
    # representation. Establishing that in O(1) avoids a full O(length) regex
    # scan of multi-megabyte ASCII notes on every load/render.
    if s.isascii():
        return s
    # PERF-002: the UTF-16 sanitize pass only matters when a lone surrogate is
    # actually present. Skip the encode/decode (and its ~3x transient
    # allocation) for the common case of valid Unicode so large notes do not
    # pay the copy-amplification penalty on every load/render.
    if _SURROGATE_RE.search(s) is None:
        return s
    return s.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


class UnreadableDataFile(Exception):
    """CORE-004: DATA_PATH exists but cannot be read/decoded/parsed.

    Distinct from a missing file: a missing file may be safely created
    fresh, while a present-but-unreadable file MUST be preserved
    (quarantined) before any subsequent write.
    """


class _StaleWriter(Exception):
    """Raised inside the locked save path when the on-disk generation no
    longer matches the in-memory generation. Another instance committed
    newer data; the caller must reload rather than clobber the winner.
    """


class _LockAcquisitionFailure(Exception):
    """Raised by _save_lock when the interprocess lock cannot be obtained
    (directory-creation failure, open permission error, or lock contention).
    Fail-closed: the writer must NOT enter the critical section.

    ``permanent`` separates a condition that retrying cannot fix (open,
    permission, missing directory) from ordinary lock contention, so PERF-002's
    bounded retry never burns its deadline on a failure that will not clear.
    """

    def __init__(self, message, permanent=False):
        super().__init__(message)
        self.permanent = permanent


# Returned by save() when a stale-writer rejection occurred and the runtime was
# reloaded from disk. Distinct from True, and never treated as success: every
# caller branches on `is True` / `is STALE_WRITER` / otherwise (CORE-001).
STALE_WRITER = object()

# PERF-002: bounded contention budget for the interprocess save lock. Small
# enough to keep the GUI responsive, long enough to absorb another instance's
# ordinary save window instead of turning it into a user-visible failure.
LOCK_TIMEOUT_S = 0.25
LOCK_RETRY_START_S = 0.002
LOCK_RETRY_MAX_S = 0.020

# PERF-003: bounded detail-render batch. Fragments accumulate in a Python list
# until this many characters are pending, then one Text.insert flushes them, so
# Tcl crossings scale with rendered bytes instead of tasks x fields while peak
# transient memory stays capped.
DETAIL_BATCH_CHARS = 1 << 18  # 256 KiB

# PERF-005: exact naming contract for atomic-write candidates. Reclamation
# matches this prefix AND suffix in DATA_PATH's own directory, nothing else.
TMP_PREFIX = ".cal_tmp_"
TMP_SUFFIX = ".json"


def _platform_lock_path(data_path):
    return data_path.with_name(data_path.name + ".lock")


@contextmanager
def _save_lock(data_path, timeout=None):
    """CORE-002 / PERF-001: interprocess file lock spanning the whole
    read-check-write-replace sequence.

    * The OS primitive stays non-blocking; we never park the thread inside a
      blocking kernel wait.
    * PERF-002: ordinary contention is retried with a short backoff until a
      bounded deadline (``timeout`` seconds, default ``LOCK_TIMEOUT_S``) instead
      of failing on the first busy result. Another instance's ordinary save
      window is milliseconds-to-hundreds-of-milliseconds long, and rejecting a
      user's Save because of that overlap turned serialization into data loss.
    * Fail-closed: when the deadline passes, or the failure is permanent, we
      raise ``_LockAcquisitionFailure`` instead of proceeding without mutual
      exclusion. There is no unlocked fallback path.
    * Re-entrant within one process via the ``_held`` flag so a nested save
      (e.g. a settings commit triggered from inside a task save) serializes
      instead of dead-locking.
    """
    if getattr(_save_lock, "_held", False):
        # Same process: re-entrant serialization, no second OS lock.
        yield
        return
    if timeout is None:
        timeout = LOCK_TIMEOUT_S
    lock_path = _platform_lock_path(data_path)
    fd = None
    acquired = False
    try:
        try:
            data_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
        except OSError as exc:
            # Permanent: no amount of waiting creates a directory we may not
            # create or opens a file we may not open.
            raise _LockAcquisitionFailure(
                "could not open save lock %s: %s" % (lock_path, exc), permanent=True
            ) from exc
        deadline = time.monotonic() + max(0.0, float(timeout))
        delay = LOCK_RETRY_START_S
        while True:
            if os.name == "nt":
                try:
                    import msvcrt  # type: ignore
                    # LK_NBLCK returns immediately; OSError means another
                    # process holds the lock -> retry below, then fail-closed.
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    acquired = True
                except ImportError as exc:
                    raise _LockAcquisitionFailure(
                        "no locking primitive available", permanent=True
                    ) from exc
                except OSError:
                    acquired = False
            else:
                try:
                    import fcntl  # type: ignore
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except ImportError as exc:
                    raise _LockAcquisitionFailure(
                        "no locking primitive available", permanent=True
                    ) from exc
                except OSError:
                    acquired = False
            if acquired or time.monotonic() >= deadline:
                break
            time.sleep(min(delay, max(0.0, deadline - time.monotonic())))
            delay = min(delay * 2, LOCK_RETRY_MAX_S)
        if not acquired:
            raise _LockAcquisitionFailure(
                "could not acquire save lock on %s within %.3fs" % (lock_path, timeout)
            )
        _save_lock._held = True
        try:
            yield
        finally:
            _save_lock._held = False
    finally:
        if fd is not None:
            if acquired and os.name == "nt":
                try:
                    import msvcrt  # type: ignore
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                except (OSError, ImportError):
                    pass
            elif acquired:
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

# PERF-002: precompiled surrogate-range search used by sanitize_text to take
# the fast (no copy) path for valid Unicode.
_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


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


def _parse_generation(raw):
    """Shared strict generation parser for load and save-side reads.

    CORE-003 (wave 3): the generation is the ownership token stale-writer
    detection compares, so it is validated BEFORE any conversion, never
    coerced by ``int()``. Valid means: an actual ``int`` (``bool`` excluded --
    ``True`` is not generation 1), value >= 0. A float such as ``1.5``, a
    numeric string such as ``"7"``, NaN/Infinity, and every other type are
    invalid and raise, which routes the file through the existing
    corruption/quarantine recovery path instead of inventing an ownership
    token that no writer ever committed.
    """
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ValueError("invalid generation: %r is not an integer" % (raw,))
    if raw < 0:
        raise ValueError("invalid generation: %r is negative" % (raw,))
    return raw


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


def _decode_state(st):
    """W2-002: decode a persisted `state` section into `(current, selected_day)`.

    A pure function of the section alone, so startup and reload derive the same
    view from the same bytes. A missing or unusable field falls back to today's
    date policy rather than to whatever the live instance happened to hold.
    """
    today = date.today()
    if not isinstance(st, dict):
        st = {}
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
    return date(y, m, 1), min(max(1, d), max_day)


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
    # Class-level defaults for the authorization/identity state introduced by
    # the CORE/W2/PERF repairs. Instances set these in __init__; declaring them
    # here means a partially constructed instance (headless probes, a crash
    # part-way through startup) still answers "not blocked, nothing known"
    # instead of raising AttributeError inside the save path.
    _preservation_required = False
    _write_blocked = False
    _write_block_reason = None
    _disk_identity = None
    _ui_ready = False
    _pending_reconcile = False
    # Same reason for the pre-existing recovery flags: the save path reads them
    # to decide whether the file may be replaced, and that decision must never
    # depend on how far a constructor happened to get.
    _load_failed = False
    _partial_recovery = False
    _recovery_message = None
    _quarantine_path = None

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
        self._selection_owner_key = None
        self._invalid_task_keys = []
        self._partial_recovery = False
        self._recovery_message = None
        self._dirty = False
        # W2-001: authoritative write authorization. `_load_failed` is a
        # warning flag; these two decide whether DATA_PATH may be replaced at
        # all. `_preservation_required` means the load dropped or could not
        # represent persisted bytes, so an immutable snapshot MUST exist before
        # any rewrite; `_write_blocked` latches fail-closed when that snapshot
        # could not be created.
        self._preservation_required = False
        self._write_blocked = False
        self._write_block_reason = None
        # PERF-001: identity of the DATA_PATH snapshot this instance last
        # loaded or wrote, used to skip the O(file-size) reparse when no other
        # writer has touched the file.
        self._disk_identity = None
        # CORE-002: reconciliation needs the widget tree; and a reload that
        # arrives mid-edit defers the parts that would fight the editor.
        self._ui_ready = False
        self._pending_reconcile = False

        self._load()
        self._apply_window_mode()
        self._build_style()
        self._build_ui()
        self._bind_keys()
        self._ui_ready = True
        # CORE-002: one idempotent reconciliation path owns startup AND reload,
        # so no derived runtime state exists on only one of the two.
        self.reconcile_runtime_from_settings()

        self.root.update_idletasks()
        self.root.deiconify()
        if self._load_failed or self._write_blocked:
            self.root.after(200, self._warn_recovery_state)

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

    def _warn_recovery_state(self):
        """W2-001: report what actually happened -- never a fabricated path.

        The old message always named ``<data>.corrupt.bak`` even when no
        snapshot had been created, which told the user their data was preserved
        at a path that did not exist.
        """
        if self._write_blocked:
            body = (
                "The data file could not be read or fully recovered, and the\n"
                "backup copy could NOT be created "
                f"({self._write_block_reason or 'unknown reason'}).\n"
                "Saving is disabled so the original file is not overwritten.\n"
                "Free up the backup names or fix permissions, then save again."
            )
        elif self._quarantine_path is not None:
            body = (
                "The data file could not be fully read. The original was\n"
                f"preserved as\n{self._quarantine_path}\n"
                + (self._recovery_message or "Recoverable data was kept.")
            )
        else:
            body = self._recovery_message or "The data file could not be fully read."
        try:
            messagebox.showwarning("Data file recovery", body, parent=self.root)
        except tk.TclError:
            pass

    def reconcile_runtime_from_settings(self, *, render=True):
        """CORE-002 / W2-004: idempotent runtime reconciliation from the model.

        ONE path derives every piece of runtime state from ``self.settings``:
        window attributes, ttk style/fonts, focus-mode packing and fullscreen
        ownership, the single clock callback, and the rendered content. Startup,
        stale-writer reload, normal settings rollback and exception rollback all
        call this instead of each replaying a private subset -- which is how the
        model could claim focus mode was on while every panel was still packed.

        Idempotent by construction: fullscreen intent comes from the settings,
        never from a re-sampled live attribute, so calling it twice cannot
        capture "fullscreen" as the pre-focus state.
        """
        if not self._ui_ready:
            self._apply_window_mode()
            return
        focus = bool(self.settings.get("focus_mode", False))
        try:
            self.root.attributes("-topmost", self.settings.get("always_on_top", True))
        except tk.TclError:
            pass
        self._pre_focus_fs = bool(self.settings.get("fullscreen_start", True))
        self._build_style()
        # capture=False: the restore target is the persisted setting, so a
        # repeated reconcile cannot overwrite it with the current live value.
        self._apply_focus_visual(focus, capture=False)
        self._start_clock()
        if render:
            self._refresh_all()
            if self.is_editing:
                # The side panel belongs to the editor right now; finish the
                # deferred part when edit mode ends (CORE-002).
                self._pending_reconcile = True
        else:
            self._pending_reconcile = True

    def _flush_pending_reconcile(self):
        """Run the reconciliation deferred by an edit session, once."""
        if not self._pending_reconcile:
            return
        self._pending_reconcile = False
        if self._ui_ready and not self.is_editing:
            self._refresh_all()

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

        self.title_lbl = ttk.Label(self.title_wrap, text=APP_NAME, style="Title.TLabel")
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
        self.btn_save = ttk.Button(self.act_btns, text="Save", style="Compact.TButton", command=self.manual_save)
        
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

        # W2-003: in-panel validation line. A blank title is a validation
        # failure that keeps the draft, so it needs somewhere to say so that is
        # not a modal dialog and not the panel heading.
        self.edit_msg = ttk.Label(self.edit_frame, text="", style="PanelMuted.TLabel")
        self.edit_msg.grid(row=6, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 0))

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
        self.root.bind("s", lambda e: None if _blocked() else self.manual_save())
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
                try:
                    slot["cell"].pack_forget()
                    slot["empty"].pack_forget()
                except tk.TclError:
                    pass

                if day_num == 0:
                    slot["empty"].pack(fill="both", expand=True)
                    if slot["badge"] is not None:
                        try: slot["badge"].pack_forget()
                        except tk.TclError: pass
                    if slot["dots"] is not None:
                        try: slot["dots"].pack_forget()
                        except tk.TclError: pass
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
                        badge = tk.Label(top, text="", bg=bg, fg=task_dot,
                                         font=self._font(self.settings["font_small_size"], True))
                        self._bind_day_widget(badge, slot)
                        slot["badge"] = badge
                    badge.configure(text=f"{task_count}", bg=bg, fg=task_dot,
                                    font=self._font(self.settings["font_small_size"], True))
                    badge.pack(side="right")
                    dots = slot["dots"]
                    if dots is None:
                        dots = tk.Label(inner, text="", bg=bg, fg=task_dot,
                                        font=self._font(self.settings["font_small_size"]))
                        self._bind_day_widget(dots, slot)
                        slot["dots"] = dots
                    dots.configure(text="● " * min(task_count, 4), bg=bg, fg=task_dot,
                                   font=self._font(self.settings["font_small_size"]))
                    dots.pack(anchor="w", pady=(4, 0))
                else:
                    # No tasks: hide (do not destroy) the slot-owned indicators
                    # so the same persistent widgets are reused on the next
                    # render. This keeps indicator count bounded to one badge
                    # + one dots per slot (CORE-005).
                    if slot["badge"] is not None:
                        try: slot["badge"].pack_forget()
                        except tk.TclError: pass
                    if slot["dots"] is not None:
                        try: slot["dots"].pack_forget()
                        except tk.TclError: pass

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
                if slot is not None:
                    self._bind_day_widget(badge, slot)
                info["badge"] = badge
                if slot is not None:
                    slot["badge"] = badge
            badge.configure(text=f"{task_count}", bg=bg, fg=task_dot, font=small_bold)
            badge.pack(side="right")
            if dots is None:
                dots = tk.Label(info["inner"], text="", bg=bg, fg=task_dot, font=small)
                if slot is not None:
                    self._bind_day_widget(dots, slot)
                info["dots"] = dots
                if slot is not None:
                    slot["dots"] = dots
            dots.configure(text="● " * min(task_count, 4), bg=bg, fg=task_dot, font=small)
            dots.pack(anchor="w", pady=(4, 0))
        else:
            # Hide (do not destroy) the slot-owned indicators; keep the same
            # persistent widget references in both info and slot (CORE-005).
            if badge is not None:
                try: badge.pack_forget()
                except tk.TclError: pass
            if dots is not None:
                try: dots.pack_forget()
                except tk.TclError: pass

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
            # Same-day cache is valid: restore the visible selection and KEEP
            # the owner key so repeated same-day rerenders stay stable (W2-003).
            self.task_list.selection_set(self._selected_task_idx)
            self.task_list.activate(self._selected_task_idx)
        elif not items:
            # Empty day: there is nothing to select.
            self._selected_task_idx = None
            self._selection_owner_key = None
        # A non-empty day with a mismatched/None owner must NOT clear the owner
        # here; selection ownership is reset only on an actual day/month/year
        # transition (_reset_selection_cache). Load-recovery state
        # (_invalid_task_keys) is persistent and must survive rendering (W2-002).

        self._update_detail_box()

    def _update_detail_box(self):
        key = self._task_key()
        items = self.tasks.get(key, [])
        self.detail_lbl.configure(state="normal")
        self.detail_lbl.delete("1.0", "end")
        if not items:
            self.detail_lbl.insert("end", "No tasks.\n\nA add\nE edit\nD delete\nSpace done")
            self.detail_lbl.configure(state="disabled")
            return
        # PERF-003 (wave 3): bounded batching, not one of the two extremes.
        # Per-fragment inserts cost 7 Tcl crossings per task (measured 62 ms at
        # 5,000 tasks); one monolithic string is unbounded memory for a 32 MiB
        # note. Accumulate fragments until DETAIL_BATCH_CHARS is pending, then
        # issue exactly one insert. Output is character-for-character identical.
        buf = []
        pending = 0
        insert = self.detail_lbl.insert

        def flush():
            nonlocal pending
            if buf:
                insert("end", "".join(buf))
                del buf[:]
                pending = 0

        def emit(fragment):
            nonlocal pending
            buf.append(fragment)
            pending += len(fragment)
            if pending >= DETAIL_BATCH_CHARS:
                flush()

        for idx, task in enumerate(items, 1):
            emit(f"{idx}. {task.title}\n")
            emit(f"   kind: {task.kind} | priority: {task.priority} | done: {task.done}\n")
            if task.time:
                emit(f"   time: {task.time}\n")
            if task.note:
                emit("   note: ")
                note = task.note
                # A single huge note is streamed through the SAME bounded
                # buffer, so peak transient Python memory stays capped.
                for start in range(0, len(note), DETAIL_BATCH_CHARS):
                    emit(note[start:start + DETAIL_BATCH_CHARS])
                emit("\n")
            emit("\n")
        flush()
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
        # CORE-005: selected_day is part of the persisted state payload, so a
        # real change IS a durable mutation and must advance the generation on
        # the next save. Without this, two instances could overwrite the field
        # at the same generation with no stale-writer detection. Selecting the
        # already-selected day returned above, so this is never a false dirty.
        self._dirty = True
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
        self._set_edit_message("")
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

    def _set_edit_message(self, text):
        """W2-003: concise, non-modal validation feedback inside the editor."""
        try:
            self.edit_msg.config(text=text)
        except (AttributeError, tk.TclError):
            pass

    def _editor_draft(self):
        """Snapshot every editor field so a conflict can restore the draft."""
        return {
            "editing_idx": self.editing_idx,
            "title": self.edit_title.get(),
            "time": self.edit_time.get(),
            "note": self.edit_note.get("1.0", "end-1c"),
            "kind": self.edit_kind.get(),
            "priority": self.edit_priority.get(),
        }

    def _restore_editor_draft(self, draft, message=""):
        """CORE-001: re-enter the editor with the user's exact typed draft.

        A stale-writer rejection reloads another instance's snapshot; the local
        edit was never persisted and must not be thrown away silently.
        """
        idx = draft.get("editing_idx")
        if idx is not None:
            items = self.tasks.get(self._task_key(), [])
            if not (isinstance(idx, int) and 0 <= idx < len(items)):
                # The row this edit targeted no longer exists in the winning
                # snapshot: keep the text, but commit it as a new task.
                idx = None
        self.is_editing = True
        self.editing_idx = idx
        self.view_frame.pack_forget()
        self.edit_frame.pack(fill="both", expand=True)
        self.edit_title.delete(0, "end")
        self.edit_title.insert(0, draft.get("title", ""))
        self.edit_time.delete(0, "end")
        self.edit_time.insert(0, draft.get("time", ""))
        self.edit_note.delete("1.0", "end")
        self.edit_note.insert("1.0", draft.get("note", ""))
        self.edit_kind.set(draft.get("kind") or "task")
        self.edit_priority.set(draft.get("priority") or "normal")
        self.side_title.config(text="Edit Task" if idx is not None else "Add Task")
        self._set_edit_message(message)
        try:
            self.edit_title.focus_set()
        except tk.TclError:
            pass

    def commit_task(self):
        title = self.edit_title.get().strip()
        if not title:
            # W2-003: a blank required field is a VALIDATION failure, not an
            # implicit Cancel. The previous behaviour called cancel_task(),
            # which destroyed a fully typed time/note/kind/priority draft with
            # no warning. Only explicit Cancel/Esc discards.
            self._set_edit_message("Title is required -- nothing was saved.")
            try:
                self.edit_title.focus_set()
            except tk.TclError:
                pass
            return

        draft = self._editor_draft()
        time_str = self.edit_time.get().strip()
        note = self.edit_note.get("1.0", "end-1c").strip()
        kind = self.edit_kind.get().strip().lower() or "task"
        priority = self.edit_priority.get().strip().lower() or "normal"

        key = self._task_key()
        # CORE-004: on the edit path, carry the existing task's completion
        # state forward; only brand-new tasks start incomplete. Never let an
        # edit silently mark a finished task as not-done.
        prev = self.tasks[key][self.editing_idx] if self.editing_idx is not None else None
        done = bool(prev.done) if prev is not None else False
        task = CalendarTask(title=title, time=time_str, note=note, kind=kind, priority=priority, done=done)

        # CORE-003: capture pre-mutation state so a failed save can roll back
        # the in-memory change rather than present a successful edit that
        # never reached disk.
        if self.editing_idx is not None:
            self.tasks[key][self.editing_idx] = task
            rollback = lambda: self.tasks[key].__setitem__(self.editing_idx, prev)
        else:
            self.tasks.setdefault(key, []).append(task)
            rollback = lambda: self.tasks[key].pop()

        prev_dirty = self._dirty
        self._dirty = True
        res = self.save()
        if res is STALE_WRITER:
            # CORE-001: STALE_WRITER is NOT success. The disk snapshot has been
            # replaced by another instance's, so `rollback()` would index a list
            # that no longer exists -- and the old truthiness check fell through
            # here as if the task had been written. Keep the draft, re-enter the
            # editor, and let the user re-commit against the winning snapshot.
            self._restore_editor_draft(
                draft,
                "Another instance saved newer data. Your draft was kept -- press Save again.",
            )
            self._update_day_visuals(self.selected_day)
            return
        if res is not True:
            self._dirty = prev_dirty
            rollback()
            self._set_edit_message("Save failed -- your draft was kept.")
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
        self._set_edit_message("")
        self.edit_frame.pack_forget()
        self.view_frame.pack(fill="both", expand=True)
        self.side_title.config(text="Day details")
        self.root.focus_set()
        # CORE-002: a reload that arrived mid-edit deferred its full render;
        # the editor no longer owns the panel, so finish it now.
        self._flush_pending_reconcile()

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
        prev_dirty = self._dirty
        self._dirty = True
        res = self.save()
        if res is STALE_WRITER:
            # CORE-001: the runtime now holds the winner's snapshot; restoring
            # our deleted item into it would resurrect a row the winner does not
            # have. Report the conflict instead of implying the delete committed.
            self._notify_stale_reload("The deletion was not saved")
            self._update_day_visuals(self.selected_day)
            self._render_side()
            return
        if res is not True:
            self._dirty = prev_dirty
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
        prev_dirty = self._dirty
        self._dirty = True
        res = self.save()
        if res is STALE_WRITER:
            # CORE-001: `items` came from the pre-reload model; the reloaded
            # snapshot owns the task list now. Do not claim the toggle stuck.
            self._notify_stale_reload("The change was not saved")
            self._update_day_visuals(self.selected_day)
            self._render_side()
            return
        if res is not True:
            self._dirty = prev_dirty
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
        prev_dirty = self._dirty
        self._dirty = True
        res = self.save()
        if res is STALE_WRITER:
            # CORE-001 + CORE-002: the reload replaced `self.settings` with the
            # winner's, which may itself carry a different focus_mode. Restoring
            # our own previous visual would contradict the loaded model, so
            # reconcile the runtime from the authoritative settings instead.
            self.reconcile_runtime_from_settings()
            self._notify_stale_reload("Focus mode was not saved")
            return
        if res is not True:
            self._dirty = prev_dirty
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

    def _notify_stale_reload(self, what):
        """One place says "another instance won" -- never silence, never success."""
        try:
            messagebox.showwarning(
                "Data reloaded",
                f"Another instance saved newer data. {what}; the current view was "
                "reloaded from disk. Re-apply your change if you still want it.",
                parent=self.root,
            )
        except tk.TclError:
            pass

    def _apply_focus_visual(self, active: bool, capture: bool = True):
        if active:
            if capture:
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

    def _commit_settings(self, candidate):
        """Run the settings change pipeline against ``candidate`` (a full
        settings dict). Applies runtime/visual effects, persists, and rolls
        everything back on failure. CORE-006: the candidate is the complete
        settings dict, so reset can submit DEFAULT_SETTINGS in full. W2-005:
        marks the model dirty so the change is actually persisted.
        """
        changed = {k: v for k, v in candidate.items() if self.settings.get(k) != v}
        if not changed:
            # No-op: clear any staged color draft and leave state untouched.
            self._draft_colors = {}
            return True
        changed_keys = set(changed)
        style_keys = (
            {"theme", "compact_header", "font_family", "font_mono",
             "font_title_size", "font_body_size", "font_small_size",
             "font_day_size", "font_day_bold"}
            | {k for k in candidate if k.startswith("color_")}
        )
        geom_keys = {"week_start_monday", "show_week_numbers", "cell_gap", "cell_padding"}
        need_style = bool(changed_keys & style_keys)
        need_geom = bool(changed_keys & geom_keys)

        prev_settings = self.settings
        prev_focus_fs = self._pre_focus_fs
        prev_dirty = self._dirty
        self._dirty = True
        self.settings = candidate
        try:
            if "always_on_top" in changed_keys:
                self.root.attributes("-topmost", candidate["always_on_top"])
            if "fullscreen_start" in changed_keys:
                # W2-006: while Focus is active, focus mode owns the live
                # fullscreen attribute. A fullscreen_start change updates the
                # deferred restore target so exiting Focus restores the user's
                # newly requested state, not the pre-focus snapshot.
                if candidate.get("focus_mode", False):
                    self._pre_focus_fs = bool(candidate["fullscreen_start"])
                else:
                    self.root.attributes("-fullscreen", candidate["fullscreen_start"])
            if "focus_mode" in changed_keys:
                if candidate.get("focus_mode", False):
                    self._apply_focus_visual(True)
                else:
                    # CORE-006: exiting Focus must restore the fullscreen state
                    # the user actually requested, not the stale pre-focus one.
                    self._pre_focus_fs = candidate.get("fullscreen_start", True)
                    self._apply_focus_visual(False)
            if "show_clock" in changed_keys:
                self._start_clock()
            if need_style:
                self._build_style()
            res = self.save()
            if res is STALE_WRITER:
                # Another instance committed newer settings; state was reloaded
                # from disk. W2-004: reconcile the runtime from that
                # authoritative model -- the staged effects above belong to a
                # candidate that never reached disk.
                self._draft_colors = {}
                self.reconcile_runtime_from_settings()
                self._notify_stale_reload("The settings change was not saved")
                return False
            if res is not True:
                # Persistence failed: restore the model, then reconcile every
                # runtime effect from it through the ONE shared path (W2-004).
                self.settings = prev_settings
                self._dirty = prev_dirty
                self._pre_focus_fs = prev_focus_fs
                self.reconcile_runtime_from_settings()
                try:
                    messagebox.showerror(
                        "Save failed",
                        "Could not write settings to disk; the change was rolled back.",
                        parent=self.root,
                    )
                except tk.TclError:
                    pass
                return False
        except Exception:
            # W2-004: the old handler restored only `settings` and `_dirty`, so a
            # TclError raised after `-topmost` had been applied left the live
            # window contradicting the model it had just reverted. Reconcile the
            # full runtime from the restored model, THEN re-raise: rollback is
            # not the same act as hiding a programmer error.
            self.settings = prev_settings
            self._dirty = prev_dirty
            self._pre_focus_fs = prev_focus_fs
            try:
                self.reconcile_runtime_from_settings()
            except Exception:
                pass
            raise
        # Success: clear the staged color draft and refresh presentation.
        self._draft_colors = {}
        if need_geom or need_style:
            self._refresh_all()
        return True

    def apply_settings(self, silent=False):
        # W2-006: build the candidate from the current live settings plus the
        # panel fields and any staged (draft) colors, then run one authoritative
        # transaction. The candidate is a full settings dict so the shared
        # pipeline can diff/apply/reconcile uniformly.
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
        ok = self._commit_settings(candidate)
        if ok and not silent and self.show_settings_panel:
            self._show_settings_panel()
        return ok

    def reset_settings(self):
        # CORE-006: submit the complete DEFAULT_SETTINGS through one
        # authoritative transaction so every setting (including focus_mode,
        # theme, lang and compact_header, which the exposed panel does not
        # represent) is reconciled to its default. Reconciles focus/fullscreen/
        # topmost/clock/style/grid from the full candidate and rolls back on
        # persistence failure.
        candidate = DEFAULT_SETTINGS.copy()
        ok = self._commit_settings(candidate)
        if ok and self.show_settings_panel:
            self._sync_settings_vars()
            self._show_settings_panel()
        return ok

    def _nav_guard(self):
        """Refuse calendar-date mutation while an editor session is active."""
        return self.is_editing

    def _navigate_to(self, y, m, day=None):
        """W2-005: one candidate-then-commit navigation primitive.

        Domain validation happens FIRST, and `_dirty` is set only after the
        persisted state actually changed. The old methods marked dirty before
        checking the boundary, so `prev_month()` at year 1 advanced the disk
        generation for an unchanged snapshot -- manufacturing a writer event that
        could force another current instance through stale-writer recovery.
        """
        if not (date.min.year <= y <= date.max.year):
            return False
        if not (1 <= m <= 12):
            return False
        try:
            max_day = calendar.monthrange(y, m)[1]
        except (ValueError, OverflowError):
            return False
        candidate_day = self.selected_day if day is None else day
        candidate_day = max(1, min(int(candidate_day), max_day))
        if (y, m, candidate_day) == (self.current.year, self.current.month, self.selected_day):
            # Genuine no-op: no dirty transition, no generation advance.
            return False
        self.current = date(y, m, 1)
        self.selected_day = candidate_day
        self._dirty = True
        self._reset_selection_cache()
        self._refresh_all()
        return True

    def prev_month(self):
        if self._nav_guard():
            return
        y, m = self.current.year, self.current.month
        if m == 1:
            y, m = y - 1, 12
        else:
            m -= 1
        self._navigate_to(y, m)

    def next_month(self):
        if self._nav_guard():
            return
        y, m = self.current.year, self.current.month
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
        self._navigate_to(y, m)

    def prev_year(self):
        if self._nav_guard():
            return
        self._navigate_to(self.current.year - 1, self.current.month)

    def next_year(self):
        if self._nav_guard():
            return
        self._navigate_to(self.current.year + 1, self.current.month)

    def go_today(self):
        if self._nav_guard():
            return
        t = date.today()
        self._navigate_to(t.year, t.month, t.day)

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
        # W2-005: a clean instance (nothing diverged from the last successful
        # save/load) does not advance the generation, so it cannot invalidate
        # another instance or create a false conflict. A dirty instance advances
        # generation exactly once. PERF-001 turns the clean case into a true
        # no-op when the file on disk is still the one we validated.
        if not self._dirty:
            return self._save(advance=False)
        return self._save(advance=True)

    def _preservation_ok(self):
        """W2-001: is DATA_PATH writable at all?

        `_load_failed` was only ever a warning flag; this is the authorization.
        When the load could not represent persisted bytes, an immutable snapshot
        MUST exist before the reduced model may replace the original. A retry is
        attempted first, because a transient quarantine failure (a full backup
        namespace, a momentary permission problem) should not permanently brick
        saving once the obstacle is gone.
        """
        if not self._write_blocked:
            return True
        if self._preservation_required and self._quarantine_file():
            self._write_blocked = False
            self._write_block_reason = None
            return True
        return False

    def _latch_write_block(self, reason):
        """Fail closed: record WHY the original file may not be replaced."""
        self._preservation_required = True
        self._write_blocked = True
        self._write_block_reason = reason

    def _require_preservation(self, reason):
        """Demand an immutable snapshot; latch fail-closed if none can be made."""
        self._preservation_required = True
        if not self._quarantine_file():
            self._latch_write_block(reason)
            return False
        return True

    def manual_save(self):
        # W2-004: explicit user-requested Save (toolbar button + 's' shortcut).
        # Surfaces exactly one failure message when persistence fails; never
        # claims success. A clean save that wrote nothing is not an error.
        res = self.save()
        if res is STALE_WRITER:
            self._notify_stale_reload("Your latest change was not saved")
            return
        if res is not True:
            try:
                messagebox.showerror(
                    "Save failed",
                    self._save_failure_text(),
                    parent=self.root,
                )
            except tk.TclError:
                pass

    def _save_failure_text(self):
        if self._write_blocked:
            return (
                "Saving is disabled: the damaged data file could not be backed "
                f"up ({self._write_block_reason or 'unknown reason'}), so replacing "
                "it would destroy the only copy of the unrecovered records."
            )
        return "Could not write data to disk. Your latest change was not saved."

    def _snapshot_identity(self):
        """PERF-001: cheap identity of the current DATA_PATH snapshot.

        File id + device + size + nanosecond mtime/ctime. Deliberately NOT
        `(size, mtime)` alone: a same-size replacement inside one timestamp tick
        would then read as unchanged and let an external writer escape stale
        detection. Returns None when identity cannot be established, which the
        caller treats as "take the authoritative slow path".
        """
        try:
            st = DATA_PATH.stat()
        except OSError:
            return None
        ino = getattr(st, "st_ino", 0)
        dev = getattr(st, "st_dev", 0)
        if not ino:
            # No usable file identity on this filesystem: refuse the fast path
            # rather than trusting timestamps alone.
            return None
        return (ino, dev, st.st_size, st.st_mtime_ns, getattr(st, "st_ctime_ns", 0))

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
            return _parse_generation(payload.get("generation", 0))
        except (TypeError, ValueError, OverflowError) as exc:
            raise UnreadableDataFile(f"invalid generation: {exc}") from exc

    def _save(self, advance=True):
        """Persist state (see save() for the clean/dirty gating). Returns True
        on success, False on failure, or the STALE_WRITER sentinel when another
        instance committed newer data. CORE-002: lock acquisition failures
        return False without entering the critical section.
        """
        # W2-001: the write barrier is checked before the lock is even taken.
        if not self._preservation_ok():
            return False
        try:
            with _save_lock(DATA_PATH):
                return self._save_locked(advance)
        except _LockAcquisitionFailure:
            return False
        except _StaleWriter:
            self._reload_from_disk()
            return STALE_WRITER

    def _reclaim_orphan_temps(self, keep=None):
        """PERF-005: delete crash-abandoned atomic-write candidates.

        Only legal while `_save_lock` is held: the lock is global to every
        cooperative writer, so no live writer can own one of these paths right
        now. Matches the exact prefix AND suffix in DATA_PATH's own directory --
        never DATA_PATH, never a `.corrupt*.bak` snapshot, never the `.lock`
        file, never an unrelated temp file. Best-effort: a file we cannot remove
        is left alone and never authorizes unsafe persistence.
        """
        try:
            entries = list(DATA_PATH.parent.glob(TMP_PREFIX + "*" + TMP_SUFFIX))
        except OSError:
            return
        for p in entries:
            if keep is not None and str(p) == str(keep):
                continue
            if not (p.name.startswith(TMP_PREFIX) and p.name.endswith(TMP_SUFFIX)):
                continue
            try:
                if p.is_file():
                    p.unlink()
            except OSError:
                pass

    def _save_locked(self, advance=True):
        try:
            # PERF-001: is the file on disk still the exact snapshot this
            # instance last loaded or wrote? If so its generation is already
            # known and no O(file-size) decode+parse is needed. Any doubt --
            # unknown identity, changed identity, active recovery state -- falls
            # through to the authoritative slow path, so an external writer can
            # never escape stale detection by matching a weak signature.
            identity = self._snapshot_identity()
            fast_path = (
                identity is not None
                and self._disk_identity is not None
                and identity == self._disk_identity
                and not self._preservation_required
                and not self._write_blocked
                and not self._load_failed
            )
            if fast_path:
                if not advance and not self._dirty:
                    # A clean instance over an unchanged file: a true no-op.
                    # Serializing the whole payload here was pure cost (measured
                    # 71 ms / 16 MiB transient on an 8 MiB dataset) and, worse,
                    # W2-001 proved it could overwrite unpreserved bytes.
                    return True
                disk_gen = self._generation
            else:
                try:
                    disk_gen = self._read_disk_generation()
                except UnreadableDataFile as exc:
                    # W2-001: the present file cannot be understood. It may only
                    # be replaced once its bytes are preserved.
                    if not self._require_preservation(
                        "backup of the unreadable data file failed: %s" % exc
                    ):
                        return False
                    disk_gen = None
            if disk_gen is not None and disk_gen != self._generation:
                raise _StaleWriter()
            if disk_gen is None:
                next_gen = self._generation + 1
            else:
                next_gen = self._generation + 1 if advance else self._generation
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
            # PERF-005: reclaim earlier crash orphans while we hold the lock.
            self._reclaim_orphan_temps()
            fd, tmp_path = tempfile.mkstemp(
                dir=str(DATA_PATH.parent), prefix=TMP_PREFIX, suffix=TMP_SUFFIX
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
                self._dirty = False
                # PERF-001: this instance is now the last known writer.
                self._disk_identity = self._snapshot_identity()
                return True
            except Exception:
                try: os.unlink(tmp_path)
                except OSError: pass
                return False
        except (OSError, TypeError, ValueError, OverflowError):
            return False

    def _quarantine_file(self):
        """Preserve a damaged/undecodable data file before any replacement.

        W2-001: snapshots are immutable / no-clobber. Each damaged source is
        copied into a unique sibling path (exclusive-create sequence) so a
        later corruption incident can never overwrite the only remaining copy
        of earlier recoverable user data. The exact snapshot path is recorded
        in ``_quarantine_path``. If the snapshot cannot be created, the damaged
        source and every older recovery file are left untouched and the caller
        must refuse the replacement.
        """
        if not DATA_PATH.exists():
            return True
        try:
            import shutil
            stem = DATA_PATH.name + ".corrupt"
            candidate = None
            for i in range(1000):
                suffix = ".bak" if i == 0 else f".{i:03d}.bak"
                p = DATA_PATH.with_name(stem + suffix)
                try:
                    fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except FileExistsError:
                    continue
                os.close(fd)
                candidate = p
                break
            if candidate is None:
                return False
            shutil.copy2(str(DATA_PATH), str(candidate))
            self._quarantine_path = candidate
            return True
        except OSError:
            return False

    def _reload_from_disk(self):
        """CORE-003: reload the current on-disk snapshot after a stale-writer
        rejection so the runtime matches the winner and the next save can
        commit.

        CORE-002: the model is not the runtime. Reload used to update settings
        and then replay only `_apply_window_mode`, leaving style, focus packing
        and the clock derived from the LOSING snapshot -- so the settings could
        say focus mode was active while every panel was still packed. One
        reconciliation path now owns that, and an active editor keeps its draft
        while the render half is deferred to `cancel_task`.
        """
        self._reset_selection_cache()
        self._load()
        self._dirty = False
        self.reconcile_runtime_from_settings(render=not self.is_editing)

    def _decode_snapshot(self):
        """W2-002: decode DATA_PATH into a COMPLETE fresh candidate snapshot.

        Returns the candidate dict, or None when DATA_PATH does not exist.
        Touches no instance model state: every section starts from documented
        defaults (`DEFAULT_SETTINGS.copy()`, empty tasks, today's date policy,
        generation 0) so identical bytes decode to an identical model no matter
        what this instance happened to be holding. The previous merge-into-live
        implementation made `_load` history-dependent: a stale-writer reload
        could keep the LOSER's `cell_gap`/font sizes for any key the winning
        snapshot omitted, and later write them back over the newer file.

        Structural corruption is reported, never silently defaulted: a present
        settings/state value of the wrong type is partial recovery requiring
        preservation, while a MISSING section is ordinary backward compatibility.
        """
        if not DATA_PATH.exists():
            return None
        snap = {
            "settings": DEFAULT_SETTINGS.copy(),
            "tasks": {},
            "current": None,
            "selected_day": None,
            "generation": 0,
            "load_failed": False,
            "partial_recovery": False,
            "invalid_task_keys": [],
            "recovery_message": None,
            "preservation_required": False,
            "fatal": None,
        }
        try:
            raw_text = DATA_PATH.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            # W2-003: non-UTF-8 bytes are a recoverable failure, not a crash.
            snap["fatal"] = "the data file could not be decoded: %s" % exc
            snap["load_failed"] = True
            snap["preservation_required"] = True
            return snap
        try:
            payload = json.loads(raw_text)
        except (json.JSONDecodeError, ValueError) as exc:
            snap["fatal"] = "the data file is not valid JSON: %s" % exc
            snap["load_failed"] = True
            snap["preservation_required"] = True
            return snap
        raw_text = None  # PERF-006: release the decoded source early
        if not isinstance(payload, dict):
            snap["fatal"] = "the data file does not contain an object"
            snap["load_failed"] = True
            snap["preservation_required"] = True
            return snap

        # ---- settings -------------------------------------------------------
        if "settings" in payload:
            raw_settings = payload["settings"]
            if isinstance(raw_settings, dict):
                snap["settings"].update(normalize_settings(raw_settings))
            else:
                # CORE-004: present but structurally wrong. The old code skipped
                # it as if absent, and the next save rewrote the malformed
                # section as a normalized dict with no backup -- destroying the
                # only copy of whatever was there.
                snap["partial_recovery"] = True
                snap["preservation_required"] = True
                snap["recovery_message"] = (
                    "The 'settings' section was not an object; defaults were used "
                    "and the original file was preserved."
                )

        # ---- tasks ----------------------------------------------------------
        if "tasks" in payload:
            raw_tasks = payload["tasks"]
            if not isinstance(raw_tasks, dict):
                snap["partial_recovery"] = True
                snap["preservation_required"] = True
                snap["recovery_message"] = (
                    "The 'tasks' section was not an object; the original file was preserved."
                )
            else:
                loaded_tasks = {}
                for k, v in raw_tasks.items():
                    if not isinstance(k, str) or not isinstance(v, list):
                        # Non-string key or non-list bucket: unrepresentable.
                        snap["invalid_task_keys"].append(k)
                        snap["partial_recovery"] = True
                        snap["preservation_required"] = True
                        continue
                    # W2-003: shared key parser/normalizer, so the load path and
                    # the runtime key contract agree on what a real date is.
                    canonical = _canonical_task_key(k)
                    if canonical is None:
                        snap["invalid_task_keys"].append(k)
                        snap["partial_recovery"] = True
                        snap["preservation_required"] = True
                        continue
                    good = [x for x in v if isinstance(x, dict)]
                    if len(good) != len(v):
                        # At least one record cannot be represented losslessly.
                        snap["partial_recovery"] = True
                        snap["preservation_required"] = True
                    existing = loaded_tasks.get(canonical, [])
                    existing.extend(CalendarTask.from_dict(x) for x in good)
                    loaded_tasks[canonical] = existing
                snap["tasks"] = loaded_tasks
                if snap["partial_recovery"] and snap["recovery_message"] is None:
                    snap["recovery_message"] = (
                        "Some tasks could not be recovered; the original file was preserved."
                    )

        # ---- state ----------------------------------------------------------
        if "state" in payload:
            st = payload["state"]
            if isinstance(st, dict):
                snap["current"], snap["selected_day"] = _decode_state(st)
            else:
                snap["partial_recovery"] = True
                snap["preservation_required"] = True
                if snap["recovery_message"] is None:
                    snap["recovery_message"] = (
                        "The 'state' section was not an object; today's date was used "
                        "and the original file was preserved."
                    )
                snap["current"], snap["selected_day"] = _decode_state({})
        if snap["current"] is None:
            # Missing state section: documented default, NOT corruption.
            snap["current"], snap["selected_day"] = _decode_state({})

        # ---- generation -----------------------------------------------------
        try:
            snap["generation"] = _parse_generation(payload.get("generation", 0))
        except (TypeError, ValueError, OverflowError):
            # CORE-003: never coerce an ownership token. Preserve and restart.
            snap["generation"] = 0
            snap["partial_recovery"] = True
            snap["preservation_required"] = True
            snap["recovery_message"] = (
                "Invalid generation counter; the original file was preserved."
            )
        if snap["partial_recovery"]:
            snap["load_failed"] = True
        return snap

    def _load(self):
        """Decode the on-disk snapshot, then commit it atomically.

        W2-002: decode-then-commit, so the same bytes produce the same model on
        startup and on reload, and a failed decode never leaves a hybrid of the
        previous runtime and the new file.
        """
        snap = self._decode_snapshot()
        if snap is None:
            # No file yet: keep the constructor defaults (fresh dataset).
            self._disk_identity = None
            return
        # Recovery state always reflects THIS decode, not an older one.
        self._load_failed = snap["load_failed"]
        self._partial_recovery = snap["partial_recovery"]
        self._invalid_task_keys = list(snap["invalid_task_keys"])
        self._recovery_message = snap["recovery_message"]
        if snap["preservation_required"]:
            # W2-001: bytes were dropped or could not be represented. The
            # original file may only be replaced once an immutable snapshot of
            # it exists; if that snapshot cannot be created, saving is latched
            # closed instead of quietly overwriting the sole copy later.
            reason = "no backup of the damaged data file could be created"
            self._require_preservation(reason)
        if snap["fatal"] is not None:
            # Unreadable/undecodable file: start a fresh dataset but keep the
            # original preserved and the failure visible.
            self._recovery_message = snap["fatal"]
            self._disk_identity = None
            return
        self.settings = snap["settings"]
        self.tasks = snap["tasks"]
        self.current = snap["current"]
        self.selected_day = snap["selected_day"]
        self._generation = snap["generation"]
        self._loaded_generation = self._generation
        # PERF-001: remember exactly which snapshot this model came from.
        self._disk_identity = self._snapshot_identity()

    def _apply_state(self, st):
        """Compatibility shim: apply a decoded `state` section to the model."""
        self.current, self.selected_day = _decode_state(st)

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
        # CORE-001: route shutdown through the public dirty-aware contract.
        # `_save()` bypassed it, so a clean exit advanced the generation for a
        # snapshot nothing had changed -- manufacturing future stale-writer
        # conflicts for other instances -- and a truthy STALE_WRITER destroyed
        # the window while the user's unsaved state was still in memory.
        res = self.save()
        if res is True:
            self.root.destroy()
            return
        if res is STALE_WRITER:
            # Another instance won. The local model has been replaced by theirs,
            # so quitting silently would discard whatever the user had. Only an
            # explicit choice may end the process here.
            choice = messagebox.askyesnocancel(
                "Data reloaded",
                "Another instance saved newer data, so your latest change was not "
                "saved. The view was reloaded from disk.\n\n"
                "Quit anyway and discard your change?",
                parent=self.root,
            )
            if choice:
                self.root.destroy()
            return
        choice = messagebox.askyesnocancel(
            "Save failed",
            self._save_failure_text() + "\n\nQuit without saving?",
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