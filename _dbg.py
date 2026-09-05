import re
src = open("ZEN_CALENDAR.py", encoding="utf-8").read()
fix = open("_fix_audit.py", encoding="utf-8").read()

m = re.search(r"# --- R_apply_settings.*?add\(\n'''(.*?)''',\n'''", fix, re.S)
old = m.group(1)
print("OLD total lines:", old.count("\n") + 1)
idx = src.find(old)
print("exact find idx:", idx)
if idx == -1:
    olines = old.split("\n")
    for i in range(len(olines), 0, -1):
        pref = "\n".join(olines[:i])
        if src.find(pref) != -1:
            print("longest matching prefix lines:", i)
            print("FIRST DIVERGENT OLD LINE:", repr(olines[i]))
            pidx = src.find(pref)
            print("REAL TEXT AT THAT POINT:", repr(src[pidx + len(pref):pidx + len(pref) + 200]))
            break
