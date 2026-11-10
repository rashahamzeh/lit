# Birthday reel v2: source

This is an upbeat, beat-synced 38 s reel at 1080×1920 / 30 fps, with an original 120 BPM track synthesised in `music2.py`. The finale melody is "Happy Birthday", which is public domain.

To rebuild it: `node sprites.js` (renders the text layers), then `python3 music2.py`, then `python3 render.py` (renders every frame and pipes them into ffmpeg).
The personal and family photos (expected in `ph/`) and the rendered video are not committed, to keep the family's photos private.
