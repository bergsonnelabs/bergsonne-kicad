#!/usr/bin/env python3
"""Generate the Bergsonne tile KiCad project templates.

    python3 tools/make_tile_templates.py          # writes ../kicad/<package>/

One template per package, all at the base fab tier (BASE_TIER). A design moves
to a higher tier later with tools/set_tier.py, which reuses TIERS from here.
Edit PACKAGES / TIERS / COMMON and re-run; every UUID is derived from the
template name so re-running gives stable files.
Requires only Python 3 (Pillow optional, for the 64x64 template icons).
"""
import json
import pathlib
import shutil
import uuid

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "kicad"
NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://bergsonne.io/tiles/templates")
KICAD_PCB_VERSION = "20241229"
KICAD_SCH_VERSION = "20250114"
BASE_TIER = "2L"

# --------------------------------------------------------------------------- #
# Tile packages (all dimensions mm, KiCad board coordinates: +y is DOWN).
# Pad centres follow the carrier-side footprints in the Bergsonne Tiles library
# minus their 0.1 mm fillet overhang, so a tile drawn top-view lands exactly on
# its carrier land pattern. Pin 1 is the long (1.0 mm) pad, top-left.
# --------------------------------------------------------------------------- #
PITCH = 0.8
PAD_W = 0.4
PAD_L = 0.8


def side_pads(n_side, sx, extra):
    """Left column 1..n top->bottom, right column n+1..2n bottom->top, then extras."""
    pads = []
    for i in range(n_side):
        pads.append(dict(num=i + 1, x=-sx, y=-1.6 + PITCH * i, length=PAD_L, vertical=False))
    for i in range(n_side):
        pads.append(dict(num=n_side + 1 + i, x=sx, y=-1.6 + PITCH * (n_side - 1 - i), length=PAD_L, vertical=False))
    for num, x, y in extra:
        pads.append(dict(num=num, x=x, y=y, length=PAD_L, vertical=True))
    return pads


def with_pin1(pads, pin1_x, overrides=()):
    for p in pads:
        if p["num"] == 1:
            p["x"], p["length"] = pin1_x, 1.0
    for num, x, length in overrides:
        for p in pads:
            if p["num"] == num:
                p["x"], p["length"] = x, length
    return pads


PACKAGES = {
    "T24-10": dict(
        outline=(-1.0, -2.0, 1.0, 2.0),
        pads=with_pin1(side_pads(5, 0.6, []), -0.5, overrides=[(10, 0.7, 0.6)]),
        pinout={1: "GND", 10: "+V", 4: "I2C.CLK", 5: "I2C.DAT"},
        pinout_note="inferred from T44-10 (no T24 tile in the symbol library yet)",
        label=None,  # 0.4 mm between the pad columns: no room for a legend
        description="2 x 4 mm, 10 pads (5 per long side)",
    ),
    "T44-10": dict(
        outline=(-2.0, -2.0, 2.0, 2.0),
        pads=with_pin1(side_pads(5, 1.6, []), -1.5),
        pinout={1: "GND", 10: "+V", 4: "I2C.CLK", 5: "I2C.DAT"},
        pinout_note="standard across all 16 T44-10 tiles in the symbol library",
        label=dict(at=(0, 0), rot=270, size=0.7),
        description="4 x 4 mm, 10 pads (5 per side)",
    ),
    "T44-14": dict(
        outline=(-2.0, -2.0, 2.0, 2.0),
        pads=with_pin1(side_pads(5, 1.6, [(11, 0.4, -1.6), (12, -0.4, -1.6), (13, -0.4, 1.6), (14, 0.4, 1.6)]), -1.5),
        pinout={1: "GND", 10: "+V", 12: "NRST"},
        pinout_note="standard across the three T44-14 core tiles",
        label=dict(at=(0, 0), rot=270, size=0.45),  # same orientation as T44-10; smaller to clear the top/bottom pads
        description="4 x 4 mm, 14 pads (5 per side + 2 top + 2 bottom)",
    ),
    "T48-16": dict(
        outline=(-2.0, -2.0, 2.0, 6.0),
        pads=with_pin1(side_pads(7, 1.6, [(15, 0.4, -1.6), (16, -0.4, -1.6)]), -1.5),
        pinout={1: "GND", 14: "+V", 16: "NRST"},
        pinout_note="from Core.ST.W5-b, the only T48-16 tile so far",
        label=dict(at=(0, 2.4), rot=270, size=0.7),
        description="4 x 8 mm, 16 pads (7 per side + 2 top)",
    ),
    "T48-22": dict(
        outline=(-2.0, -2.0, 2.0, 6.0),
        pads=with_pin1(side_pads(10, 1.6, [(21, 0.4, -1.6), (22, -0.4, -1.6)]), -1.5),
        pinout={1: "GND", 20: "+V", 22: "NRST"},
        pinout_note="inferred by analogy with T44-14 / T48-16 (no T48-22 tile yet)",
        label=dict(at=(0, 2.4), rot=270, size=0.7),
        description="4 x 8 mm, 22 pads (10 per side + 2 top)",
    ),
}

