from flask import Flask, request, Response, send_file, url_for
app = Flask(__name__)

@app.route("/")
def hello():
  return """
<form action="svg" method="post">
<textarea name="source" cols=100, rows=25>
hi\\begin{tikzpicture}
\\draw (0,0) -- (1,1);
\\draw (0,0) node[ground]{} (1,0);
\\end{tikzpicture}there
</textarea><br>
<input type="submit">
</form>
  """

import tikz
from pathlib import Path
import hashlib
import time

CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LAST_CACHE_CLEAN = 0
CACHE_CLEAN_PERIOD = 3600
CACHE_CLEAN_EXPIRY = 7200

@app.route('/clean')
def clean_cache(auto=False):
  global LAST_CACHE_CLEAN
  now = time.time()
  if auto and now < LAST_CACHE_CLEAN + CACHE_CLEAN_PERIOD:
    return

  out = []
  for file in CACHE_DIR.iterdir():
    if not file.is_file():
      continue
    if now - file.stat().st_mtime > CACHE_CLEAN_EXPIRY:
      out.append(file.name)
      file.unlink()

  LAST_CACHE_CLEAN = now
  if auto:
    return out
  else:
    return Response('\n'.join(out), mimetype='text/plain')

@app.before_request
def auto_clean():
  clean_cache(True)

@app.route('/tikz.js')
def js():
  src = Path('./tikz.js').read_text() + f'\nprocessTikz("{request.host_url}")\n'
  return Response(src, mimetype="text/javascript")

formats = {
  'png': ('.png', 'image/png'),
  'svg': ('.svg', 'image/svg+xml')
}

@app.route("/<format>", methods=["POST"])
def generate(format):
  ext, mime = formats[format]

  preamble = request.form.get("preamble", "")
  source = request.form.get("source", "")

  key = hashlib.md5(preamble.encode() + b'\0' + source.encode()).hexdigest()
  CACHED = CACHE_DIR / (key + ext)

  if not CACHED.exists():
    ok, out = tikz.render(source, preamble=preamble, format=format)
    if not ok:
      return Response(out, mimetype="text/plain", status=500)
    CACHED.write_bytes(out)

  CACHED.touch()
  return send_file(CACHED, mimetype=mime)
