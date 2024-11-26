#!/usr/bin/env python3
import sys
from bs4 import BeautifulSoup
from PIL import Image
import argparse
import config
import base64
import urllib

def process_script(script, fmt, preamble, source):
  try:
    fn, kw, ext, mime, scale = config.formats[fmt]
    kw = {**kw, 'preamble': preamble}

    key = config.CACHE_KEY(preamble, source)
    CACHED = config.CACHE_DIR / (key + ext)

    try:
      if not CACHED.exists():
        ok, out = fn(source, **kw)
        if not ok:
          raise Exception(out)
        CACHED.write_bytes(out)
    except:
      raise

    CACHED.touch()
    image = CACHED.read_bytes()

    if mime == 'image/svg+xml':
      soup = BeautifulSoup(image.decode(), "xml")
      svg, = soup.find_all('svg', recursive=False)
      w, h = float(svg['width']), float(svg['height'])
      uri = "data:image/svg+xml;utf8," + urllib.parse.quote(image.decode().replace('\n',''), safe="' =/:;,")
      element = BeautifulSoup('<object>', 'html.parser').object
      element['type'] = 'image/svg+xml'
      element['data'] = uri
    else:
      w, h = Image.open(CACHED).size
      uri = f"data:{mime};base64,{base64.b64encode(image).decode()}"
      element = BeautifulSoup('<img>', 'html.parser').img
      element['src'] = uri

    element['class'] = 'tikz'
    element['style'] = f"width:{int(w) / scale}em;"
    script.replace_with(element)
  except Exception as e:
    print(e, file=sys.stderr)

def process(file, fmt, inplace=False, preserve_ws=True):
  with open(file, 'r') as fp:
    contents = fp.read()
  if preserve_ws:
    soup = BeautifulSoup(f'<pre>{contents}</pre>', 'html.parser')
  else:
    soup = BeautifulSoup(contents, 'html.parser')

  for script in soup.find_all(class_="tikz-server"):
    script.decompose()

  preamble = ""
  for script in soup.find_all("script", type="preamble"):
    preamble += script.string
    script.decompose()

  for script in soup.find_all("script", type="tex"):
    process_script(
      script,
      fmt,
      preamble,
      script.string)

  for script in soup.find_all("script", type="tikz"):
    process_script(
      script,
      fmt,
      preamble,
      "\\begin{tikzpicture}" + script.string + "\\end{tikzpicture}")

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
  parser = argparse.ArgumentParser(add_help=False, description="Replaces tikz/tex 'scripts' in an HTML file(s) with rendered copies of specified format.")
  parser.add_argument('-h', '-help', help="Show this help message", action='help')
  group = parser.add_argument_group('format')
  group1 = group.add_mutually_exclusive_group(required=False)
  for fmt, format_ in config.formats.items():
    group1.add_argument(f"-{fmt}", dest="format", action='store_const', const=fmt, help=format_['description'])
  parser.add_argument('-inplace', action='store_true', help="Overwrite input files in-place, otherwise outputs to stdout")
  parser.add_argument('-preserve', action='store_true', help="Preserve whitespace")
  parser.add_argument('files', metavar='file', type=str, nargs='+', help="Input HTML file(s)")
  parser.set_defaults(format='png')
  args = parser.parse_args()
  for file in args.files:
    process(file, fmt=args.format, inplace=args.inplace, preserve_ws=args.preserve)

if __name__ == '__main__':
  main()
