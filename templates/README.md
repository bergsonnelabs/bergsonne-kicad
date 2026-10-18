# Bergsonne tile templates for KiCad 9

One KiCad project template per tile package (T24-10, T44-10, T44-14, T48-16,
T48-22), each a complete project (schematic, board, project settings, custom
DRC rules) with the outline, base pads, standard pinout, stackup, netclasses
and PCBWay order parameters set for the cheapest fab tier. A new tile starts
with a board that passes DRC. When the cheapest tier stops routing,
`tools/set_tier.py` moves the project up a tier in place.

```
templates/
  README.md                  this file
  kicad/                     the templates (point KiCad here, see Install)
    T44-10/                  one folder per package, all at tier 2L
      T44-10.kicad_pro       project settings, design rules, netclasses, text variables
      T44-10.kicad_sch       base pads P1..Pn, GND / +V / signal pre-wired, no-connect flags on the rest
      T44-10.kicad_pcb       outline, base pads, keep-in guide, name legend, order note
      T44-10.kicad_dru       custom rules: edge-clearance exemption for base pads, via-type limits
      meta/info.html         shown in KiCad's template chooser
      meta/icon.png
    ...
  tools/set_tier.py              move an existing project to 2L-fine, 4L or 4L-HDI in place
  tools/make_tile_templates.py   generator: edit PACKAGES / TIERS / COMMON, re-run, all five are rebuilt
  tools/base_project.json        project-settings skeleton (severities, ERC pin map, BOM presets)
  tools/*.txt                    symbol definitions embedded into every schematic
```

## Install (once per machine)

1. Clone this repository (the same clone that provides the tile libraries).
2. KiCad > Preferences > Configure Paths: set `KICAD_USER_TEMPLATE_DIR` to the
   clone's `templates/kicad` directory.
3. Restart KiCad. The templates appear under File > New Project from Template >
   User Templates. `git pull` picks up template updates; KiCad reads the folder
   fresh each time the dialog opens.

The pad symbol and footprints are `Bergsonne:SMD-PAD`, `Bergsonne:SMD-800-400`,
`SMD-1000-400` and `SMD-600-400` from Bergsonne's internal `Bergsonne` library
(not part of this repository). They are embedded in every template, so the
files open and pass DRC without it; editing the pads themselves needs that
library installed under the `Bergsonne` nickname.

## Use

1. File > New Project from Template > User Templates, pick the package,
   name the project after the tile (`Sense-XYZ`).
2. Project > Project Settings > Text Variables: set `TILE_FAMILY`, `TILE_VARIANT`,
   `TILE_REV`. They drive the title block and the name legend on the underside.
3. In the schematic, delete the no-connect flag on any base pad you use and wire
   it. P1 (GND), the +V pad and the standard signals are already wired.
4. Design on the top side. Run DRC; the template is clean before you start, so
   every violation you see is yours.
5. Order exactly as the "ORDER AT PCBWAY AS" note on the Cmts.User layer says.
   The same text is in `FAB_QUOTE` and in the title block.

## Upgrading the tier

Every project starts at `2L`. When it will not route, close the project in
KiCad and run, from the clone's `templates` folder:

```
python3 tools/set_tier.py "/path/to/Sense-XYZ/Sense-XYZ.kicad_pro" 2L-fine
```

with `2L-fine`, `4L` or `4L-HDI`. The script

- copies the project files to `Sense-XYZ-tier-backup-<old tier>-<time>/`,
- sets the design rules, netclass widths and the track/via presets,
- regenerates the custom rules (anything you wrote below the marker line in
  the `.kicad_dru` is kept),
- on a move to 4 layers, adds `In1.Cu` / `In2.Cu`, the 0.4 mm stackup, and a
  GND plane on In1 and a +V plane on In2 if the board has none,
- rewrites the order note on `Cmts.User`, the title block and `FAB_TIER` /
  `FAB_QUOTE`.

