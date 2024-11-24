from pathlib import Path
import tikz

HOST = "127.0.0.1"
PORT = 8459

formats = {
  'png': (tikz.render, {'format': 'png'}, '.png', 'image/png', 100),
  'svg': (tikz.render, {'format': 'svg'}, '.svg', 'image/svg+xml', 10),
  'svg2': (tikz.render_dvi, {}, '-2.svg', 'image/svg+xml', 10)
}

CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LAST_CACHE_CLEAN = 0
CACHE_CLEAN_PERIOD = 3600
CACHE_CLEAN_EXPIRY = 7200
