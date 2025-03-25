# Ti*k*Z-server

_Note: This is tested on macOS, it will probably work as-is on linux, but changes may be required for Windows._

This project allows TikZ pictures, animations, or standalone LaTeX documents in general to be embedded in HTML documents and rendered on demand. The rendering is cached, so that large documents with many TikZ pictures can be rendered quickly and efficiently.

The project includes two utilities:

- A webserver (written in python using flask) that enables the dynamic replacement of embedded TikZ/LaTeX on page load
- A 'compiler' that replaces embedded TikZ/LaTeX in the page source with rendered copies

## Setup

The easiest way to use TikZ-Server is with docker.
Run it as

```bash
docker run --rm -d -p 8459:5000 ghcr.io/hannah-earley/tikz-server:latest
```

...or pick another port besides 8459 if you prefer.

To run it as a service that starts on boot, use

```bash
docker run -d -p 8459:5000 --restart unless-stopped ghcr.io/hannah-earley/tikz-server:latest
```

instead.

If you prefer not to use Docker, you should install the below requirements:

- python3
  - flask
  - beautifulsoup4
  - Pillow
  - lxml
- latex
  - dvisvgm
- poppler
  - pdftocairo
  - pdf2svg

Running outside of docker works on macOS, should work on linux, and is not tested on Windows.

## Supported rendering formats

- `png`: High quality raster (default 720dpi).
- `svg`: Vector.
- `svg2`: Vector, but with animation support; the SVGs include an embedded script that pauses animation on mouseover.

## Usage (general)

LaTeX is embedded using custom script tags, for example a simple TikZ embedding is as follows:

```html
<script type="tikz">
  \draw (0,0) node[above]{Hello, world!};
</script>
```

This automatically wraps the contents in `\begin{tikzpicture}` / `\end{tikzpicture}`. For more general LaTeX bodies, use:

```html
<script type="tex">
  Hello, world $n! = \prod_{k=1}^n k$.
</script>
```

Custom preambles may be assembled using one or more dedicated scripts:

```html
<script type="preamble">
  \usepackage{pgfplots}
  \pgfplotsset{compat=1.18}
</script>
<script type="preamble">
  \usetikzlibrary{arrows.meta,shapes.geometric,shapes.symbols,animations}
  \ctikzset{tripoles/pmos style/emptycircle}
  \ctikzset{logic ports=ieee}
  \ctikzset{american inductors}
</script>
```

All preamble scripts are found, combined, and applied to all TikZ and TeX on the page. Currently it is not possible to use different preambles for different TeX scripts.

_N.B. Default packages loaded are `amssymb`, `amsmath`, `tikz`, `circuitikz`._

While the compilation can also be used for math, it may be preferable to use something like [MathJax](https://www.mathjax.org) or [KaTeX](https://katex.org) for better inline support and to avoid spinning up an entire latex compiler for each.

You may like to add styling for the rendered documents. Rasters will be rendered as img tags with class `tikz`, and SVGs as object tags (also with class `tikz`):

```css
img.tikz, object.tikz {
  display: block;
  margin: 2em auto;
  max-width: 100%;
}
```

You may also wish to style the scripts as a fallback in case they are not rendered, and the error messages that may be added in case of compilation failure:

```css
script[type=tikz], script[type=tex] {
  border: 1px solid black;
}
div.tikz-error {
  border: 1px solid red;
  margin-top: -1px;
}
script[type=tikz], script[type=tex], div.tikz-error {
  margin-left: auto;
  margin-right: auto;
  display: block;
  unicode-bidi: embed;
  white-space: pre-wrap;
  padding: 1em;
  max-height: 10em;
  overflow: scroll;
  font-size: 0.7em;
}
```

## Usage (webserver)

1. Launch the server with `./serve.py` (should be run from the repository's directory)
2. Include the client-side script in an HTML document:

    ```html
    <script defer src="http://localhost:8459/tikz.js" class="tikz-server"></script>
    ```

    The class allows the script to be stripped when using the compiler.

## Usage (compiler)

Execute `/path/to/tikz-server/compile.py document.html`.

```
usage: compile.py [-h] [-png | -svg | -svg2] [-inplace] [-preserve] [-threading T] file [file ...]

Replaces tikz/tex 'scripts' in an HTML file(s) with rendered copies of specified format.

positional arguments:
  file          Input HTML file(s)

options:
  -h, -help     Show this help message
  -inplace      Overwrite input files in-place, otherwise outputs to stdout
  -preserve     Preserve whitespace
  -threading T  Activate threading with T threads (T=0 uses number of CPU cores)

format:
  -png          High quality PNG raster format
  -svg          SVG vector format
  -svg2         SVG vector format with animation support
```

## Example jekyll workflow

### Development

```bash
jekyll serve --livereload --force_polling
```

_You may want to add a tall blank div at the end of the page during development to accommodate the page height changes during rendering on livereload._

### Deployment

```bash
jekyll build --config _config.deploy.yml
find _site -type f -name "*.html" -print -exec /path/to/tikz-server/compile.py -svg2 -inplace {} \;
rsync --progress --dry-run --delete -avi _site/ /path/to/destination
```

## Advanced usage

The scripts support some optional arguments:

```html
<script type="tex" data-compile="2" data-format="svg"></script>
```

- The number of compilations can be specified (default is 1). This is useful for, e.g., `tikzmark`.
- The format can be changed on a per-script basis. For example, `tikzmark` doesn't work with `svg2`, so the format can be overriden to `svg`.


## Related projects

- [TikZJax](https://tikzjax.com) is an entirely client-side solution that embeds (using WASM) the full LaTeX engine (with TikZ loaded), and converts the DVI output to SVG in-browser too. The main differences that tikz-server offers are that it can do caching, offline compilation, animations, and supports arbitrary additional packages and TikZ libraries (e.g. CircuiTikZ).