# --------------------------------------------------------------------------- #
# Fab tiers. Each is one set of PCBWay quote options reverse-engineered from
# past orders. Everything is 0.4 mm, FR-4, 1 oz, ENIG, green mask, white silk.
# --------------------------------------------------------------------------- #
COMMON = dict(
    thickness=0.4,
    edge=0.15,            # copper to board edge (base pads excepted by rule)
    hole_to_hole=0.25,
    hole_clearance=0.15,  # copper to (other) hole
    annular=0.1,
    mask_expansion=0.0,
    mask_dam=0.19,        # PCBWay DFM reply, Oct 2026: no dam between pads closer than 0.19 mm (green/red/yellow/blue)
    text_height=0.45,   # the smallest legend (T44-14)
    text_thickness=0.05,
)

TIERS = {
    "2L": dict(
        layers=2, hdi=False,
        track=0.1, hole=0.2, via=(0.4, 0.2), uvia=None,
        track_presets=[0.1, 0.15, 0.2, 0.3],
        via_presets=[(0.4, 0.2)],
        title="2-layer standard",
        quote="Standard calculator: 2 layers / 0.4 mm / 4/4 mil / min hole 0.2 mm / ENIG / tenting",
        cost="Cheapest tile build: $102 per 10-piece 98.2 mm panel, 3-4 days, express available (Oct 2026). Every design starts here.",
    ),
    "2L-fine": dict(
        layers=2, hdi=False,
        track=0.075, hole=0.15, via=(0.35, 0.15), uvia=None,
        track_presets=[0.075, 0.1, 0.15, 0.2, 0.3],
        via_presets=[(0.35, 0.15), (0.4, 0.2)],
        title="2-layer fine (3/3 mil, 0.15 drill)",
        quote="Advanced calculator, through-hole: 2 layers / 0.4 mm / 3/3 mil / min hole 0.15 mm / ENIG",
        cost="$172, 7-8 days, no express (Oct 2026). Only for a board whose single tight spot is one 0.5 mm pitch part; 4L is cheaper and faster for anything else.",
    ),
    "4L": dict(
        layers=4, hdi=False,
        track=0.1, hole=0.2, via=(0.4, 0.2), uvia=None,
        track_presets=[0.1, 0.15, 0.2, 0.3],
        via_presets=[(0.4, 0.2)],
        title="4-layer, through vias",
        quote="Standard calculator: 4 layers / 0.4 mm / 4/4 mil / min hole 0.2 mm / ENIG / through vias only",
        cost="$162, 4-5 days, express available (Oct 2026). First step up from 2L: a GND plane on In1 and a +V plane on In2. Keep the 0.2 mm drill; 0.15 mm on the standard form is the $419 bucket.",
    ),
    "4L-fine": dict(
        layers=4, hdi=False,
        track=0.075, hole=0.15, via=(0.35, 0.15), uvia=None,
        track_presets=[0.075, 0.1, 0.15, 0.2, 0.3],
        via_presets=[(0.35, 0.15), (0.4, 0.2)],
        title="4-layer fine (3/3 mil, 0.15 drill)",
        quote="Advanced calculator, through-hole: 4 layers / 0.4 mm / 3/3 mil / min hole 0.15 mm / ENIG",
        cost="$290, 8-9 days, no express (Oct 2026). 3/3 mil and 0.15 mm drills cost the same there, so take both.",
    ),
    "4L-HDI": dict(
        layers=4, hdi=True,
        track=0.075, hole=0.15, via=(0.35, 0.15), uvia=(0.25, 0.1),
        track_presets=[0.075, 0.1, 0.15, 0.2, 0.3],
        via_presets=[(0.35, 0.15), (0.4, 0.2)],
        title="4-layer HDI 1+2+1 (laser microvias)",
        quote="Advanced calculator, HDI 1+N+1: 4 layers / 0.4 mm / 3/3 mil / laser microvia 0.1 mm drill, 0.25 mm pad, F.Cu-In1.Cu and In2.Cu-B.Cu / through via 0.15 mm / via-in-pad / ENIG",
        cost="$646 with via-in-pad, 8-9 days, no express (Oct 2026). Only when a pad cannot be reached from the surface: interior balls of a 0.4 mm pitch part. Buried In1-In2 vias are disallowed by rule.",
    ),
}

USER_RULES_MARKER = "# --- your own rules below this line ---"

SEVERITY_OVERRIDES = {
    "copper_edge_clearance": "error",
    "solder_mask_bridge": "error",
    "hole_to_hole": "error",
    "text_height": "warning",
    "text_thickness": "warning",
    "isolated_copper": "warning",
    "missing_courtyard": "ignore",
    "silk_over_copper": "warning",
    "silk_overlap": "warning",
}

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def uid(*keys):
    return str(uuid.uuid5(NS, "/".join(str(k) for k in keys)))


