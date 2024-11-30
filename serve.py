#!/usr/bin/env python3

from flask import Flask, request, Response, url_for
from pathlib import Path
import config
import cache
import tikz

app = Flask(__name__)

# Implement CORS

@app.route("/", defaults={'path': '/'}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def cors_preflight():
  response = make_response()
  response.headers.add("Access-Control-Allow-Origin", "*")
  response.headers.add('Access-Control-Allow-Headers', "*")
  response.headers.add('Access-Control-Allow-Methods', "*")
  return response

@app.after_request
def corsify(response):
  response.headers.add("Access-Control-Allow-Origin", "*")
  return response

# Cache cleaning

@app.before_request
def auto_clean():
  cache.clean(True)

@app.route('/clean')
def clean_cache():
  out = cache.clean(False)
  return Response('\n'.join(out), mimetype='text/plain')

# Client-side

@app.route('/tikz.js')
def js():
  fmt = request.args.get('format', default='png')
  format_ = config.formats[fmt]
  base = Path('./tikz.js').read_text()
  generator = url_for("generate", fmt=fmt, _external=True)
  init = f'\nprocessTikZ("{generator}", {format_['em-size']})\n'
  return Response(base + init, mimetype="text/javascript")

# Server-side

@app.route("/<fmt>", methods=["POST"])
def generate(fmt):
  fmt = request.form.get("format", fmt)
  format_ = config.formats[fmt]

  preamble = request.form.get("preamble", "").replace('\r\n', '\n')
  source = request.form.get("source", "").replace('\r\n', '\n')
  compiles = int(request.form.get("compiles", "1"))
  kw = {
    **format_['options'],
    'preamble': preamble,
    'compiles': compiles
  }

  try:
    filename = cache.filename(preamble, source, fmt)
    out = cache.cached(format_['renderer'])(filename, source, **kw)
    return Response(out, mimetype=format_["mimetype"])
  except tikz.LaTeXError as e:
    return Response(str(e), mimetype="text/plain", status=500)

#

if __name__ == '__main__':
    app.run(config.HOST, port=config.PORT, debug=True)
