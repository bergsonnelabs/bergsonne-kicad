# PCBWay price and lead-time sweeps

Raw quotes from PCBWay's two online calculators, fetched on 2026-10-18 by
posting every combination of the knobs below to the calculators' own quote
endpoint (`/Quote/GetDeliveryDays/`, the call the Calculate button makes).
Fixed for every row: single pieces, 98.2 x 98.2 mm, 10 pcs, FR-4 Tg150, 1 oz
copper, white silkscreen, shipping to the US. Prices are PCB cost in USD before
shipping; `std_lead` / `std_hours` is the cheapest build-time option offered,
`other_options` lists the faster paid options when PCBWay offered any.

- `pcbway-standard-2026-10-18.csv`: Standard PCB calculator, 256 rows
  (layers 2/4 x thickness 0.4/0.6/1.0/1.6 x 4/4 or 3/3 mil x hole 0.2/0.15 x
  green/blue mask x HASL lead-free/ENIG x tenting/plugged vias).
- `pcbway-advanced-2026-10-18.csv`: Advanced PCB calculator, 512 rows (same
  knobs minus via tenting, which that form does not have, plus through-hole
  vs HDI and via-in-pad off/on). IPC 6012 Class 2.

Re-run: open the calculator, fill size and quantity, press Calculate once,
then replay the captured request with the option fields changed. The field
names are the `rad*` / `hid*` inputs of the form (`hidLayers`,
`radBoardThickness`, `radLineWeight`, `radVias`, `radSolderColor`,
`radPlatingType`, `radSolderCover`; advanced adds `iptPCBShape` and
`hidViaPadNew`).

See the "PCBWay price breakpoints" section of ../README.md for the reading.