Reopen the project, press `B` to fill zones, run DRC: the tracks and vias you
already placed are untouched, so DRC tells you nothing new is broken. Right
after a move to 4 layers DRC warns "Isolated copper fill" for the two new
planes; that clears once a via ties each plane to its net.
Tiers only go up; to go back down, restore the backup folder. Jumping tiers
(`2L` straight to `4L-HDI`) is fine.

The KiCad-only alternative is Board Setup > Import Settings from Another
Board, pointing at a project already on the target tier, with "Design rule
constraints", "Predefined track & via dimensions", "Net classes" and "Custom
rules" ticked. It does not add inner layers, planes, or the order note.

## Fab tiers (PCBWay, from past orders)

Common to every tier: FR-4, 0.4 mm, 1 oz copper, ENIG, green mask, white
silkscreen on the bottom only.

| Tier | Layers | Track / space | Min hole | Via (pad / drill) | Microvia | Order as |
|---|---|---|---|---|---|---|
| `2L` (start here) | 2 | 0.10 mm (4/4 mil) | 0.20 | 0.40 / 0.20 | none | 2 layers, 0.4 mm, 4/4 mil, min hole 0.2, ENIG |
| `2L-fine` | 2 | 0.075 mm (3/3 mil) | 0.15 | 0.35 / 0.15 | none | 2 layers, 0.4 mm, 3/3 mil, min hole 0.15, ENIG |
| `4L` | 4 | 0.10 mm (4/4 mil) | 0.15 | 0.35 / 0.15 | none | 4 layers, 0.4 mm, 4/4 mil, min hole 0.15, ENIG, through vias only |
| `4L-HDI` | 4 (1+2+1) | 0.075 mm (3/3 mil) | 0.15 (mech.) | 0.35 / 0.15 | 0.25 / 0.10 laser, F.Cu-In1.Cu and In2.Cu-B.Cu, via-in-pad OK | 4 layers HDI 1+2+1, 0.4 mm, 3/3 mil, laser via 0.1, ENIG |

Price breakpoints, measured on 2026-10-18 (10 pcs of 98.2 x 98.2 mm, Tg150,
1 oz, ENIG, green, tenting; raw data in `fab/`). The two calculators price
the same board differently, so the table says which one to use.

| Build | Standard calculator | Advanced calculator (through-hole) |
|---|---|---|
| 2L 0.4 mm, 4/4 mil, 0.2 mm hole | **$101.52, 3-4 days** | $171.62, 7-8 days |
| 2L 0.4 mm, 3/3 mil, 0.2 mm hole | $198.71, 7-8 days | **$171.62, 7-8 days** |
| 2L 0.4 mm, any, 0.15 mm hole | $259.56, 7-8 days | **$171.62, 7-8 days** |
| 4L 0.4 mm, 4/4 mil, 0.2 mm hole | **$161.88, 4-5 days** | $290.00, 8-9 days |
| 4L 0.4 mm, 3/3 mil, 0.2 mm hole | $358.16, 8-9 days | **$290.00, 8-9 days** |
| 4L 0.4 mm, any, 0.15 mm hole | $419.01, 8-9 days | **$290.00, 8-9 days** |
| 4L HDI 1+N+1 (advanced only), 4/4, 0.2 | n/a | $461.79, 8-9 days |
| 4L HDI, 3/3 or 0.15 | n/a | +$7.10 per step (max $475.99) |
| via-in-pad (advanced only) | n/a | +$170 (HDI), +$151 to +$183 (through-hole) |

What the data says:

- On the standard calculator the fab options are buckets, not increments:
  3/3 mil moves a 2L board to a flat $198.71 and 0.15 mm holes to a flat
  $259.56 regardless of thickness; on 4L the same options cost $358.16 and
  $419.01. Thickness, mask colour and tenting/plugged vias do not change those
  bucket prices. Blue mask is free but adds about two days.
