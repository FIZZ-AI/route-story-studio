# Story plan v1

A plan is JSON. The agent authors its structure after inspecting the actual input; the renderer does not infer a narrative from filenames. Run `validate` before keyframes/rendering.

## Top-level fields

- `schema_version`: 1.
- `title`: film title.
- `mode`: `one-shot` or `interactive`.
- `intake_status`: `ready` when rendering an interactive film; closing intake is triggered by the user's request to proceed, not by collecting every optional answer.
- `size`: `[1280,720]`, even landscape dimensions.
- `fps`: 24, 25 or 30.
- `target_seconds`: requested total length. The validator rejects exceeding it by over 10%.
- `palette`: `paper`, `forest` or `night` (region overrides permitted).
- `avatar_asset`: optional user-provided image ledger ID. Without it, the bundled anonymous illustrated traveler portrait moves in a white/coral marker; no private likeness is included.
- `chapters`: regions, their thematic grouping and map geometry.
- `scenes`: the actual ordered sequence. Their frame-rounded durations define the total.
- `music`: optional timed audio cues.
- `assumptions`: explicit source gaps and production decisions, not invented personal events.

## Chapter

```json
{
  "id":"harbor",
  "title":"Harbor district",
  "date":"Recorded date, or empty when unknown",
  "themes":["street life","waterfront"],
  "map_geometry":"schematic",
  "terrain":"coastal",
  "palette":"paper",
  "nodes":[
    {"id":"entry","label":"Arrival","x":0.16,"y":0.64},
    {"id":"market","label":"Market","x":0.30,"y":0.24},
    {"id":"pier","label":"Pier","x":0.72,"y":0.52}
  ],
  "route":["entry","market","pier"]
}
```

Node x,y are normalized diagram positions, not latitude/longitude. Labels should be source-supported or descriptive. Terrain is a visual style. Background illustrations can be supplied as a ledger image ID in `background_asset`. Routes may follow story order when the user permits; do not label that order as recorded chronology unless verified.

## Scenes

Every scene needs unique `id`, `kind`, `duration`. Kinds: `intro`, `map`, `move`, `photo`, `video`, `note`, `transition`, `outro`.

- `map`: `chapter`; optional `at` node. No photos on an establishing map.
- `move`: `chapter`, `from`, `to`; the avatar moves between nodes at source-independent story speed.
- `photo`: `chapter`, ledger `asset` ID of an image, `at`, optional `topic`, `caption`, and `evidence` source IDs. `anchor` left/right/center, `photo_width` fraction (e.g. .57).
- `video`: same, plus `source_in` in source seconds. Playback is real time, so `source_in + duration` must not exceed the source. `source_audio` defaults false.
- `note`: `chapter`, `title`, `text` string or paragraph array, `evidence`, optional `reveal` paragraph/instant and `text_size`. Shorten/split overly dense notes.
- `intro`, `transition`, `outro`: `title`, `subtitle`, optional `chapter` for its visual backdrop. No automatic credits.

All captions must be grounded in their `evidence` IDs. A source ID proves traceability, not the truth of an invented interpretation; the agent must still check what the source actually supports. Unknown places and dates may stay descriptive/empty.

For media, an optional crop `[x0,y0,x1,y1]` uses normalized bounds in the original oriented frame. `redactions` is a list of similarly normalized boxes, applied **before crop**. Inspect the redacted frame. There is no automatic face detector. For moving people, a fixed box must cover their entire path or the clip should be excluded.

```json
{"id":"market-photo","kind":"photo","chapter":"harbor","at":"market","topic":"street life",
 "duration":4,"asset":"A0002","caption":"A stall opening for the evening","evidence":["A0002"],"anchor":"right"}
```

## Music

```json
{"asset":"A0012","start":0,"source_in":0,"duration":38,"target_lufs":-20,"fade_in":0.6,"fade_out":1.2}
```

The source must have an audio stream and fit the cue length. Overlapping cues crossfade through their respective fades. The mixer limits peaks and strips source metadata. If there is no audio cue and no selected source audio, the film is silent; disclose that rather than claiming it has music.

## Example you can execute

Run `scripts/make_demo.py --out /path/to/demo-run` to create a wholly fictional small media folder, music bed and valid editable plan. Inspect it as a syntax/runtime example, not a story that new users must copy. Then run its printed commands with `keyframes` and `render`.

## Inherited production skin

No background_asset is needed to get polished output: the renderer automatically chooses the bundled illustrated atlas by terrain. Geographic precision and visual quality are separate; map_geometry:schematic means illustrative placement, not a primitive drawing. Intro scenes use an equal-aperture rolling filmstrip by default; set layout:title only for an explicit title-only opening. Cover frames reuse selected photo scenes and their crop/redaction settings; opening_allow:false excludes a selected image from the strip. Photo cards default to40px captions at1280px, warm paper, slight tilt and shadow. Notes inherit a taped paper layer. Titles/date get the bundled type and coral underline. Do not put paragraph explanations or repeated caveats in date; keep those in assumptions/project notes.