def fmt(v):
    """KiCad-style number: no trailing zeros, no '-0'."""
    s = ("%.6f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def footprint_name(length):
    return {0.8: "SMD-800-400", 1.0: "SMD-1000-400", 0.6: "SMD-600-400"}[length]


def net_table(pkg):
    """Ordered nets: ('' , GND, +V, signals..., unconnected pads...) -> {name: index}."""
    names = [""]
    pinout = pkg["pinout"]
    for sig in ("GND", "+V"):
        if sig in pinout.values():
            names.append(sig)
    for num in sorted(pinout):
        sig = pinout[num]
        if sig not in ("GND", "+V"):
            names.append("/" + sig)
    for p in pkg["pads"]:
        if p["num"] not in pinout:
            names.append("unconnected-(P%d-Pad1)" % p["num"])
    return {n: i for i, n in enumerate(names)}


def pad_net_name(pkg, num):
    sig = pkg["pinout"].get(num)
    if sig is None:
        return "unconnected-(P%d-Pad1)" % num
    return sig if sig in ("GND", "+V") else "/" + sig


# --------------------------------------------------------------------------- #
# board (.kicad_pcb)
# --------------------------------------------------------------------------- #

def layers_block(layers):
    rows = ['(0 "F.Cu" signal)']
    if layers == 4:
        rows += ['(4 "In1.Cu" signal)', '(6 "In2.Cu" signal)']
    rows += ['(2 "B.Cu" signal)']
    rows += [
        '(9 "F.Adhes" user "F.Adhesive")', '(11 "B.Adhes" user "B.Adhesive")',
        '(13 "F.Paste" user)', '(15 "B.Paste" user)',
        '(5 "F.SilkS" user "F.Silkscreen")', '(7 "B.SilkS" user "B.Silkscreen")',
        '(1 "F.Mask" user)', '(3 "B.Mask" user)',
        '(17 "Dwgs.User" user "User.Drawings")', '(19 "Cmts.User" user "User.Comments")',
        '(21 "Eco1.User" user "User.Eco1")', '(23 "Eco2.User" user "User.Eco2")',
        '(25 "Edge.Cuts" user)', '(27 "Margin" user)',
        '(31 "F.CrtYd" user "F.Courtyard")', '(29 "B.CrtYd" user "B.Courtyard")',
        '(35 "F.Fab" user)', '(33 "B.Fab" user)',
        '(39 "User.1" user)', '(41 "User.2" user)', '(43 "User.3" user)',
        '(45 "User.4" user "Copper keep-in")',
    ]
    return "\t(layers\n" + "".join("\t\t%s\n" % r for r in rows) + "\t)\n"


def stackup_block(layers):
    def cu(name):
        return '\t\t\t(layer "%s"\n\t\t\t\t(type "copper")\n\t\t\t\t(thickness 0.035)\n\t\t\t)\n' % name

    def diel(n, kind, t):
        return ('\t\t\t(layer "dielectric %d"\n\t\t\t\t(type "%s")\n\t\t\t\t(thickness %s)\n'
                '\t\t\t\t(material "FR4")\n\t\t\t\t(epsilon_r 4.5)\n\t\t\t\t(loss_tangent 0.02)\n\t\t\t)\n' % (n, kind, fmt(t)))

    s = "\t\t(stackup\n"
    s += '\t\t\t(layer "F.SilkS"\n\t\t\t\t(type "Top Silk Screen")\n\t\t\t)\n'
    s += '\t\t\t(layer "F.Paste"\n\t\t\t\t(type "Top Solder Paste")\n\t\t\t)\n'
    s += '\t\t\t(layer "F.Mask"\n\t\t\t\t(type "Top Solder Mask")\n\t\t\t\t(thickness 0.01)\n\t\t\t)\n'
    s += cu("F.Cu")
    if layers == 2:
        s += diel(1, "core", 0.31)
    else:
        s += diel(1, "prepreg", 0.08) + cu("In1.Cu") + diel(2, "core", 0.08) + cu("In2.Cu") + diel(3, "prepreg", 0.08)
    s += cu("B.Cu")
    s += '\t\t\t(layer "B.Mask"\n\t\t\t\t(type "Bottom Solder Mask")\n\t\t\t\t(thickness 0.01)\n\t\t\t)\n'
    s += '\t\t\t(layer "B.Paste"\n\t\t\t\t(type "Bottom Solder Paste")\n\t\t\t)\n'
    s += '\t\t\t(layer "B.SilkS"\n\t\t\t\t(type "Bottom Silk Screen")\n\t\t\t)\n'
    s += '\t\t\t(copper_finish "ENIG")\n\t\t\t(dielectric_constraints no)\n'
    s += "\t\t)\n"
    return s


PLOT_PARAMS = """\t\t(pcbplotparams
\t\t\t(layerselection 0x00000000_00000000_55555555_5755f5ff)
\t\t\t(plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12.000000)
\t\t\t(dashed_line_gap_ratio 3.000000)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(hpglpennumber 1)
\t\t\t(hpglpenspeed 20)
\t\t\t(hpglpendiameter 15.000000)
\t\t\t(pdf_front_fp_property_popups yes)
\t\t\t(pdf_back_fp_property_popups yes)
\t\t\t(pdf_metadata yes)
\t\t\t(pdf_single_document no)
\t\t\t(dxfpolygonmode yes)
\t\t\t(dxfimperialunits yes)
\t\t\t(dxfusepcbnewfont yes)
\t\t\t(psnegative no)
\t\t\t(psa4output no)
\t\t\t(plot_black_and_white yes)
\t\t\t(sketchpadsonfab no)
\t\t\t(plotpadnumbers no)
\t\t\t(hidednponfab no)
\t\t\t(sketchdnponfab yes)
\t\t\t(crossoutdnponfab yes)
\t\t\t(subtractmaskfromsilk no)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 1)
\t\t\t(scaleselection 1)
\t\t\t(outputdirectory "fab/")
\t\t)
"""


def fp_property(name, value, at, layer, uid_, thickness, hide=True):
    return (
        '\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(unlocked yes)\n\t\t\t(layer "%s")\n%s'
        '\t\t\t(uuid "%s")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness %s)\n\t\t\t\t)\n'
        '\t\t\t\t(justify mirror)\n\t\t\t)\n\t\t)\n'
        % (name, esc(value), fmt(at[0]), fmt(at[1]), layer, "\t\t\t(hide yes)\n" if hide else "", uid_, fmt(thickness))
    )


def pad_footprint(tname, pkg, pad, nets, sch_file):
    num = pad["num"]
    ref = "P%d" % num
    fpname = footprint_name(pad["length"])
    rot = 90 if pad["vertical"] else 180
    net_name = pad_net_name(pkg, num)
    k = (tname, "fp", num)
    s = '\t(footprint "Bergsonne:%s"\n\t\t(layer "B.Cu")\n\t\t(uuid "%s")\n\t\t(at %s %s %d)\n' % (
        fpname, uid(*k), fmt(pad["x"]), fmt(pad["y"]), rot)
    s += fp_property("Reference", ref, (0, 0.5), "B.SilkS", uid(*k, "ref"), 0.1)
    s += fp_property("Value", "~", (0, -1), "B.Fab", uid(*k, "val"), 0.15)
    s += fp_property("Datasheet", "", (0, 0), "B.Fab", uid(*k, "ds"), 0.15)
    s += fp_property("Description", "Tile base pad %d" % num, (0, 0), "B.Fab", uid(*k, "desc"), 0.15)
    s += '\t\t(path "/%s")\n\t\t(sheetname "/")\n\t\t(sheetfile "%s")\n\t\t(attr smd)\n' % (uid(tname, "sym", num), sch_file)
    s += ('\t\t(pad "1" smd rect\n\t\t\t(at 0 0 %d)\n\t\t\t(size %s %s)\n\t\t\t(layers "B.Cu" "B.Mask" "B.Paste")\n'
          '\t\t\t(net %d "%s")\n\t\t\t(pintype "passive")\n\t\t\t(solder_mask_margin 0)\n\t\t\t(uuid "%s")\n\t\t)\n'
          % (rot, fmt(pad["length"]), fmt(PAD_W), nets[net_name], esc(net_name), uid(*k, "pad")))
    s += "\t\t(embedded_fonts no)\n\t)\n"
    return s


def gr_rect(x1, y1, x2, y2, layer, width, uid_):
    return ('\t(gr_rect\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type solid)\n\t\t)\n'
            '\t\t(fill no)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n' % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), fmt(width), layer, uid_))


