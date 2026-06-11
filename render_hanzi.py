import base64
import json
from io import BytesIO

import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components
from matplotlib.patches import PathPatch
from svgpath2mpl import parse_path

# Stroke color order: red, orange, yellow, green, blue, purple, pink, black, brown.
# Strokes beyond the 9th wrap back around to red, orange, ...
STROKE_COLORS = [
    "#FF0000",  # red
    "#FF8C00",  # orange
    "#FFD700",  # yellow
    "#008000",  # green
    "#0000FF",  # blue
    "#800080",  # purple
    "#FF69B4",  # pink
    "#000000",  # black
    "#8B4513",  # brown
]


def get_char_data(ch, filepath="graphics.txt"):
    """Look up a single character's stroke data in the makemeahanzi dataset."""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("character") == ch:
                    return data
            except json.JSONDecodeError:
                continue
    return None


def build_figure(strokes):
    """Draw the strokes onto a transparent Matplotlib figure, one color per stroke."""
    fig, ax = plt.subplots(figsize=(5, 5), facecolor="none")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor("none")

    # makemeahanzi paths use a 1024x1024 grid with the baseline near y=0.
    ax.set_xlim(-50, 1074)
    ax.set_ylim(-150, 950)

    for i, d in enumerate(strokes):
        try:
            path = parse_path(d)
            color = STROKE_COLORS[i % len(STROKE_COLORS)]
            patch = PathPatch(path, facecolor=color, edgecolor=color, lw=0, alpha=0.9)
            ax.add_patch(patch)
        except Exception as e:
            st.warning(f"Stroke {i + 1} failed to render: {e}")

    return fig


def figure_to_png(fig):
    """Render a figure to transparent PNG bytes."""
    buf = BytesIO()
    fig.savefig(buf, format="png", transparent=True, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def copy_button(png_bytes, label="📋 Copy image"):
    """Render an HTML button that copies the PNG to the clipboard via the Clipboard API.

    Note: clipboard image writes require a secure context (HTTPS or localhost).
    """
    b64 = base64.b64encode(png_bytes).decode()
    html = """
    <div style="display:flex; gap:10px; align-items:center; font-family:sans-serif;">
      <button id="copyBtn" style="padding:6px 14px; font-size:14px; cursor:pointer;
              border:1px solid #ccc; border-radius:6px; background:#f6f6f6;">__LABEL__</button>
      <span id="copyStatus" style="font-size:13px; color:#2e7d32;"></span>
    </div>
    <script>
      const b64 = "__B64__";
      document.getElementById("copyBtn").addEventListener("click", async () => {
        const status = document.getElementById("copyStatus");
        try {
          const res = await fetch("data:image/png;base64," + b64);
          const blob = await res.blob();
          await navigator.clipboard.write([new ClipboardItem({"image/png": blob})]);
          status.style.color = "#2e7d32";
          status.textContent = "Copied to clipboard!";
        } catch (e) {
          status.style.color = "#c62828";
          status.textContent = "Copy failed: " + e;
        }
      });
    </script>
    """
    html = html.replace("__LABEL__", label).replace("__B64__", b64)
    components.html(html, height=50)


def render_char(ch):
    """Render a character and show it with download and copy controls."""
    data = get_char_data(ch)
    if not data:
        st.error(f"Character not found: 「{ch}」")
        return

    strokes = data.get("strokes", [])
    if not strokes:
        st.error("This character has no stroke data.")
        return

    png_bytes = figure_to_png(build_figure(strokes))

    st.image(png_bytes, use_container_width=False)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.download_button(
            "⬇️ Download PNG",
            data=png_bytes,
            file_name=f"{ch}.png",
            mime="image/png",
        )
    with col2:
        copy_button(png_bytes)


# ── UI ──
st.title("Hanzi Stroke Viewer")
st.caption("Renders each stroke in a distinct color using the makemeahanzi graphics.txt dataset.")

word_input = st.text_input(
    "Enter a Chinese character:",
    placeholder="Type a character and press Enter, or click Show",
    help="Works with Zhuyin/Pinyin IMEs. After selecting the character, press Enter.",
)

show_btn = st.button("Show", use_container_width=False)

if show_btn or word_input:
    # Take the first non-whitespace character of the input.
    cleaned = word_input.strip()
    if cleaned:
        ch = cleaned[0]
        if len(cleaned) > 1:
            st.info(f"Multiple characters detected; showing only the first: 「{ch}」")
        render_char(ch)