- 0.4 mm with HASL is a $168 special on the standard form; with ENIG it is a
  normal thin build ($101.52 on 2L, $161.88 on 4L). Tiles are ENIG anyway.
- ENIG costs +$26 on 2L, +$25 on 4L at thickness >= 0.6 mm. Plugged vias
  +$25. The $18.18 / 24-hour base is 2L, >= 1.0 mm, HASL, 4/4 mil, 0.2 hole.
- On the advanced calculator the through-hole price ignores thickness,
  track/space, hole size and mask entirely: $171.62 (2L ENIG) or $290.00
  (4L ENIG), always 7-9 days. That is why a fine-feature board is cheaper
  there and a plain one is cheaper on the standard form.
- HDI is a flat $461.79 (ENIG) with tiny steps for 3/3 mil and 0.15 holes,
  and the same price on 2 or 4 layers.

Tiers this suggests (ENIG, 0.4 mm, per 10-piece panel):

| Tier | Order where | Options | Price, lead |
|---|---|---|---|
| `2L` | standard | 4/4 mil, 0.2 mm hole | $101.52, 3-4 days |
| `2L-fine` | advanced, through-hole | 3/3 mil, 0.15 mm hole | $171.62, 7-8 days |
| `4L` | standard | 4/4 mil, **0.2 mm hole** | $161.88, 4-5 days |
| `4L-fine` | advanced, through-hole | 3/3 mil, 0.15 mm hole | $290.00, 8-9 days |
| `4L-HDI` | advanced, HDI | 3/3 mil, 0.15 mm, via-in-pad | $646.39, 8-9 days |

The `4L` tier in the generator currently uses a 0.15 mm drill; on the
standard form that is the $419 bucket, so it should move to 0.2 mm and the
0.15 mm drill should become `4L-fine` on the advanced form.

Rules common to every tier (Board Setup > Constraints):

| Rule | Value | Note |
|---|---|---|
| Copper to board edge | 0.15 mm | base pads excepted by custom rule (below) |
| Hole to hole | 0.25 mm | |
| Copper to hole | 0.15 mm | |
| Via annular ring | 0.10 mm | |
| Solder mask expansion | 0 | mask-defined pads, as before |
| Solder mask dam | 0.10 mm | PCBWay normal-difficulty figure; not yet confirmed from an order |
| Silkscreen text | 0.7 mm / 0.05 mm, vertical (T44-14: 0.45 mm) | only the name on the underside; PCBWay's stated minimum is 0.8 / 0.15 |
| Blind / buried vias | disallowed | on every tier (enable in `.kicad_dru` if an HDI order includes In1-In2 buried vias) |

Netclasses: `Default` at the tier's track width; `Power` at 0.2 mm for nets
matching `+V` or `V*`. Both use the tier's via.

## Base pads and the edge clearance

The base pads reach the board edge; everything else must stay 0.15 mm away.
The old projects solved this by ignoring the edge-clearance check altogether.
The templates keep the check at error severity and exempt only the base pads
with a custom rule in the project's `.kicad_dru`:

```
(rule "tile base pads reach the board edge"
    (condition "A.Pad_Type == 'SMD' && A.existsOnLayer('B.Cu')")
    (constraint edge_clearance (min -0.1mm)))
```

"SMD pad on the bottom layer" is the definition of a base pad, because tiles
carry components on the top only. A second rule enforces that: any footprint
other than `P<n>` on B.Cu is a DRC error. A pad flush with the edge measures
0 mm, which KiCad reports as a violation of `min 0`, so the exemption uses a
small negative minimum.

## Packages

Coordinates are tile top view, origin at the centre of the pin-1 cell, y down,
so a tile drawn here lands exactly on its carrier footprint from
`Bergsonne Tiles.pretty` (those pads are 0.1 mm longer for the fillet).
Pin 1 is the long (1.0 mm) pad at the top left. The others are 0.8 x 0.4 mm on
a 0.8 mm pitch, reaching the edge.