def gr_text(text, at, rot, layer, size, thickness, justify, uid_):
    return ('\t(gr_text "%s"\n\t\t(at %s %s %d)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t\t(effects\n\t\t\t(font\n'
            '\t\t\t\t(size %s %s)\n\t\t\t\t(thickness %s)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t)\n'
            % (esc(text), fmt(at[0]), fmt(at[1]), rot, layer, uid_, fmt(size), fmt(size), fmt(thickness), justify))


def zone(net_idx, net_name, layer, outline, clearance, uid_):
    x1, y1, x2, y2 = outline
    return ('\t(zone\n\t\t(net %d)\n\t\t(net_name "%s")\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t\t(name "%s plane")\n'
            '\t\t(hatch edge 0.5)\n\t\t(connect_pads yes\n\t\t\t(clearance %s)\n\t\t)\n\t\t(min_thickness 0.1)\n'
            '\t\t(filled_areas_thickness no)\n\t\t(fill yes\n\t\t\t(thermal_gap 0.15)\n\t\t\t(thermal_bridge_width 0.15)\n'
            '\t\t\t(island_removal_mode 1)\n\t\t\t(island_area_min 1)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n'
            '\t\t\t\t(xy %s %s) (xy %s %s) (xy %s %s) (xy %s %s)\n\t\t\t)\n\t\t)\n\t)\n'
            % (net_idx, net_name, layer, uid_, net_name, fmt(clearance),
               fmt(x1), fmt(y1), fmt(x2), fmt(y1), fmt(x2), fmt(y2), fmt(x1), fmt(y2)))


def fab_note(pkg_name, pkg, tier_name, tier):
    lines = [
        "%s  %s" % (pkg_name, tier["title"]),
        "ORDER AT PCBWAY AS: " + tier["quote"],
        "FR-4 %s mm, 1 oz Cu, ENIG, green mask, white silk (bottom only)" % fmt(COMMON["thickness"]),
        "track/space >= %s mm, copper to edge >= %s mm (base pads excepted)" % (fmt(tier["track"]), fmt(COMMON["edge"])),
        "via %s/%s mm, hole-to-hole >= %s, copper-to-hole >= %s" % (fmt(tier["via"][0]), fmt(tier["via"][1]), fmt(COMMON["hole_to_hole"]), fmt(COMMON["hole_clearance"])),
    ]
    if tier["uvia"]:
        lines.append("microvia %s/%s mm laser, F.Cu-In1.Cu and In2.Cu-B.Cu, via-in-pad OK" % (fmt(tier["uvia"][0]), fmt(tier["uvia"][1])))
    if tier["layers"] == 4:
        lines.append("In1.Cu = GND plane, In2.Cu = +V plane")
    lines.append("components top side only; bottom = base pads + name")
    lines.append("pinout: " + ", ".join("P%d=%s" % (n, s) for n, s in sorted(pkg["pinout"].items())))
    return "\n".join(lines)


