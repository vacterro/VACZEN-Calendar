import io, sys

PATH = r"V:\___VAC\__K\__CODE\_PY\_VACZEN_CALENDAR\ZEN_CALENDAR.py"

with open(PATH, "r", encoding="utf-8") as f:
    src = f.read()

repls = []

def add(old, new):
    repls.append((old, new))

# --- R_surrogate: _SURROGATE_RE (PERF-002) ---
add(
'''_TASK_KEY_RE = re.compile(r"^\\s*(\\d{1,4})-(\\d{1,2})-(\\d{1,2})\\s*$")''',
'''_TASK_KEY_RE = re.compile(r"^\\s*(\\d{1,4})-(\\d{1,2})-(\\d{1,2})\\s*$")

# PERF-002: precompiled surrogate-range search used by sanitize_text to take
# the fast (no copy) path for valid Unicode.
_SURROGATE_RE = re.compile(r"[\\ud800-\\udfff]")'''
)

# --- R_parse_gen: add _parse_generation after _is_non_finite (CORE-007) ---
add(
'''def _is_non_finite(v):
    if isinstance(v, float):
        return v != v or v in (float("inf"), float("-inf"))
    return False''',
'''def _is_non_finite(v):
    if isinstance(v, float):
        return v != v or v in (float("inf"), float("-inf"))
    return False


def _parse_generation(raw):
    """Shared generation parser for load and save-side reads (CORE-007).

    Missing generation defaults to 0. Only non-negative integers are valid;
    negative, non-finite, or non-integer values are rejected so both readers
    agree exactly and an invalid generation routes through the damaged-file
    recovery path instead of being silently normalized differently per side.
    """
    gen = int(raw)
    if _is_non_finite(gen) or gen < 0:
        raise ValueError("invalid generation")
    return gen'''
)

# --- R_readgen: use _parse_generation (CORE-007) ---
add(
'''        if not isinstance(payload, dict):
            raise UnreadableDataFile("top-level payload is not an object")
        try:
            return int(payload.get("generation", 0))
        except (TypeError, ValueError, OverflowError) as exc:
            raise UnreadableDataFile(f"invalid generation: {exc}") from exc''',
'''        if not isinstance(payload, dict):
            raise UnreadableDataFile("top-level payload is not an object")
        try:
            return _parse_generation(payload.get("generation", 0))
        except (TypeError, ValueError, OverflowError) as exc:
            raise UnreadableDataFile(f"invalid generation: {exc}") from exc'''
)

# --- R_sanitize fast path (PERF-002) ---
add(
'''    if not isinstance(s, str):
        return s
    return s.encode("utf-16", "surrogatepass").decode("utf-16", "replace")''',
'''    if not isinstance(s, str):
        return s
    # PERF-002: the UTF-16 sanitize pass only matters when a lone surrogate is
    # actually present. Skip the encode/decode (and its ~3x transient
    # allocation) for the common case of valid Unicode so large notes do not
    # pay the copy-amplification penalty on every load/render.
    if _SURROGATE_RE.search(s) is None:
        return s
    return s.encode("utf-16", "surrogatepass").decode("utf-16", "replace")'''
)

# --- R_init flags ---
add(
'''        self._clock_after_id = None
        self._selected_task_idx = None

        self._load()''',
'''        self._clock_after_id = None
        self._selected_task_idx = None
        self._selection_owner_key = None
        self._invalid_task_keys = []
        self._partial_recovery = False
        self._recovery_message = None
        self._dirty = False

        self._load()'''
)

# --- R_dup_bind: delete first _bind_day_widget (CORE-009) ---
add(
'''    def _bind_day_widget(self, widget, day_num):
        widget.bind("<Button-1>", lambda e, d=day_num: self.select_day(d))

    def _ensure_calendar_pool(self):''',
'''    def _ensure_calendar_pool(self):'''
)

# --- R_render_reset: remove badge/dots None resets (CORE-005) ---
add(
'''                # Reset the slot to a fresh state.
                slot["day_num"] = day_num
                slot["badge"] = None
                slot["dots"] = None
                try:
                    slot["cell"].pack_forget()
                    slot["empty"].pack_forget()
                except tk.TclError:
                    pass''',
'''                # Reset the slot to a fresh state.
                slot["day_num"] = day_num
                try:
                    slot["cell"].pack_forget()
                    slot["empty"].pack_forget()
                except tk.TclError:
                    pass'''
)

