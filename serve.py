from flask import Flask, request, Response, send_file, url_for
from pathlib import Path
import hashlib
import time
import config
import mimetypes

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
  format_ = config.formats[fmt]
  src = Path('./tikz.js').read_text() + f'\nprocessTikz("{url_for("generate", fmt=fmt, _external=True)}", {format_['em-size']})\n'
  return Response(src, mimetype="text/javascript")

@app.route("/<fmt>", methods=["OPTIONS"])
def cors_preflight():
  response = make_response()
  response.headers.add("Access-Control-Allow-Origin", "*")
  response.headers.add('Access-Control-Allow-Headers', "*")
  response.headers.add('Access-Control-Allow-Methods', "*")
  return response

def corsify(response):
  response.headers.add("Access-Control-Allow-Origin", "*")
  return response

@app.route("/<fmt>", methods=["POST"])
def generate(fmt):
  format_ = config.formats[fmt]

  preamble = request.form.get("preamble", "").replace('\r\n', '\n')
  source = request.form.get("source", "").replace('\r\n', '\n')
  kw = {**format_['options'], 'preamble': preamble}

  key = config.CACHE_KEY(preamble, source)
  ext = mimetypes.guess_extension(format_['mimetype'])
  filename = f"{key}-{fmt}{ext}"
  CACHED = config.CACHE_DIR / filename

  if not CACHED.exists():
    ok, out = format_['renderer'](source, **kw)
    if not ok:
      return corsify(Response(out, mimetype="text/plain", status=500))
    CACHED.write_bytes(out)

  CACHED.touch()
  return corsify(send_file(CACHED, mimetype=format_['mimetype']))

if __name__ == '__main__':
    app.run(config.HOST, port=config.PORT, debug=True)