def board_text(tname, pkg_name, pkg, tier_name, tier):
    x1, y1, x2, y2 = pkg["outline"]
    nets = net_table(pkg)
    sch_file = tname + ".kicad_sch"
    s = "(kicad_pcb\n\t(version %s)\n\t(generator \"pcbnew\")\n\t(generator_version \"9.0\")\n" % KICAD_PCB_VERSION
    s += "\t(general\n\t\t(thickness %s)\n\t\t(legacy_teardrops no)\n\t)\n" % fmt(COMMON["thickness"])
    s += '\t(paper "A4")\n'
    s += ('\t(title_block\n\t\t(title "${TILE_FAMILY} ${TILE_VARIANT}")\n\t\t(rev "${TILE_REV}")\n'
          '\t\t(company "Bergsonne")\n\t\t(comment 1 "%s  %s")\n\t\t(comment 2 "${FAB_QUOTE}")\n\t)\n' % (pkg_name, tier["title"]))
    s += layers_block(tier["layers"])
    s += "\t(setup\n" + stackup_block(tier["layers"])
    s += ("\t\t(pad_to_mask_clearance %s)\n\t\t(solder_mask_min_width %s)\n\t\t(allow_soldermask_bridges_in_footprints no)\n"
          "\t\t(tenting front back)\n" % (fmt(COMMON["mask_expansion"]), fmt(COMMON["mask_dam"])))
    s += PLOT_PARAMS + "\t)\n"
    for name, idx in sorted(nets.items(), key=lambda kv: kv[1]):
        s += '\t(net %d "%s")\n' % (idx, esc(name))
    for pad in pkg["pads"]:
        s += pad_footprint(tname, pkg, pad, nets, sch_file)
    s += gr_rect(x1, y1, x2, y2, "Edge.Cuts", 0.05, uid(tname, "edge"))
    e = COMMON["edge"]
    s += gr_rect(x1 + e, y1 + e, x2 - e, y2 - e, "User.4", 0.001, uid(tname, "keepin"))
    if pkg["label"]:
        lb = pkg["label"]
        s += gr_text("${TILE_FAMILY}\n${TILE_VARIANT}", lb["at"], lb["rot"], "B.SilkS", lb["size"], COMMON["text_thickness"], "mirror", uid(tname, "label"))
    s += gr_text(fab_note(pkg_name, pkg, tier_name, tier), (x2 + 2, y1), 0, "Cmts.User", 0.5, 0.08, "left top", uid(tname, "fabnote"))
    if tier["layers"] == 4:
        s += zone(nets["GND"], "GND", "In1.Cu", pkg["outline"], tier["track"], uid(tname, "zone-gnd"))
        s += zone(nets["+V"], "+V", "In2.Cu", pkg["outline"], tier["track"], uid(tname, "zone-v"))
    s += "\t(embedded_fonts no)\n)\n"
    return s


# --------------------------------------------------------------------------- #
# schematic (.kicad_sch)
# --------------------------------------------------------------------------- #
X_SYM = 124.46          # pad symbol anchor
X_PIN = X_SYM + 1.27    # pin tip (symbol is rotated 180 so the pin points right)
X_JUNC = X_PIN + 2.54
X_END = X_PIN + 5.08
Y0 = 78.74
DY = 2.54


def prop(name, value, at, hide, justify=None, rot=0):
    j = ("\t\t\t\t(justify %s)\n" % justify) if justify else ""
    h = "\t\t\t\t(hide yes)\n" if hide else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n%s%s\t\t\t)\n\t\t)\n'
            % (name, esc(value), fmt(at[0]), fmt(at[1]), rot, j, h))


def sym_instance(lib_id, at, rot, ref, value, footprint, uid_, root_uuid, extra_props=(), value_at=None, value_hide=False, ref_hide=False, ref_at=None, value_justify=None, value_rot=0):
    s = '\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s %d)\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid "%s")\n' % (
        lib_id, fmt(at[0]), fmt(at[1]), rot, uid_)
    s += prop("Reference", ref, ref_at or at, ref_hide, "left" if not ref_hide else None)
    s += prop("Value", value, value_at or at, value_hide, value_justify, rot=value_rot)
    s += prop("Footprint", footprint, at, True)
    s += prop("Datasheet", "", at, True)
    for n, v in extra_props:
        s += prop(n, v, at, True)
    s += '\t\t(pin "1"\n\t\t\t(uuid "%s")\n\t\t)\n' % uid(uid_, "pin1")
    s += '\t\t(instances\n\t\t\t(project ""\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n' % (root_uuid, ref)
    return s


def wire(x1, y1, x2, y2, uid_):
    return ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
            % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), uid_))


