# Absent source labels

The shared Sprite 16 `bishaAir` predicate checks energy (default 100) and special
input. Both base timelines lack the `空中必杀` label; they share the control
branch without sharing the set of available timeline labels. Existing placements
and frame scripts keep running; no new attack, resource cost or forced stand may
be invented for this request.

Original fresh-fight traces `minren-missing-bishaAir-neutral` and
`yihu-missing-bishaAir-neutral` hold jump at observation 5 and special at 20–22.
Each records 602 fighter states. Both match the prior native playheads and state,
but native additionally raises `Missing source label: 空中必杀`. Remove the host
assertion and retain its no-op behavior for an absent label. The source callback
survival check must continue observing the same retained instance. This does not
add an aerial special to either form.

The complete source catalogs and callback paths are in each fighter's
`combat.json` / `command_catalog`; no PlaceObject or MOVE is introduced here.
The ordinary jump/landing script remains responsible for the eventual exit.
