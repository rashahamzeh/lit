# Birthday reel v2: source

This is an upbeat, beat-synced 44 s reel at 1080×1920 / 30 fps, with an original 120 BPM track synthesised in `music3.py`. The finale melody is "Happy Birthday", which is public domain.

To rebuild it: `node sprites.js` (renders the text layers), then `python3 music3.py`, then `python3 render.py` (renders every frame and pipes them into ffmpeg).
The personal and family photos (expected in `ph/`) and the rendered video are not committed, to keep the family's photos private.

All text uses the LIT brand fonts from the Brand Guidelines: Futura XBlk BT, Futura Hv BT, Futura BdCn BT and Futura Md BT. The font files are licensed, so they are not committed. Copy them into `fonts/` from the LIT Drive.