def schematic_text(tname, pkg_name, pkg, tier_name, tier):
    root = uid(tname, "root")
    s = '(kicad_sch\n\t(version %s)\n\t(generator "eeschema")\n\t(generator_version "9.0")\n\t(uuid "%s")\n\t(paper "A4")\n' % (KICAD_SCH_VERSION, root)
    s += ('\t(title_block\n\t\t(title "${TILE_FAMILY} ${TILE_VARIANT}")\n\t\t(rev "${TILE_REV}")\n\t\t(company "Bergsonne")\n'
          '\t\t(comment 1 "%s  %s")\n\t\t(comment 2 "${FAB_QUOTE}")\n\t)\n' % (pkg_name, tier["title"]))
    s += "\t(lib_symbols\n" + (HERE / "smd_pad_symbol.txt").read_text() + "\n" + (HERE / "power_symbols.txt").read_text() + "\n\t)\n"

    pwr_n = flg_n = 0
    body = ""
    for pad in pkg["pads"]:
        num = pad["num"]
        y = Y0 + DY * (num - 1)
        ref = "P%d" % num
        fp = "Bergsonne:" + footprint_name(pad["length"])
        su = uid(tname, "sym", num)
        body += sym_instance("Bergsonne:SMD-PAD", (X_SYM, y), 180, ref, "~", fp, su, root,
                             extra_props=[("Description", "Tile base pad %d" % num)],
                             ref_at=(X_SYM - 2.54, y), value_at=(X_SYM - 2.54, y - 1.27), value_hide=True, value_justify="left")
        sig = pkg["pinout"].get(num)
        if sig is None:
            body += '\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)\n' % (fmt(X_PIN), fmt(y), uid(tname, "nc", num))
        elif sig in ("GND", "+V"):
            body += wire(X_PIN, y, X_JUNC, y, uid(tname, "w1", num))
            body += wire(X_JUNC, y, X_END, y, uid(tname, "w2", num))
            body += '\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)\n' % (fmt(X_JUNC), fmt(y), uid(tname, "junc", num))
            pwr_n += 1
            flg_n += 1
            if sig == "GND":
                # symbol lies along the wire, pointing right, so neighbouring pad rows stay clear
                body += sym_instance("power:GND", (X_END, y), 90, "#PWR%02d" % pwr_n, "GND", "", uid(tname, "pwr", num), root,
                                     extra_props=[("Description", "Power symbol creates a global label with name \"GND\" , ground")],
                                     ref_hide=True, ref_at=(X_END + 6.35, y), value_at=(X_END + 3.81, y), value_rot=0, value_justify="left")
            else:
                body += sym_instance("power:VD", (X_END, y), 270, "#PWR%02d" % pwr_n, "+V", "", uid(tname, "pwr", num), root,
                                     extra_props=[("Description", "Power symbol creates a global label with name \"VD\"")],
                                     ref_hide=True, ref_at=(X_END + 3.81, y), value_at=(X_END + 3.81, y), value_rot=0, value_justify="left")
            # flag points away from the power symbol: up on the GND row, down on the +V row
            flag_rot = 0 if sig == "GND" else 180
            flag_dy = -3.81 if sig == "GND" else 3.81
            body += sym_instance("power:PWR_FLAG", (X_JUNC, y), flag_rot, "#FLG%02d" % flg_n, "PWR_FLAG", "", uid(tname, "flg", num), root,
                                 extra_props=[("Description", "Special symbol for telling ERC where power comes from")],
                                 ref_hide=True, ref_at=(X_JUNC, y - flag_dy / 2), value_at=(X_JUNC, y + flag_dy))
        else:
            body += wire(X_PIN, y, X_END, y, uid(tname, "w1", num))
            body += ('\t(label "%s"\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
                     '\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (esc(sig), fmt(X_END), fmt(y), uid(tname, "lbl", num)))

    note = "\n".join([
        "%s tile  -  %s" % (pkg_name, tier["title"]),
        "Project > Project Settings > Text Variables: set TILE_FAMILY, TILE_VARIANT, TILE_REV.",
        "Pads P1..P%d are the tile base pads (bottom side). Delete a no-connect flag to use a pad." % len(pkg["pads"]),
        "Standard pinout (%s): %s." % (pkg["pinout_note"], ", ".join("P%d=%s" % (n, v) for n, v in sorted(pkg["pinout"].items()))),
        "Fab: " + tier["quote"],
    ])
    s += ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at 25.4 25.4 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
          '\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (esc(note), uid(tname, "note")))
    s += body
    s += '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n'
    return s


# --------------------------------------------------------------------------- #
# project (.kicad_pro) and custom rules (.kicad_dru)
# --------------------------------------------------------------------------- #

def apply_tier_to_project(d, pkg_name, tier_name, tier):
    """Write a tier's rules, netclasses, presets and text variables into a project dict.
    Used for new templates and by tools/set_tier.py on existing projects."""
    tv = d.setdefault("text_variables", {})
    tv.setdefault("TILE_FAMILY", "TILE")
    tv.setdefault("TILE_VARIANT", "NAME")
    tv.setdefault("TILE_REV", "a")
    tv["TILE_PACKAGE"] = pkg_name
    tv["FAB_TIER"] = tier_name
    tv["FAB_QUOTE"] = tier["quote"]
    ds = d["board"]["design_settings"]
    via_d, via_h = tier["via"]
    uvia_d, uvia_h = tier["uvia"] or tier["via"]
    ds["rules"].update({
        "min_clearance": tier["track"],
        "min_track_width": tier["track"],
        "min_connection": tier["track"],
        "min_copper_edge_clearance": COMMON["edge"],
        "min_hole_clearance": COMMON["hole_clearance"],
        "min_hole_to_hole": COMMON["hole_to_hole"],
        "min_through_hole_diameter": tier["hole"],
        "min_via_diameter": via_d,
        "min_via_annular_width": COMMON["annular"],
        "min_microvia_diameter": uvia_d,
        "min_microvia_drill": uvia_h,
        "min_silk_clearance": 0.0,
        "min_text_height": COMMON["text_height"],
        "min_text_thickness": COMMON["text_thickness"],
        "solder_mask_to_copper_clearance": COMMON["mask_expansion"],
        "max_error": 0.005,
    })
    ds["rule_severities"].update(SEVERITY_OVERRIDES)
    ds["track_widths"] = [0.0] + tier["track_presets"]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}] + [{"diameter": a, "drill": b} for a, b in tier["via_presets"]]
    ds["defaults"]["zones"]["min_clearance"] = tier["track"]
    ds["defaults"]["copper_line_width"] = tier["track"]
    ds["defaults"]["board_outline_line_width"] = 0.05

    def netclass(name, track, priority):
        return {
            "bus_width": 12, "clearance": tier["track"],
            "diff_pair_gap": 0.1, "diff_pair_via_gap": 0.1, "diff_pair_width": 0.1,
            "line_style": 0,
            "microvia_diameter": uvia_d, "microvia_drill": uvia_h,
            "name": name,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": priority,
            "schematic_color": "rgba(0, 0, 0, 0.000)",
            "track_width": track, "via_diameter": via_d, "via_drill": via_h, "wire_width": 6,
        }
    ns = d["net_settings"]
    existing = {c["name"]: c for c in ns.get("classes", [])}
    for name, track, prio in (("Default", tier["track"], 2147483647), ("Power", 0.2, 0)):
        fresh = netclass(name, track, prio)
        if name in existing:
            # keep the user's colours and widths that are not tier-dependent
            for k in ("clearance", "track_width", "via_diameter", "via_drill", "microvia_diameter", "microvia_drill"):
                existing[name][k] = fresh[k]
        else:
            ns.setdefault("classes", []).append(fresh)
    pats = ns.get("netclass_patterns") or []
    for pat in ("+V", "V*"):
        if not any(p.get("pattern") == pat for p in pats):
            pats.append({"netclass": "Power", "pattern": pat})
    ns["netclass_patterns"] = pats
    return d


