# Decisions that make this a story film

## Story hierarchy

The route is the outer spine; thematic organization inside a place is the inner spine. A scene sequence might move from what was noticed, through an encounter or contrast, to a changed understanding. Use only relationships supported by the actual material. The example pattern is not a demand for a museum, a historical explanation or a philosophical conclusion in every trip.

A plain chronological list of photos does not pass just because a map is behind it. The outline must say what the region's internal sections contribute to the overall story. A coherent sequence can be simple and descriptive when no personal notes exist.

## Two visual states

- **Travel:** an overview/map with enough space for the path and an avatar. Avoid floating photos and dense prose at this moment. Keep movement legible, with short anticipation and arrival holds.
- **Arrival:** a real photo or short video becomes the primary detail. A map remains as context, with one clear current stop. Use a neutral one-line caption or, if needed, two balanced lines. The caption should add information rather than repeat the point label.

Use native-aspect portrait and landscape cards. Do not stretch an image, enlarge only its empty frame, or hide important content in an automatic center crop. `crop` is an intentional normalized box. The bundled fallback supports left/right/center cards and relative photo width; inspect whether the chosen anchor obscures the avatar or route. Choose node positions and anchors together.

Use the shipped Storybook Atlas illustrated assets as the default production quality floor. Read default-style.md and open the reference assets. Rich regional illustrations are part of the design, not optional polish that can be omitted because the user gave no preference. Adapt them with the host image generator when local character should change. Keep text, routes and avatar editable. Unknown exact geography calls for an explicitly illustrative composition, not poor drawing quality. The renderer must never silently substitute a flat grid or primitive clip-art diagram.

## Pace and reading

Budget duration by story role, not one identical time per file. A still may take 2.5–5 seconds; an informative image or personal thought can need more; a moving route may need only 1–3 seconds. These are starting points. Respect user choices and the total runtime. Retain source video speed unless deliberately requested otherwise.

Show a short reflection in a separate readable state instead of adding analysis over every photo. Text can appear in paragraphs, early enough to leave a brief complete hold. Avoid slow per-character typing and long empty waits. Do not shrink type to fit excessive text; shorten, split or re-budget.

## Sound

Use changes in emotional direction, not every photo switch, to motivate music changes. Keep music quieter for reading. Fade/overlap cues rather than abruptly swapping recordings. A busy firework/crowd recording is not automatically an improvement over music; use it only if it serves this user's intended experience. Credits and soundtrack lists are opt-in, not forced onto the farewell card.

The curated official music catalogue is the production default when the user has no choice. The tone generator is only an explicitly accepted test aid, not a production shortcut. Do not bundle or redistribute commercial songs or this project's testing audio inside the public package.

## Quality review in dependency order

Review source selection and narrative connections first, then regional/map layout, then media crop/privacy/caption placement, then durations/reveals, then music and final continuity. Changing the story after polishing every frame causes avoidable rework.

Inspect the finished encoded movie too. A correct scene plan is not proof that the visual result is attractive, that a face is hidden, or that the soundtrack is pleasant. Report exactly what you checked.