# --- R_render_empty: hide indicators for day_num==0 (CORE-005) ---
add(
'''                if day_num == 0:
                    slot["empty"].pack(fill="both", expand=True)
                    continue''',
'''                if day_num == 0:
                    slot["empty"].pack(fill="both", expand=True)
                    if slot["badge"] is not None:
                        try: slot["badge"].pack_forget()
                        except tk.TclError: pass
                    if slot["dots"] is not None:
                        try: slot["dots"].pack_forget()
                        except tk.TclError: pass
                    continue'''
)

# --- R_render_badge: create-once badge/dots (CORE-005) ---
add(
'''                task_count = len(self.tasks.get(self._task_key(day_num), []))
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
                    dots.configure(text="\\u25cf " * min(task_count, 4), bg=bg, fg=task_dot, font=self._font(self.settings["font_small_size"]))
                    dots.pack(anchor="w", pady=(4, 0))

                self._day_widgets[day_num] = {''',
'''                task_count = len(self.tasks.get(self._task_key(day_num), []))
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
                    dots.configure(text="\\u25cf " * min(task_count, 4), bg=bg, fg=task_dot,
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

                self._day_widgets[day_num] = {'''
)

# --- R_update_visuals: ownership sync (CORE-005) ---
add(
'''        task_count = len(self.tasks.get(self._task_key(day_num), []))
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
            dots.configure(text="\\u25cf " * min(task_count, 4), bg=bg, fg=task_dot, font=small)
        else:
            if badge is not None:
                badge.destroy()
                info["badge"] = None
            if dots is not None:
                dots.destroy()
                info["dots"] = None''',
'''        task_count = len(self.tasks.get(self._task_key(day_num), []))
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
            dots.configure(text="\\u25cf " * min(task_count, 4), bg=bg, fg=task_dot, font=small)
            dots.pack(anchor="w", pady=(4, 0))
        else:
            # Hide (do not destroy) the slot-owned indicators; keep the same
            # persistent widget references in both info and slot (CORE-005).
            if badge is not None:
                try: badge.pack_forget()
                except tk.TclError: pass
            if dots is not None:
                try: dots.pack_forget()
                except tk.TclError: pass'''
)

# --- R_render_side owner (W2-003) ---
add(
'''        if (
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
        self._invalid_task_keys = []''',
'''        if (
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
        # (_invalid_task_keys) is persistent and must survive rendering (W2-002).'''
)

# --- R_detail_box bounded (PERF-003) ---
add(
'''    def _update_detail_box(self):
        key = self._task_key()
        items = self.tasks.get(key, [])
        self.detail_lbl.configure(state="normal")
        self.detail_lbl.delete("1.0", "end")
        if not items:
            self.detail_lbl.insert("end", "No tasks.\\n\\nA add\\nE edit\\nD delete\\nSpace done")
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
            self.detail_lbl.insert("end", "\\n".join(lines))
        self.detail_lbl.configure(state="disabled")''',
'''    def _update_detail_box(self):
        key = self._task_key()
        items = self.tasks.get(key, [])
        self.detail_lbl.configure(state="normal")
        self.detail_lbl.delete("1.0", "end")
        if not items:
            self.detail_lbl.insert("end", "No tasks.\\n\\nA add\\nE edit\\nD delete\\nSpace done")
            self.detail_lbl.configure(state="disabled")
            return
        # PERF-003: avoid building one unbounded Python document. Insert each
        # detail block directly; for very large notes stream the note text in
        # chunks so peak temporary memory is bounded regardless of note size
        # and the rendered text stays character-for-character identical.
        _CHUNK = 1 << 16  # 64 KiB
        for idx, task in enumerate(items, 1):
            self.detail_lbl.insert("end", f"{idx}. {task.title}\\n")
            self.detail_lbl.insert(
                "end",
                f"   kind: {task.kind} | priority: {task.priority} | done: {task.done}\\n",
            )
            if task.time:
                self.detail_lbl.insert("end", f"   time: {task.time}\\n")
            if task.note:
                self.detail_lbl.insert("end", "   note: ")
                note = task.note
                for start in range(0, len(note), _CHUNK):
                    self.detail_lbl.insert("end", note[start:start + _CHUNK])
                self.detail_lbl.insert("end", "\\n")
            self.detail_lbl.insert("end", "\\n")
        self.detail_lbl.configure(state="disabled")'''
)

