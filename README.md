# README

This is a simple server which will compile and cache tikz pictures (or standalone latex documents in general) on demand, and can be called from a webpage to replace tikz source with images.

## Usage
`flask --app serve run --port=8459`

```html
<script defer src="http://localhost:8459/tikz.js"></script>
<script type="tikz">
  \draw (0,0) node[above]{Hello, world!};
</script>
```

## Requirements
- python3
  - flask
- latex
- poppler
  - pdftocairo
  - pdf2svg