| Package | Outline | Pads | Pre-wired pinout | Source of the pinout |
|---|---|---|---|---|
| T24-10 | 2 x 4 mm | 5 per long side; pad 10 shortened to 0.6 mm opposite pin 1 | P1 GND, P4 I2C.CLK, P5 I2C.DAT, P10 +V | inferred from T44-10 (no T24 tile in the library yet) |
| T44-10 | 4 x 4 mm | 5 per side | P1 GND, P4 I2C.CLK, P5 I2C.DAT, P10 +V | all 16 T44-10 tiles |
| T44-14 | 4 x 4 mm | 5 per side + 2 top + 2 bottom | P1 GND, P10 +V, P12 NRST | the three T44-14 core tiles |
| T48-16 | 4 x 8 mm | 7 per side + 2 top | P1 GND, P14 +V, P16 NRST | Core.ST.W5-b |
| T48-22 | 4 x 8 mm | 10 per side + 2 top | P1 GND, P20 +V, P22 NRST | inferred by analogy; no T48-22 tile yet |

Pad numbering: down the left side, up the right side, then the top pair right
to left, then the bottom pair left to right (same as the carrier footprints).

## What is on the board

- `Edge.Cuts`: the outline (0.05 mm line).
- `User.4` ("Copper keep-in"): the outline inset by 0.15 mm, a drawing guide for
  where copper may go.
- `B.SilkS`: `${TILE_FAMILY}` / `${TILE_VARIANT}` mirrored, between the pad
  columns. T24-10 has no room for it.
- `Cmts.User`: the order note, off-board to the right. Not a fab layer.
- After an upgrade to 4 layers: `In1.Cu` GND plane and `In2.Cu` +V plane,
  solid connections, covering the outline. Rename the +V zone's net if the tile has a different
  main rail. (Sig / GND / PWR / Sig is the classic 4-layer stack; with 0.08 mm
  dielectrics both outer layers are tightly coupled to their plane. The
  alternative, GND on both inner layers with power as tracks, is a one-zone
  change.)

## Conventions the rules enforce

- Components on the top side only. Bottom = base pads + name.
- No blind/buried vias. Microvias only on `4L-HDI`, 0.1 mm drill, 0.25 mm pad.
- Through holes no smaller than the tier's minimum drill.
- Edge clearance 0.15 mm except base pads.

## Checks

Every template passes `kicad-cli pcb drc --schematic-parity` with zero
violations, and so does a copy of T44-10 stepped through `set_tier.py` to
`2L-fine`, `4L` and `4L-HDI`.

ERC on a fresh template reports "Label not connected to anything" for each
pre-placed signal label (`I2C.CLK`, `I2C.DAT`, `NRST`). KiCad 9 flags a local
label whose net contains nothing but that label and its one pad; the error
disappears as soon as you wire the signal to something, which is the point of
the label. Everything else in ERC is clean: unused pads carry no-connect
flags, and GND / +V have power flags.

## Regenerating

```
python3 tools/make_tile_templates.py
```

rewrites `kicad/` from `PACKAGES`, `TIERS` and `COMMON` at the top of the
script; `set_tier.py` imports the same tables, so a tier edit reaches both new
and existing projects. UUIDs derive from the template name, so a re-run
changes only what you changed. Pillow (installed) draws the icons; without it the templates are
still produced, just without icons.

## Open items

- 0.1 mm mechanical drill: understand when PCBWay asks for it, then decide
  whether it is a tier.
- Solder mask dam 0.1 mm and the 0.25 / 0.15 hole clearances are PCBWay's
  published numbers, not yet confirmed against an order.
- T24-10 and T48-22 pinouts are inferred; fix the generator when the first
  tile of each exists.
- Panelization and singulation (saw streets, fiducials) are not part of the
  tile template.