# --- R_commit done (CORE-004) + dirty ---
add(
'''        kind = self.edit_kind.get().strip().lower() or "task"
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
            rollback = lambda: self.tasks[key].pop()''',
'''        kind = self.edit_kind.get().strip().lower() or "task"
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
            rollback = lambda: self.tasks[key].pop()'''
)

# --- R_commit save dirty ---
add(
'''        if not self.save():
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
        self.cancel_task()''',
'''        prev_dirty = self._dirty
        self._dirty = True
        if not self.save():
            self._dirty = prev_dirty
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
        self.cancel_task()'''
)

# --- R_delete save dirty ---
add(
'''        if not self.save():
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
            return''',
'''        prev_dirty = self._dirty
        self._dirty = True
        if not self.save():
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
            return'''
)

# --- R_done save dirty ---
add(
'''        if not self.save():
            items[idx].done = prev_done
            try:
                messagebox.showerror(
                    "Save failed",
                    "Could not write data to disk; the change was rolled back.",
                    parent=self.root,
                )
            except tk.TclError:
                pass
            return''',
'''        prev_dirty = self._dirty
        self._dirty = True
        if not self.save():
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
            return'''
)

# --- R_focus save dirty ---
add(
'''        self.settings["focus_mode"] = new
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
                pass''',
'''        self.settings["focus_mode"] = new
        self._apply_focus_visual(new)
        prev_dirty = self._dirty
        self._dirty = True
        if not self.save():
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
                pass'''
)

# --- R_bind_save button ---
add(
'''        self.btn_save = ttk.Button(self.act_btns, text="Save", style="Compact.TButton", command=self.save)''',
'''        self.btn_save = ttk.Button(self.act_btns, text="Save", style="Compact.TButton", command=self.manual_save)'''
)

# --- R_bind_s ---
add(
'''        self.root.bind("s", lambda e: None if _blocked() else self.save())''',
'''        self.root.bind("s", lambda e: None if _blocked() else self.manual_save())'''
)

# --- R_nav prev_month ---
add(
'''    def prev_month(self):
        if self._nav_guard():
            return
        y, m = self.current.year, self.current.month
        if m == 1:''',
'''    def prev_month(self):
        if self._nav_guard():
            return
        self._dirty = True  # W2-005: navigation changes persisted state
        y, m = self.current.year, self.current.month
        if m == 1:'''
)

# --- R_nav next_month ---
add(
'''    def next_month(self):
        if self._nav_guard():
            return
        y, m = self.current.year, self.current.month
        if m == 12:''',
'''    def next_month(self):
        if self._nav_guard():
            return
        self._dirty = True  # W2-005: navigation changes persisted state
        y, m = self.current.year, self.current.month
        if m == 12:'''
)

# --- R_nav prev_year ---
add(
'''    def prev_year(self):
        if self._nav_guard():
            return
        y = self.current.year - 1''',
'''    def prev_year(self):
        if self._nav_guard():
            return
        self._dirty = True  # W2-005: navigation changes persisted state
        y = self.current.year - 1'''
)

# --- R_nav next_year ---
add(
'''    def next_year(self):
        if self._nav_guard():
            return
        y = self.current.year + 1''',
'''    def next_year(self):
        if self._nav_guard():
            return
        self._dirty = True  # W2-005: navigation changes persisted state
        y = self.current.year + 1'''
)

# --- R_nav go_today ---
add(
'''    def go_today(self):
        if self._nav_guard():
            return
        t = date.today()''',
'''    def go_today(self):
        if self._nav_guard():
            return
        self._dirty = True  # W2-005: navigation changes persisted state
        t = date.today()'''
)

# --- R_save public gating + manual_save ---
add(
'''    def save(self):
        # CORE-003: surface persistence success/failure to callers; mutations
        # MUST know whether their state actually hit disk.
        return self._save()''',
'''    def save(self):
        # W2-005: a clean instance (nothing diverged from the last successful
        # save/load) still performs the locked write but WITHOUT advancing the
        # generation, so it cannot invalidate another instance or create a
        # false conflict. A dirty instance advances generation exactly once.
        if not self._dirty:
            return self._save(advance=False)
        return self._save(advance=True)

    def manual_save(self):
        # W2-004: explicit user-requested Save (toolbar button + 's' shortcut).
        # Surfaces exactly one failure message when persistence fails; never
        # claims success. A clean save that wrote nothing is not an error.
        res = self.save()
        if res is STALE_WRITER:
            try:
                messagebox.showwarning(
                    "Data reloaded",
                    "Another instance saved newer data. The current view was reloaded; re-apply your change if needed.",
                    parent=self.root,
                )
            except tk.TclError:
                pass
            return
        if res is not True:
            try:
                messagebox.showerror(
                    "Save failed",
                    "Could not write data to disk. Your latest change was not saved.",
                    parent=self.root,
                )
            except tk.TclError:
                pass'''
)

