import tempfile
from pathlib import Path
import subprocess

def render(source, preamble="", libs=["amssymb", "amsmath", "tikz", "circuitikz"], format="png", timeout=5):
  document = f"""
\\documentclass[margin=0pt,crop]{{standalone}}
\\usepackage{{{",".join(libs)}}}
{preamble}
\\begin{{document}}
{source}
\\end{{document}}
  """.strip()

  with tempfile.TemporaryDirectory() as base:
    path = Path(base)
    call = lambda *a, **k: subprocess.run(a, **k, cwd=path, capture_output=True, check=True, timeout=timeout)

    name = 'document'
    (path / (name+'.tex')).write_text(document)
    try:
      call("texfot", "pdflatex", "-halt-on-error", name)
    except subprocess.CalledProcessError as e:
      return False, '\n'.join(e.output.decode().strip().split('\n')[2:-1])
    match format:
      case "png":
        call("pdftocairo", "-png", "-transp", "-r", "720", "-singlefile", f"{name}.pdf", name)
        return True, (path / (name+'.png')).read_bytes()
      case "svg":
        call("pdf2svg", f"{name}.pdf", f"{name}.svg")
        return True, (path / (name+'.svg')).read_bytes()
      case _:
        raise Exception(f"Unknown format {format}")
