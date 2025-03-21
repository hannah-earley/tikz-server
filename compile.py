#!/usr/bin/env python3
import sys
from bs4 import BeautifulSoup
from PIL import Image
import argparse
import config
import cache
import base64
import urllib
import io

def svg_uri(svg):
  lineless = svg.decode().replace('\n','')
  quoted = urllib.parse.quote(lineless, safe="' =/:;,")
  return "data:image/svg+xml;utf8," + quoted

def binary_uri(image, mimetype):
  return f"data:{mimetype};base64,{base64.b64encode(image).decode()}"

def preprocess_script(fmt, preamble, source, compiles=1, verbose=False):
  """
  Prerender scripts; intended to be used with multithreading to accelerate compilation.
  """

  try:
    format_ = config.formats[fmt]
    kw = {
      **format_['options'],
      'preamble': preamble,
      'compiles': compiles
    }
    filename = cache.filename(preamble, source, fmt)
    image = cache.cached(format_['renderer'])(filename, source, **kw)

    if verbose:
      print('.', end='', file=sys.stderr, flush=True)

  except Exception as e:
    pass

def process_script(script, fmt, preamble, source, compiles=1, verbose=False):
  """
  Replace the given script element with a rendered copy. This behavior should
  be identical to that of tikz.js (at least when no errors occur).
  """

  try:
    format_ = config.formats[fmt]
    kw = {
      **format_['options'],
      'preamble': preamble,
      'compiles': compiles
    }

    filename = cache.filename(preamble, source, fmt)
    image = cache.cached(format_['renderer'])(filename, source, **kw)

    if format_['mimetype'] == 'image/svg+xml':
      soup = BeautifulSoup(image.decode(), "xml")
      svg, = soup.find_all('svg', recursive=False)

      # we use int(...) to be consistent with tikz.js, which uses
      # img.naturalWidth which is the rounded width of the image; for more
      # accurate sizing, this outermost conversion may be removed
      w = int(float(svg['width']))

      element = BeautifulSoup('<object>', 'html.parser').object
      element['type'] = 'image/svg+xml'
      element['data'] = svg_uri(image)

    else:
      w, _h = Image.open(io.BytesIO(image)).size

      element = BeautifulSoup('<img>', 'html.parser').img
      element['src'] = binary_uri(image, format_['mimetype'])

    w_em = w / format_['em-size']
    element['class'] = 'tikz'
    element['style'] = f"width:{w_em}em;"
    script.replace_with(element)

    if verbose:
      print('.', end='', file=sys.stderr, flush=True)

  except Exception as e:
    print(e, file=sys.stderr)

def process(file, fmt, inplace=False, preserve_ws=True, threading=False):
  with open(file, 'r') as fp:
    contents = fp.read()

  if preserve_ws:
    # hack to enable whitespace preservation in BeautifulSoup
    soup = BeautifulSoup(f'<pre>{contents}</pre>', 'html.parser')
  else:
    soup = BeautifulSoup(contents, 'html.parser')

  for script in soup.find_all(class_="tikz-server"):
    script.decompose()

  preamble = ""
  for script in soup.find_all("script", type="preamble"):
    preamble += script.string
    script.decompose()

  if threading:
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=threading) as executor:
      for script in soup.find_all("script", type="tex"):
        fmt2 = script.get("data-format", fmt)
        compiles = int(script.get("data-compile", "1"))
        content = script.string
        executor.submit(preprocess_script, fmt2, preamble, content, compiles, verbose=True)
      for script in soup.find_all("script", type="tikz"):
        fmt2 = script.get("data-format", fmt)
        compiles = int(script.get("data-compile", "1"))
        content = "\\begin{tikzpicture}" + script.string + "\\end{tikzpicture}"
        executor.submit(preprocess_script, fmt2, preamble, content, compiles, verbose=True)

  for script in soup.find_all("script", type="tex"):
    fmt2 = script.get("data-format", fmt)
    compiles = int(script.get("data-compiles", "1"))
    content = script.string
    process_script(script, fmt2, preamble, content, compiles, verbose=not threading)

  for script in soup.find_all("script", type="tikz"):
    fmt2 = script.get("data-format", fmt)
    compiles = int(script.get("data-compiles", "1"))
    content = "\\begin{tikzpicture}" + script.string + "\\end{tikzpicture}"
    process_script(script, fmt2, preamble, content, compiles, verbose=not threading)

  print('', file=sys.stderr)

  if preserve_ws:
    output = str(soup.pre)
    output = output.removeprefix('<pre>')
    output = output.removesuffix('</pre>')
  else:
    output = str(soup)

  if inplace:
    with open(file, 'w') as fp:
      fp.write(output)
  else:
    print(output)

def main():
  cache.clean()

  parser = argparse.ArgumentParser(add_help=False, description="Replaces tikz/tex 'scripts' in an HTML file(s) with rendered copies of specified format.")
  parser.add_argument('-h', '-help', help="Show this help message", action='help')

  group = parser.add_argument_group('format')
  group1 = group.add_mutually_exclusive_group(required=False)
  for fmt, format_ in config.formats.items():
    group1.add_argument(f"-{fmt}", dest="format", action='store_const', const=fmt, help=format_['description'])
  parser.set_defaults(format='png')

  parser.add_argument('-inplace', action='store_true', help="Overwrite input files in-place, otherwise outputs to stdout")
  parser.add_argument('-preserve', action='store_true', help="Preserve whitespace")
  parser.add_argument('-threading', action='store', type=int, metavar='T', help="Activate threading with T threads (T=0 uses number of CPU cores)", default=False)
  parser.add_argument('files', metavar='file', type=str, nargs='+', help="Input HTML file(s)")

  args = parser.parse_args()

  cores = args.threading
  if cores == 0:
    import multiprocessing
    cores = multiprocessing.cpu_count()

  for file in args.files:
    process(file, fmt=args.format, inplace=args.inplace, preserve_ws=args.preserve, threading=cores)

if __name__ == '__main__':
  main()