def project_json(tname, pkg_name, pkg, tier_name, tier):
    d = json.loads((HERE / "base_project.json").read_text())
    d["meta"]["filename"] = tname + ".kicad_pro"
    d["sheets"] = [[uid(tname, "root"), "Root"]]
    d["text_variables"] = {}
    d["net_settings"]["classes"] = []
    d["net_settings"]["netclass_patterns"] = []
    d["net_settings"]["netclass_assignments"] = None
    d["board"]["design_settings"]["diff_pair_dimensions"] = [{"gap": 0.0, "via_gap": 0.0, "width": 0.0}]
    d["board"]["layer_presets"] = []
    d["board"]["layer_pairs"] = []
    apply_tier_to_project(d, pkg_name, tier_name, tier)
    return json.dumps(d, indent=2) + "\n"


def dru_text(tname, pkg_name, tier_name, tier):
    s = "(version 1)\n\n"
    s += "# %s  %s  -  custom design rules, generated by tools/make_tile_templates.py\n\n" % (pkg_name, tier["title"])
    s += ("# Tile base pads are the SMD pads on B.Cu. They reach the board edge by design,\n"
          "# so they are exempt from the %s mm copper-to-edge clearance in Board Setup.\n"
          "# (A pad flush with the edge measures 0, which KiCad treats as a violation of\n"
          "# 'min 0', hence the small negative minimum.)\n" % fmt(COMMON["edge"]))
    s += '(rule "tile base pads reach the board edge"\n\t(condition "A.Pad_Type == \'SMD\' && A.existsOnLayer(\'B.Cu\')")\n\t(constraint edge_clearance (min -0.1mm)))\n\n'
    s += ("# Components live on the top side only; the bottom carries the base pads and\n"
          "# the tile name. Anything else on B.Cu is a mistake.\n")
    s += '(rule "no components on the bottom side"\n\t(condition "A.Type == \'Footprint\' && A.Layer == \'B.Cu\' && !(A.Reference =~ \'^P[0-9]+$\')")\n\t(constraint disallow footprint))\n\n'
    s += "# Blind/buried vias are not part of any ordered stackup.\n"
    s += '(rule "no blind or buried vias"\n\t(constraint disallow buried_via))\n\n'
    if tier["hdi"]:
        ud, uh = tier["uvia"]
        s += ("# HDI 1+2+1: laser microvias %s mm drill / %s mm pad between F.Cu-In1.Cu and\n"
              "# In2.Cu-B.Cu; mechanical through vias %s mm drill minimum.\n" % (fmt(uh), fmt(ud), fmt(tier["hole"])))
        s += ('(rule "microvia size"\n\t(condition "A.Via_Type == \'Micro\'")\n\t(constraint hole_size (min %smm) (max %smm))\n'
              '\t(constraint via_diameter (min %smm)))\n\n' % (fmt(uh), fmt(uh), fmt(ud)))
        s += ('(rule "mechanical via size"\n\t(condition "A.Type == \'Via\' && A.Via_Type != \'Micro\'")\n'
              '\t(constraint hole_size (min %smm)))\n' % fmt(tier["hole"]))
    else:
        s += "# This tier is quoted without laser drilling.\n"
        s += '(rule "no microvias on this tier"\n\t(constraint disallow micro_via))\n'
    s += "\n" + USER_RULES_MARKER + "\n# Rules below this line survive tools/set_tier.py; everything above is regenerated.\n"
    return s


