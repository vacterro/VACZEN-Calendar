t = open("ZEN_CALENDAR.py", encoding="utf-8").read()
BS = chr(92)  # backslash
print("literal backslash-u25cf tokens:", t.count(BS + "u25cf"))
print("bullet glyph count:", t.count(chr(0x25CF)))
for marker in ["_reload_from_disk", "_commit_settings", "def manual_save",
               "_StaleWriter", "_LockAcquisitionFailure", "STALE_WRITER",
               "_dirty", "_selection_owner_key", "_invalid_task_keys",
               "_partial_recovery", "_load_failed", "_parse_generation",
               "_SURROGATE_RE"]:
    print(f"has {marker}:", marker in t)
# sanity: duplicate _bind_day_widget should be gone (def appears once)
print("def _bind_day_widget count:", t.count("def _bind_day_widget"))
print("def _load count:", t.count("def _load(self):"))
print("def _save_locked count:", t.count("def _save_locked"))
