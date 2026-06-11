# Hanzi Stroke Viewer

A small [Streamlit](https://streamlit.io/) app that renders any Chinese character
stroke by stroke, giving each stroke a distinct color. Built on the
[makemeahanzi](https://github.com/skishore/makemeahanzi) `graphics.txt` dataset.

## Features

- Render any single Chinese character from its stroke outlines.
- Each stroke is drawn in a fixed color order — **red, orange, yellow, green,
  blue, purple, pink, black, brown** — wrapping back to red for the 10th stroke
  onward.
- Transparent PNG output.
- **Download** the rendered image as a PNG.
- **Copy** the image straight to your clipboard.
- Bilingual UI: switch between **中文** and **English**.

## Requirements

- Python 3.8+
- The `graphics.txt` dataset (already included in this repo).

Python dependencies are listed in [`requirements.txt`](requirements.txt):

```
streamlit
matplotlib
svgpath2mpl
```

## Installation

```bash
git clone https://github.com/EdwardLien0426/Render_hanzi.git
cd Render_hanzi
pip install -r requirements.txt
```

## Usage

```bash
streamlit run render_hanzi.py
```

Then open the local URL Streamlit prints (usually <http://localhost:8501>),
type a character, and press **Enter** or click **Show**.

> **Note on the copy button:** copying an image to the clipboard requires a
> secure context (HTTPS or `localhost`). It works out of the box when running
> locally; if you deploy the app, serve it over HTTPS.

## How it works

1. `get_char_data` scans `graphics.txt` (one JSON object per line) for the
   requested character.
2. `build_figure` parses each stroke's SVG path with `svgpath2mpl` and draws it
   as a filled Matplotlib patch, picking the next color from `STROKE_COLORS`.
3. The figure is exported to a transparent PNG, which is then shown, offered for
   download, and made available to the clipboard-copy button.

## Customizing the colors

Edit the `STROKE_COLORS` list near the top of `render_hanzi.py`. Strokes are
colored by index, cycling through the list, so you can use any number of colors.

## Data source & license

Stroke data comes from [makemeahanzi](https://github.com/skishore/makemeahanzi),
which is distributed under the Arphic Public License and LGPL. Please review and
comply with the upstream license when redistributing the dataset.
