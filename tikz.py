import tempfile
from pathlib import Path
import subprocess

def render(source, libs=["amssymb", "amsmath", "tikz", "circuitikz"], format="png"):
  document = f"""
\\documentclass[margin=0pt]{{standalone}}
\\usepackage{{{",".join(libs)}}}
\\begin{{document}}
{source}
\\end{{document}}
  """.strip()

  with tempfile.TemporaryDirectory() as base:
    path = Path(base)
    name = 'document'
    (path / (name+'.tex')).write_text(document)
    try:
      subprocess.run(["pdflatex", "-halt-on-error", name], cwd=path, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
      return False, e.output
    match format:
      case "png":
        subprocess.run(["pdftocairo", "-png", "-transp", "-r", "600", "-singlefile", f"{name}.pdf", name], cwd=path, capture_output=True, check=True)
        return True, (path / (name+'.png')).read_bytes()
      case "svg":
        subprocess.run(["pdf2svg", f"{name}.pdf", f"{name}.svg"], cwd=path, capture_output=True, check=True)
        return True, (path / (name+'.svg')).read_text()
      case _:
        raise Exception(f"Unknown format {format}")
