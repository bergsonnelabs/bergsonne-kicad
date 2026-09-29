# Bergsonne Tiles: KiCad library

Schematic symbols and footprints for [Bergsonne](https://bergsonne.io) tiles,
for KiCad 9 and later. Covers every tile in production or beta.

- `Bergsonne Tiles.kicad_sym`: one symbol per tile.
- `Bergsonne Tiles.pretty/`: one footprint per tile package (T24-10, T44-10,
  T44-12, T44-14, T48-16, T48-22).

## Install

1. Clone or download this repository.
2. In KiCad, open **Preferences > Manage Symbol Libraries**, click the folder
   icon, and add `Bergsonne Tiles.kicad_sym`.
3. Open **Preferences > Manage Footprint Libraries**, click the folder icon, and
   add the `Bergsonne Tiles.pretty` folder.

Keep the nickname **Bergsonne Tiles** for both. Each symbol names its footprint
as `Bergsonne Tiles:<package>`, so that nickname is what links them.

## Symbols

Symbols are generated from Bergsonne's tile definitions. Please don't edit them
here; open an issue instead and we'll fix the source.

- Named after the tile (`Drive.H`). Revisions after the first carry a suffix
  (`Core.ST.W5-b`).
- Supply pins sit at the top: V+ first, then the other rails, each followed by
  its own ground, then shared grounds. Every other pin follows in pad order.
- The text beside a pin gives its supply range or its main alternate functions.
  Every alternate function is also on the pin itself: right-click the pin in a
  schematic to switch to it.
- Pins carry electrical types, so ERC checks supplies and signal directions.
  Unused pads are hidden no-connect pins.

## Footprints

The footprints are designed to extend the pads by 0.1 mm past the tile edge to
leave room for a visible/probe-able solder fillet.