# --------------------------------------------------------------------------- #
# template metadata
# --------------------------------------------------------------------------- #

def info_html(tname, pkg_name, pkg, tier_name, tier):
    rows = [
        ("Package", "%s: %s" % (pkg_name, pkg["description"])),
        ("Fab tier", tier["title"]),
        ("Order as", tier["quote"]),
        ("Track / space", "%s mm" % fmt(tier["track"])),
        ("Via", "%s / %s mm" % (fmt(tier["via"][0]), fmt(tier["via"][1]))),
        ("Microvia", ("%s / %s mm laser" % (fmt(tier["uvia"][0]), fmt(tier["uvia"][1]))) if tier["uvia"] else "none"),
        ("Copper to edge", "%s mm (base pads excepted)" % fmt(COMMON["edge"])),
        ("Pinout", ", ".join("P%d=%s" % (n, v) for n, v in sorted(pkg["pinout"].items()))),
    ]
    table = "".join("<tr><th align=left>%s</th><td>%s</td></tr>" % r for r in rows)
    return ("<html><head><meta charset='utf-8'><title>%s</title></head><body>"
            "<h2>%s</h2><p>Bergsonne tile, %s. %s</p><table>%s</table>"
            "<p>Then: Project &gt; Project Settings &gt; Text Variables &rarr; TILE_FAMILY, TILE_VARIANT, TILE_REV.</p>"
            "<p>Starts at the cheapest tier. When it no longer routes, close the project and run "
            "<code>python3 tools/set_tier.py &lt;project&gt;.kicad_pro 2L-fine | 4L | 4L-HDI</code>.</p>"
            "</body></html>\n" % (tname, tname, pkg["description"], tier["cost"], table))


def icon_png(path, pkg, pkg_name):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    W = 64
    img = Image.new("RGBA", (W, W), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    x1, y1, x2, y2 = pkg["outline"]
    span = max(x2 - x1, y2 - y1)
    sc = 40.0 / span
    ox = 32 - sc * (x1 + x2) / 2
    oy = 26 - sc * (y1 + y2) / 2
    d.rectangle([ox + sc * x1, oy + sc * y1, ox + sc * x2, oy + sc * y2], fill=(20, 90, 50, 255), outline=(0, 0, 0, 255))
    for p in pkg["pads"]:
        w, h = (PAD_W, p["length"]) if p["vertical"] else (p["length"], PAD_W)
        d.rectangle([ox + sc * (p["x"] - w / 2), oy + sc * (p["y"] - h / 2), ox + sc * (p["x"] + w / 2), oy + sc * (p["y"] + h / 2)], fill=(230, 180, 60, 255))
    d.rectangle([0, 50, 63, 63], fill=(40, 40, 40, 255))
    d.text((32, 57), pkg_name, fill=(255, 255, 255, 255), anchor="mm")
    img.save(path)
    return True


# --------------------------------------------------------------------------- #

def write_template(tdir, tname, pkg_name, pkg, tier_name, tier):
    (tdir / "meta").mkdir(parents=True, exist_ok=True)
    (tdir / (tname + ".kicad_pro")).write_text(project_json(tname, pkg_name, pkg, tier_name, tier))
    (tdir / (tname + ".kicad_sch")).write_text(schematic_text(tname, pkg_name, pkg, tier_name, tier))
    (tdir / (tname + ".kicad_pcb")).write_text(board_text(tname, pkg_name, pkg, tier_name, tier))
    (tdir / (tname + ".kicad_dru")).write_text(dru_text(tname, pkg_name, tier_name, tier))
    (tdir / "meta" / "info.html").write_text(info_html(tname, pkg_name, pkg, tier_name, tier))
    icon_png(tdir / "meta" / "icon.png", pkg, pkg_name)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    tier = TIERS[BASE_TIER]
    for pkg_name, pkg in PACKAGES.items():
        write_template(OUT / pkg_name, pkg_name, pkg_name, pkg, BASE_TIER, tier)
    print("wrote %d templates (tier %s) to %s: %s" % (len(PACKAGES), BASE_TIER, OUT, ", ".join(PACKAGES)))


if __name__ == "__main__":
    build()
