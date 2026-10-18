#!/usr/bin/env python3
"""Move an existing tile project to another fab tier, in place.

    python3 tools/set_tier.py  path/to/Tile.kicad_pro  2L-fine | 4L | 4L-fine | 4L-HDI
    python3 tools/set_tier.py  path/to/Tile.kicad_pro  4L --package T44-10   # project not made from a template

Close the project in KiCad first. --package names the tile package when the
project has no TILE_PACKAGE text variable (projects that predate the templates).
--ignore-locks skips the open-in-KiCad check when the lock files are stale. The script rewrites:
  .kicad_pro   design rules, netclasses, track/via presets, FAB_TIER / FAB_QUOTE
  .kicad_dru   generated rules (your own rules below the marker line are kept)
  .kicad_pcb   layer list and stackup (adds In1.Cu / In2.Cu when going to 4 layers,
               plus GND and +V planes if none exist), the order note, title block
  .kicad_sch   title block comment
A copy of the four files is saved in <project>-tier-backup-<old tier>-<time>/ first.
Going down in layer count is refused: delete inner-layer items by hand first.
"""
import datetime
import json
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import make_tile_templates as gen  # noqa: E402


def die(msg):
    sys.exit("set_tier: " + msg)


def match_paren(s, start):
    """Index just past the ')' closing the '(' at s[start]."""
    depth = 0
    in_str = False
    i = start
    while i < len(s):
        c = s[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    die("unbalanced s-expression")


def copper_layer_count(pcb):
    m = re.search(r"\n\t\(layers\n(.*?)\n\t\)\n", pcb, re.S)
    if not m:
        die("no layers block in board")
    return len(re.findall(r'\(\d+ "[A-Za-z0-9.]+Cu" signal\)', m.group(1)))


def update_board(pcb, pkg_name, pkg, tier_name, tier, notes):
    # --- layers: add inner layers when moving to 4
    if tier["layers"] == 4 and '"In1.Cu"' not in pcb:
        pcb = pcb.replace('\t\t(0 "F.Cu" signal)\n', '\t\t(0 "F.Cu" signal)\n\t\t(4 "In1.Cu" signal)\n\t\t(6 "In2.Cu" signal)\n', 1)
        notes.append("added In1.Cu and In2.Cu")
    # --- stackup: regenerate
    i = pcb.find("\t\t(stackup\n")
    if i < 0:
        die("no stackup block in board")
    j = match_paren(pcb, i + 2)
    pcb = pcb[:i] + gen.stackup_block(tier["layers"]).rstrip("\n") + pcb[j:]
    notes.append("stackup rewritten for %d layers" % tier["layers"])
    # --- planes
    if tier["layers"] == 4:
        nets = {name: int(num) for num, name in re.findall(r'\n\t\(net (\d+) "([^"]*)"\)', pcb)}
        tail = "\t(embedded_fonts no)\n)\n"
        if not pcb.rstrip().endswith("(embedded_fonts no)\n)".rstrip()) and tail not in pcb:
            die("unexpected end of board file")
        added = []
        for layer, net in (("In1.Cu", "GND"), ("In2.Cu", "+V")):
            has_zone = re.search(r'\(zone\n(?:.*\n)*?\t\t\(layer "%s"\)' % re.escape(layer), pcb)
            if has_zone:
                continue
            if net not in nets:
                notes.append("no net %s in the board, no plane added on %s" % (net, layer))
                continue
            z = gen.zone(nets[net], net, layer, pkg["outline"], tier["track"], gen.uid("set_tier", pkg_name, layer))
            pcb = pcb.replace(tail, z + tail)
            added.append("%s = %s" % (layer, net))
        if added:
            notes.append("planes added: " + ", ".join(added) + " (press B in the board editor to fill)")
    # --- order note
    new_note = gen.fab_note(pkg_name, pkg, tier_name, tier)
    found = False
    for m in re.finditer(r'\(gr_text "((?:[^"\\]|\\.)*)"', pcb):
        text = m.group(1)
        if "ORDER AT PCBWAY" in text:
            pcb = pcb[:m.start(1)] + gen.esc(new_note) + pcb[m.end(1):]
            found = True
            break
    if not found:
        x1, y1, x2, y2 = pkg["outline"]
        pcb = pcb.replace("\t(embedded_fonts no)\n)\n", gen.gr_text(new_note, (x2 + 2, y1), 0, "Cmts.User", 0.5, 0.08, "left top", gen.uid("set_tier", pkg_name, "fabnote")) + "\t(embedded_fonts no)\n)\n")
    notes.append("order note updated")
    pcb = re.sub(r'\(comment 1 "[^"]*"\)', '(comment 1 "%s  %s")' % (pkg_name, tier["title"]), pcb, count=1)
    return pcb


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = [a for a in argv[1:] if a.startswith("--")]
    package_override = None
    for i, a in enumerate(argv):
        if a == "--package" and i + 1 < len(argv):
            package_override = argv[i + 1]
            args = [x for x in args if x != package_override]
    ignore_locks = "--ignore-locks" in flags
    if len(args) != 2 or args[1] not in gen.TIERS:
        sys.exit(__doc__ + "\ntiers: " + ", ".join(gen.TIERS))
    argv = [argv[0]] + args
    pro_path = pathlib.Path(argv[1]).resolve()
    tier_name = argv[2]
    tier = gen.TIERS[tier_name]
    if pro_path.suffix != ".kicad_pro" or not pro_path.exists():
        die("give the .kicad_pro file of the project")
    base = pro_path.with_suffix("")
    pcb_path, sch_path, dru_path = (base.with_suffix(ext) for ext in (".kicad_pcb", ".kicad_sch", ".kicad_dru"))
    for p in (pcb_path, sch_path):
        if not p.exists():
            die("missing %s" % p.name)
    locks = list(pro_path.parent.glob("~*.lck")) + list(pro_path.parent.glob("*.lck"))
    if locks and not ignore_locks:
        die("project looks open in KiCad (lock files: %s). Close it first." % ", ".join(l.name for l in locks))

    d = json.loads(pro_path.read_text())
    tv = d.get("text_variables", {})
    pkg_name = package_override or tv.get("TILE_PACKAGE")
    if pkg_name not in gen.PACKAGES:
        die("TILE_PACKAGE text variable is '%s'; pass --package with one of %s" % (pkg_name, ", ".join(gen.PACKAGES)))
    pkg = gen.PACKAGES[pkg_name]
    old_tier = tv.get("FAB_TIER", "?")
    pcb = pcb_path.read_text()
    if tier["layers"] < copper_layer_count(pcb):
        die("board has %d copper layers; tier %s has %d. Going down is not automated." % (copper_layer_count(pcb), tier_name, tier["layers"]))

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    bdir = pro_path.parent / ("%s-tier-backup-%s-%s" % (base.name, old_tier, stamp))
    bdir.mkdir()
    for p in (pro_path, pcb_path, sch_path, dru_path):
        if p.exists():
            shutil.copy2(p, bdir / p.name)

    notes = []
    gen.apply_tier_to_project(d, pkg_name, tier_name, tier)
    pro_path.write_text(json.dumps(d, indent=2) + "\n")
    notes.append("design rules, netclasses and presets set for %s" % tier_name)

    user_rules = ""
    if dru_path.exists():
        old = dru_path.read_text()
        if gen.USER_RULES_MARKER in old:
            user_rules = old.split(gen.USER_RULES_MARKER, 1)[1].split("\n", 2)[-1] if old.count("\n", old.index(gen.USER_RULES_MARKER)) >= 2 else ""
    dru_path.write_text(gen.dru_text(base.name, pkg_name, tier_name, tier) + user_rules)
    notes.append("custom rules regenerated%s" % (" (your rules kept)" if user_rules.strip() else ""))

    pcb_path.write_text(update_board(pcb, pkg_name, pkg, tier_name, tier, notes))
    sch = sch_path.read_text()
    sch = re.sub(r'\(comment 1 "[^"]*"\)', '(comment 1 "%s  %s")' % (pkg_name, tier["title"]), sch, count=1)
    sch_path.write_text(sch)

    print("%s: %s -> %s" % (base.name, old_tier, tier_name))
    for n in notes:
        print("  - " + n)
    print("  backup in " + bdir.name)
    print("Next: open the project, press B in the board editor to fill zones, run DRC.")
    print("Order as: " + tier["quote"])


if __name__ == "__main__":
    main(sys.argv)