# --- R_save primitive advance ---
add(
'''    def _save(self):
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
            return self._save_locked()''',
'''    def _save(self, advance=True):
        """Persist state (see save() for the clean/dirty gating). Returns True
        on success, False on failure, or the STALE_WRITER sentinel when another
        instance committed newer data. CORE-002: lock acquisition failures
        return False without entering the critical section.
        """
        try:
            with _save_lock(DATA_PATH):
                return self._save_locked(advance)
        except _LockAcquisitionFailure:
            return False
        except _StaleWriter:
            self._reload_from_disk()
            return STALE_WRITER'''
)

# --- R_save_locked advance + stale raise + dirty clear ---
add(
'''    def _save_locked(self):
        try:
            try:
                disk_gen = self._read_disk_generation()
            except UnreadableDataFile:
                if not self._quarantine_file():
                    return False
                disk_gen = None
            if disk_gen is not None and disk_gen != self._generation:
                return False
            next_gen = self._generation + 1''',
'''    def _save_locked(self, advance=True):
        try:
            try:
                disk_gen = self._read_disk_generation()
            except UnreadableDataFile:
                if not self._quarantine_file():
                    return False
                disk_gen = None
            if disk_gen is not None and disk_gen != self._generation:
                raise _StaleWriter()
            if disk_gen is None:
                next_gen = self._generation + 1
            else:
                next_gen = self._generation + 1 if advance else self._generation'''
)

add(
'''                os.replace(tmp_path, str(DATA_PATH))
                self._generation = next_gen
                self._loaded_generation = next_gen
                return True''',
'''                os.replace(tmp_path, str(DATA_PATH))
                self._generation = next_gen
                self._loaded_generation = next_gen
                self._dirty = False
                return True'''
)

# --- R_quarantine no-clobber (W2-001) ---
add(
'''    def _quarantine_file(self):
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
            return False''',
'''    def _quarantine_file(self):
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
            return False'''
)

# --- R_load reset (CORE-001/007 start) ---
add(
'''    def _load(self):
        if not DATA_PATH.exists():
            return
        raw_text = None''',
'''    def _load(self):
        if not DATA_PATH.exists():
            return
        # Reset recovery state so a reload starts clean (used by CORE-003).
        self._load_failed = False
        self._partial_recovery = False
        self._invalid_task_keys = []
        self._recovery_message = None
        raw_text = None'''
)

# --- R_load gen (CORE-007) ---
add(
'''        gen = payload.get("generation", 0)
        try:
            self._generation = max(0, int(gen))
        except (TypeError, ValueError, OverflowError):
            self._generation = 0
        self._loaded_generation = self._generation''',
'''        gen = payload.get("generation", 0)
        try:
            self._generation = _parse_generation(gen)
        except (TypeError, ValueError, OverflowError):
            # Invalid/negative generation: preserve the original file via
            # quarantine and start clean (CORE-007).
            self._load_failed = True
            self._partial_recovery = True
            self._recovery_message = (
                "Invalid generation counter; the original file was preserved."
            )
            if not self._quarantine_file():
                self._load_failed = False
            self._generation = 0
        self._loaded_generation = self._generation'''
)

