#!/usr/bin/env python3
import sys
from bs4 import BeautifulSoup
from PIL import Image
import argparse
import config
import base64

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
    else:
      w, h = Image.open(CACHED).size

    img = BeautifulSoup('<img>', 'html.parser').img
    img['class'] = 'tikz'
    img['src'] = f"data:{mime};base64,{base64.b64encode(image).decode()}"
    img['style'] = f"width:{w / scale}em;"
    script.replace_with(img)
    # print(img)
  except Exception as e:
    print(e, file=sys.stderr)

def process(file, fmt, inplace=False):
  with open(file, 'r') as fp:
    contents = fp.read()
    soup = BeautifulSoup(f'<pre>{contents}</pre>', 'html.parser')

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

  output = str(soup.pre)
  output = output.removeprefix('<pre>')
  output = output.removesuffix('</pre>')
  if inplace:
    with open(file, 'w') as fp:
      fp.write(output)
  else:
    print(output)

def main():
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group(required=False)
  for fmt in config.formats:
    group.add_argument(f"-{fmt}", dest="format", action='store_const', const=fmt)
  parser.add_argument('-inplace', action='store_true')
  parser.add_argument('files', metavar='file', type=str, nargs='+')
  parser.set_defaults(format='png')
  args = parser.parse_args()
  for file in args.files:
    process(file, fmt=args.format, inplace=args.inplace)

if __name__ == '__main__':
  main()
