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

# UI strings for each supported language.
TRANSLATIONS = {
    "中文": {
        "title": "漢字筆畫顯示器",
        "caption": "使用 makemeahanzi graphics.txt 資料，每一筆畫以不同顏色顯示。",
        "input_label": "請輸入一個漢字：",
        "input_placeholder": "輸入完成後按 Enter，或點「顯示」",
        "input_help": "支援注音／拼音輸入法，選好字後按 Enter。",
        "show": "顯示",
        "copy": "📋 複製圖片",
        "copied": "已複製到剪貼簿！",
        "copy_failed": "複製失敗：",
        "download": "⬇️ 下載 PNG",
        "not_found": "找不到字「{ch}」",
        "no_strokes": "此字沒有筆畫資料。",
        "multi": "偵測到多個字元，只顯示第一個字：「{ch}」",
        "stroke_failed": "第 {i} 筆繪製失敗：{e}",
    },
    "English": {
        "title": "Hanzi Stroke Viewer",
        "caption": "Renders each stroke in a distinct color using the makemeahanzi graphics.txt dataset.",
        "input_label": "Enter a Chinese character:",
        "input_placeholder": "Type a character and press Enter, or click Show",
        "input_help": "Works with Zhuyin/Pinyin IMEs. After selecting the character, press Enter.",
        "show": "Show",
        "copy": "📋 Copy image",
        "copied": "Copied to clipboard!",
        "copy_failed": "Copy failed: ",
        "download": "⬇️ Download PNG",
        "not_found": "Character not found: 「{ch}」",
        "no_strokes": "This character has no stroke data.",
        "multi": "Multiple characters detected; showing only the first: 「{ch}」",
        "stroke_failed": "Stroke {i} failed to render: {e}",
    },
}


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


def build_figure(strokes, t):
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
            st.warning(t["stroke_failed"].format(i=i + 1, e=e))

    return fig


def figure_to_png(fig):
    """Render a figure to transparent PNG bytes."""
    buf = BytesIO()
    fig.savefig(buf, format="png", transparent=True, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def copy_button(png_bytes, t):
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
          status.textContent = "__COPIED__";
        } catch (e) {
          status.style.color = "#c62828";
          status.textContent = "__FAILED__" + e;
        }
      });
    </script>
    """
    html = (
        html.replace("__LABEL__", t["copy"])
        .replace("__COPIED__", t["copied"])
        .replace("__FAILED__", t["copy_failed"])
        .replace("__B64__", b64)
    )
    components.html(html, height=50)


def resolve_char(word_input, t):
    """Return the first character of the input, warning if extra characters were given."""
    cleaned = word_input.strip()
    if not cleaned:
        return None
    ch = cleaned[0]
    if len(cleaned) > 1:
        st.info(t["multi"].format(ch=ch))
    return ch


# ── Language selector ──
lang = st.radio("🌐 Language / 語言", list(TRANSLATIONS.keys()), horizontal=True)
t = TRANSLATIONS[lang]

# ── UI ──
st.title(t["title"])
st.caption(t["caption"])

word_input = st.text_input(
    t["input_label"],
    placeholder=t["input_placeholder"],
    help=t["input_help"],
)

# Action row: Show, Download, and Copy buttons sit side by side. The Download
# and Copy buttons only appear once a character has been rendered into a PNG.
col_show, col_download, col_copy = st.columns([1, 1, 2])
show_btn = col_show.button(t["show"], use_container_width=True)

if show_btn or word_input:
    ch = resolve_char(word_input, t)
    if ch:
        data = get_char_data(ch)
        if not data:
            st.error(t["not_found"].format(ch=ch))
        elif not data.get("strokes"):
            st.error(t["no_strokes"])
        else:
            png_bytes = figure_to_png(build_figure(data["strokes"], t))

            # Download and Copy buttons: same row as Show.
            col_download.download_button(
                t["download"],
                data=png_bytes,
                file_name=f"{ch}.png",
                mime="image/png",
                use_container_width=True,
            )
            with col_copy:
                copy_button(png_bytes, t)

            # Rendered character below the action row.
            st.image(png_bytes, use_container_width=False)