# --- R_load tasks (CORE-001 + W2-002) ---
add(
'''        raw_tasks = payload.get("tasks", {})
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
        st = payload.get("state", {})''',
'''        raw_tasks = payload.get("tasks", {})
        if not isinstance(raw_tasks, dict):
            # Wrong top-level shape for the tasks section: structural loss.
            # Preserve the original file and keep recovery state (CORE-001).
            self._partial_recovery = True
            self._recovery_message = (
                "The 'tasks' section was not an object; the original file was preserved."
            )
            self._load_failed = True
            self._quarantine_file()
        else:
            loaded_tasks = {}
            for k, v in raw_tasks.items():
                if not isinstance(k, str):
                    # Non-string key: unrecoverable; record for forensics.
                    self._invalid_task_keys.append(k)
                    self._partial_recovery = True
                    continue
                if not isinstance(v, list):
                    # Bucket is not a list: structural loss; preserve original.
                    self._invalid_task_keys.append(k)
                    self._partial_recovery = True
                    continue
                # W2-003: validate and canonicalize the task key. Shared with
                # _task_key so the load path and the runtime key contract
                # agree on what a real date looks like.
                canonical = _canonical_task_key(k)
                if canonical is None:
                    # Impossible / unrecoverable date key: keep it OUT of live
                    # tasks. The original file (with these buckets) is preserved
                    # via quarantine so the data stays recoverable (W2-002).
                    self._invalid_task_keys.append(k)
                    self._partial_recovery = True
                    continue
                good = [x for x in v if isinstance(x, dict)]
                if len(good) != len(v):
                    # At least one entry could not be represented losslessly.
                    self._partial_recovery = True
                existing = loaded_tasks.get(canonical, [])
                existing.extend(CalendarTask.from_dict(x) for x in good)
                loaded_tasks[canonical] = existing
            self.tasks = loaded_tasks
            if self._partial_recovery:
                # Preserve the sole copy of every rejected byte/record before
                # any subsequent rewrite (CORE-001): the quarantine snapshot
                # holds the original, untouched file.
                self._load_failed = True
                if self._recovery_message is None:
                    self._recovery_message = (
                        "Some tasks could not be recovered; the original file was preserved."
                    )
                self._quarantine_file()
        st = payload.get("state", {})'''
)

# --- R_reload_from_disk insert before _load ---
# Anchor only on the `_quarantine_file` tail + `def _load(self):` so it survives
# the earlier R_load reset edit (which injects lines between `return` and
# `raw_text = None` inside `_load`).
add(
'''        except OSError:
            return False

    def _load(self):''',
'''        except OSError:
            return False

    def _reload_from_disk(self):
        """CORE-003: reload the current on-disk snapshot after a stale-writer
        rejection so the runtime matches the winner and the next save can
        commit. Refreshes the UI without dropping an active editor draft.
        """
        self._reset_selection_cache()
        self._load()
        self._dirty = False
        if not self.is_editing:
            self._apply_window_mode()
            self._refresh_all()
        else:
            self._apply_window_mode()

    def _load(self):'''
)

# --- R_apply_settings/_commit_settings/reset_settings rewrite (CORE-006/008/006) ---
add(
'''    def apply_settings(self, silent=False):
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
        self.apply_settings()''',
'''    def _commit_settings(self, candidate):
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
                # from disk, so keep that rather than rolling back.
                return False
            if res is not True:
                # Persistence failed: revert runtime effects + in-memory state.
                self.settings = prev_settings
                self._dirty = prev_dirty
                if "always_on_top" in changed_keys:
                    self.root.attributes("-topmost", prev_settings.get("always_on_top", True))
                if "fullscreen_start" in changed_keys and not prev_settings.get("focus_mode", False):
                    self.root.attributes("-fullscreen", prev_settings.get("fullscreen_start", True))
                if "focus_mode" in changed_keys:
                    self._apply_focus_visual(prev_settings.get("focus_mode", False))
                if "show_clock" in changed_keys:
                    # CORE-008: restart/reconcile the clock against the restored
                    # setting so exactly one pending callback remains scheduled.
                    self._start_clock()
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
                return False
        except Exception:
            self.settings = prev_settings
            self._dirty = prev_dirty
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
        return ok'''
)

# ============ apply ============
# The target source embeds the literal bullet glyph "●" (U+25CF). The repl
# strings above carry it as the 7-char token backslash+u25cf; normalize both
# sides to the real character so exact matching works and the written file
# stays valid UTF-8.
TOKEN = "\\" + "u25cf"
BULLET = chr(0x25CF)
repls = [(o.replace(TOKEN, BULLET), n.replace(TOKEN, BULLET)) for o, n in repls]

# Re-check every replacement against the progressively-modified source so an
# earlier edit that shifts a later anchor fails loudly instead of silently
# doing nothing.
for i, (old, new) in enumerate(repls):
    cnt = src.count(old)
    if cnt != 1:
        print(f"REPL {i} FAILED at apply: count={cnt}")
        sys.exit(1)
    src = src.replace(old, new, 1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(src)

print(f"OK: applied {len(repls)} replacements")
