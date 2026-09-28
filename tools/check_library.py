"""Check that every symbol's pins match its footprint's pads.

Each symbol names its footprint as "Bergsonne Tiles:<package>". The footprint
must exist in Bergsonne Tiles.pretty, and the symbol's pin numbers must equal
the footprint's pad numbers exactly (unused pads are hidden no-connect pins, so
nothing is left over). KiCad itself checks that both libraries load; this
checks that they agree.

usage: python3 tools/check_library.py [repo root]
"""
import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "."
sym_path = os.path.join(root, "Bergsonne Tiles.kicad_sym")
fp_dir = os.path.join(root, "Bergsonne Tiles.pretty")

pads = {}
for f in sorted(os.listdir(fp_dir)):
    if f.endswith(".kicad_mod"):
        text = open(os.path.join(fp_dir, f)).read()
        pads[f[: -len(".kicad_mod")]] = set(re.findall(r'\(pad "([^"]+)"', text))

errors = []
count = 0
text = open(sym_path).read()
for m in re.finditer(r'^\t\(symbol "([^"]+)"(.*?)^\t\)', text, re.S | re.M):
    name, body = m.group(1), m.group(2)
    count += 1
    fp = re.search(r'\(property "Footprint" "([^"]*)"', body)
    fp = fp.group(1) if fp else ""
    lib, _, pkg = fp.partition(":")
    if lib != "Bergsonne Tiles" or pkg not in pads:
        errors.append(f"{name}: footprint '{fp}' is not in Bergsonne Tiles.pretty")
        continue
    pins = set(re.findall(r'\(number "([^"]+)"', body))
    if pins != pads[pkg]:
        missing = sorted(pads[pkg] - pins, key=lambda s: (len(s), s))
        extra = sorted(pins - pads[pkg], key=lambda s: (len(s), s))
        errors.append(f"{name} ({pkg}): pads without a pin {missing}, pins without a pad {extra}")

if count == 0:
    errors.append("no symbols found")
for e in errors:
    print("ERROR", e)
print(f"{count} symbols, {len(pads)} footprints, {len(errors)} errors")
sys.exit(1 if errors else 0)
