from pathlib import Path
import hashlib

HOST = "127.0.0.1"
PORT = 8459

RENDER_TIMEOUT = 15
DEFAULT_LIBRARIES = [
  "amssymb",
  "amsmath",
  "tikz",
  "circuitikz"
]

import tikz
RASTER_SCALE = 10
EM_PT_SIZE = 10
PT_DPI = 72
formats = {
  'png': {
    'renderer': tikz.render,
    'options': {
      'format': 'png',
      'raster_dpi': PT_DPI * RASTER_SCALE
    },
    'mimetype': 'image/png',
    'em-size': RASTER_SCALE * EM_PT_SIZE,
    'description': 'High quality PNG raster format'
  },
  'svg': {
    'renderer': tikz.render,
    'options': {
      'format': 'svg'
    },
    'mimetype': 'image/svg+xml',
    'em-size': EM_PT_SIZE,
    'description': 'SVG vector format'
  },
  'svg2': {
    'renderer': tikz.render_dvi,
    'options': {
      'header': '''<script><![CDATA[const svg=document.documentElement;svg.addEventListener('mouseover',svg.pauseAnimations);svg.addEventListener('mouseout',svg.unpauseAnimations);]]></script>'''
    },
    'mimetype': 'image/svg+xml',
    'em-size': EM_PT_SIZE,
    'description': 'SVG vector format with animation support'
  }
}

CACHE_DIR = Path(__file__).resolve().parent / Path("./cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LAST_CACHE_CLEAN = 0
CACHE_CLEAN_PERIOD = 3600
CACHE_CLEAN_EXPIRY = 7200
CACHE_KEY = lambda preamble, source: hashlib.md5(preamble.encode() + b'\0' + source.encode()).hexdigest()
