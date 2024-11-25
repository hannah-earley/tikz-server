from flask import Flask, request, Response, send_file, url_for
from pathlib import Path
import hashlib
import time
import config

app = Flask(__name__)

@app.route('/clean')
def clean_cache(auto=False):
  now = time.time()
  if auto and now < config.LAST_CACHE_CLEAN + config.CACHE_CLEAN_PERIOD:
    return

  out = []
  for file in config.CACHE_DIR.iterdir():
    if not file.is_file():
      continue
    if now - file.stat().st_mtime > config.CACHE_CLEAN_EXPIRY:
      out.append(file.name)
      file.unlink()

  config.LAST_CACHE_CLEAN = now
  if auto:
    return out
  else:
    return Response('\n'.join(out), mimetype='text/plain')

@app.before_request
def auto_clean():
  clean_cache(True)

@app.route('/tikz.js')
def js():
  fmt = request.args.get('format', default='png')
  _,_,_,_,scale = config.formats[fmt]
  src = Path('./tikz.js').read_text() + f'\nprocessTikz("{url_for("generate", fmt=fmt, _external=True)}", {scale})\n'
  return Response(src, mimetype="text/javascript")

@app.route("/<fmt>", methods=["POST"])
def generate(fmt):
  fn, kw, ext, mime, _scale = config.formats[fmt]

  preamble = request.form.get("preamble", "").replace('\r\n', '\n')
  source = request.form.get("source", "").replace('\r\n', '\n')
  kw = {**kw, 'preamble': preamble}

  key = config.CACHE_KEY(preamble, source)
  CACHED = config.CACHE_DIR / (key + ext)

  if not CACHED.exists():
    ok, out = fn(source, **kw)
    if not ok:
      return Response(out, mimetype="text/plain", status=500)
    CACHED.write_bytes(out)

  CACHED.touch()
  return send_file(CACHED, mimetype=mime)

if __name__ == '__main__':
    app.run(config.HOST, port=config.PORT, debug=True)
