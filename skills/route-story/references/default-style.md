# Default production design: Storybook Atlas

This is the required baseline when the user has not chosen a different design. A missing preference means **use these proven defaults**, not “produce a simplified diagram” or “make a rough technical demo”. Preserve the quality floor while replacing the user's own places, route, identity, text and media.

## Read the shipped visuals

Before authoring a new film, open at least `assets/atlas/urban-atlas.png`, `coastal-atlas.png`, `journey-paper.png` and `traveler-portrait.png` with the host image viewer. These are the concrete visual standard, not optional inspiration. `assets/defaults.json` stores sizes and pacing. They are available offline; a network failure does not justify replacing them with a vector grid, colored dots or clip-art buildings.

When country/region is known and image generation is available, adapt an illustrated backdrop to that region's terrain and architecture using these assets as style references. Keep the same finish; do not deliver a generic European-looking town as a named Thai city, for example. Unknown precise stops do not prevent a country-level visual adaptation without claiming invented landmarks. Keep route, names, dates and portrait as editable code layers. Do not invent a specific visited city, building or route from a generic painting. Fictional bundled maps are valid illustrated templates when geography is not sufficiently known; document that in project notes, not as repeated disclaimers on every frame.

## Inherit this design by default

- Watercolor travel atlas with warm paper, lively turquoise water, layered greens, delicate linework and attractive miniature architecture. Keep an overall coherent style, with locally relevant differences.
- An anime-style portrait in a warm white/coral round marker travels on the map. Use the bundled anonymous traveler if no custom portrait is supplied; never borrow a real person's face from a reference.
- White-underlaid coral dashed paths, clear directional cues, default green stops and coral active stop. Place nodes after viewing the actual artwork: streets/exhibits on plausible land/paths, coast nodes on shore, water crossings only when appropriate. Do not transplant arbitrary zigzags onto water. Leave movement space and keep names/avatar clear of media cards.
- Large navy chapter title with coral underline; concise date directly below. Bundle WenKai to preserve the typography across hosts instead of relying on random system fonts. At 1280px width: captions about40px, labels/date about28px, avatar about78px diameter. Use short place titles and one-line or balanced two-line captions.
- Travel state: first show the region's full illustrated map, then animate avatar travel without media clutter. Arrival state: large real photo/video on a warm paper card, subtle tilt and soft shadow, preserving its deliberate crop/aspect ratio. It must be the photo that grows, not just an empty white frame.
- Default opening is a connected, equal-aperture filmstrip over the watercolor journey-paper background, using selected privacy-checked media. Let memories move past, then hold the film title. Don't force a personal sentence the user never supplied.
- Notebook thoughts have a distinct paper layer, a little tape/underline and a strong enough shadow to read clearly over the illustrated map. Paragraphs appear promptly; leave a short complete hold. Avoid slow per-character typing or excessive final waiting.
- Return/closing sequence has room to breathe; farewell card is uncluttered, a title and optional date. No soundtrack list or long credits unless explicitly requested.

## Pacing defaults

If no total length is given, target about4–5 minutes when enough meaningful material exists. Shorten naturally when material is sparse; do not repeat images or pad empty holds. Respect any explicit requested length, such as a90-second first film.

Start around: overview2s, travel1.5–4s, photo3–5s, short notebook5s, city reflection12–16s, final reflection20–25s, farewell3.5s. Scale to the story and budget; these are the inherited starting points, not a requirement to place every element in every film. Respect user changes to individual timings.

## Music defaults

If the user supplies music, use their choice. Otherwise prefer the curated official catalogue that established this design's emotional arc: a light band piece for departure, gentle piano for contemplative places, a city-night groove for a metropolitan section, restrained piano for return/reflection. `scripts/default_music.py` writes the four reference pages into the working project; it never downloads audio. The referenced site prohibits bot collection. Obtain permitted user-supplied copies or an appropriately licensed alternative from a source allowing the acquisition method:

```bash
python scripts/default_music.py --out /path/to/working-input/music
```

Read source and licence/composer conditions before acquiring any recording. Required attribution can accompany the movie in its description or credits document where the chosen licence allows; do not clutter the farewell card unnecessarily. Do not bundle raw music in the public skill or imply a commercial song is licensed just because it can be streamed. Smooth music transitions and reduce it for longer reading. Original crowd/fireworks sound is off by default. Tone-bed synthesis is only for an explicitly requested rough/test soundtrack, not the normal production default. If the host cannot retrieve or use any appropriate music, state the specific limitation instead of disguising a beep loop as finished scoring.

## Acceptance gate

A technically decodable MP4 is necessary but not sufficient. Before delivery, inspect the illustrated overview, an arrival card, a transition, a notebook (when present), the ending and actual encoded frames. Record in `DESIGN_REVIEW.md` what you actually inspected against the shipped visual references. Reject small illegible captions, placeholder diagrams, empty padded cards, obstructed avatar/labels, accidental crops, conflicting styles, repetitive edits or unreadably slow text.

One-shot mode performs this review internally and fixes failures without asking the user at every stage. Interactive mode preserves agreed designs; missing preferences still use the defaults. If required artwork is absent or corrupt, restore/adapt the bundled quality assets or report that constraint; do not call a downgraded diagram the final product.
