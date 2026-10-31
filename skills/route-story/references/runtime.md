# Runtime and portable execution

The narration/curation workflow runs in any capable agent host. Actual movie production needs:

- Python 3.9+, Pillow, FFmpeg and FFprobe on PATH.
- NumPy only for the optional original review bed.
- The bundled OFL WenKai font supplies the default consistent CJK/Latin type. Set ROUTE_STORY_FONT or plan font only for an explicit alternative.
- Optional `pillow-heif` for HEIC. macOS native `sips` and FFmpeg are fallback decoders, checked at runtime. An unsuccessful conversion remains an unreadable asset, not a blank success.

```bash
python -m pip install -r requirements.txt
python skills/route-story/scripts/route_story.py doctor
```

`ROUTE_STORY_FFMPEG` and `ROUTE_STORY_FFPROBE` can name binaries when they are not on PATH. The production artwork, anonymous avatar and open WenKai font are bundled. No OpenAI API key, user account, private photo database or particular operating system is required by the bundled renderer. Network/image-generation availability is a host capability, not something this package secretly provides.

## Codex vs ChatGPT

The same skill can guide both hosts. A local skill folder can be used with Codex or installed through a skill installer. The repository also includes a portable plugin manifest and one bundled skill. ChatGPT web distribution uses the host's supported plugin installation/public directory mechanisms; merely uploading `SKILL.md` does not establish that every account can execute local scripts or access local media. Check the actual host, files and tools before promising video production.

If code execution or FFmpeg is unavailable, give the user the complete editable storyboard and runnable project, name the missing capability, and clearly mark MP4 rendering as incomplete. Do not substitute a slideshow image and call it a rendered video.

## Frame geometry

The first renderer supports even-sized landscape canvases with width at least 480 and height at least 270; 1280x720 at 24 or 30 fps is recommended. Treat other aspect ratios as unsupported until their keyframes have been checked. Video playback is real time; trims must fit the source. Silent inputs remain silent unless music or source audio is explicitly selected.

## Optional original review music

```bash
python scripts/tone_bed.py --out /path/to/working-input/review-score.wav --seconds 90
```

Use this only when the user explicitly requests or accepts a rough/test soundtrack. It creates a simple original synthetic instrumental bed for testing/review, with no external recording, artist imitation or samples. Label it as a placeholder; the user may replace it. Add it to the ledger by re-running inventory, then refer to its resulting asset ID in the plan's `music` cues. Do not write it into the user's original source folder.
