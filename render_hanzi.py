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
        "theme_label": "🎨 主題",
        "light": "☀️ 白天",
        "dark": "🌙 黑夜",
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
        "theme_label": "🎨 Theme",
        "light": "☀️ Light",
        "dark": "🌙 Dark",
    },
}

# Background / text / input / button colors for each theme.
THEMES = {
    "light": {
        "bg": "#FFFFFF", "fg": "#111111", "input_bg": "#FFFFFF",
        "border": "#CCCCCC", "btn_bg": "#F0F0F0",
    },
    "dark": {
        "bg": "#0E1117", "fg": "#FAFAFA", "input_bg": "#262730",
        "border": "#555555", "btn_bg": "#262730",
    },
}


def apply_theme(mode):
    """Override the app background, header bar, text, inputs, and buttons for the theme."""
    c = THEMES[mode]
    st.markdown(
        f"""
        <style>
          /* Pull content up toward the top, clear of the floating toolbar */
          .block-container {{ padding-top: 2rem; }}
          header[data-testid="stHeader"] {{ background-color: {c["bg"]}; }}

          .stApp {{ background-color: {c["bg"]}; color: {c["fg"]}; }}
          .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label,
          .stApp span, .stApp .stMarkdown {{ color: {c["fg"]} !important; }}

          /* Text input box */
          .stTextInput div[data-baseweb="input"],
          .stTextInput div[data-baseweb="base-input"] {{
              background-color: {c["input_bg"]}; border-color: {c["border"]};
          }}
          .stTextInput input {{
              background-color: {c["input_bg"]} !important; color: {c["fg"]} !important;
          }}

          /* Buttons (Show + Download) */
          .stButton > button, .stDownloadButton > button {{
              background-color: {c["btn_bg"]} !important;
              color: {c["fg"]} !important;
              border: 1px solid {c["border"]} !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def show_card(b64):
    """Display the rendered character on a white card so every stroke color stays
    visible regardless of the app theme (the black stroke in particular)."""
    st.markdown(
        f"""
        <div style="background:#FFFFFF; border-radius:12px; padding:16px;
                    display:inline-block; box-shadow:0 2px 10px rgba(0,0,0,0.2);">
          <img src="data:image/png;base64,{b64}" style="display:block; width:360px;"/>
        </div>
        """,
        unsafe_allow_html=True,
    )


def copy_button(b64, t):
    """Render an HTML button that copies the PNG to the clipboard via the Clipboard API.

    Note: clipboard image writes require a secure context (HTTPS or localhost).
    """
    html = """
    <style>html, body { margin:0; padding:0; }</style>
    <div style="display:flex; gap:10px; align-items:center; height:38px; font-family:sans-serif;">
      <button id="copyBtn" style="height:38px; padding:0 16px; font-size:14px; cursor:pointer;
              border:1px solid rgba(128,128,128,0.4); border-radius:8px; background:#f6f6f6;
              white-space:nowrap;">__LABEL__</button>
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
    components.html(html, height=44)


def resolve_char(word_input, t):
    """Return the first character of the input, warning if extra characters were given."""
    cleaned = word_input.strip()
    if not cleaned:
        return None
    ch = cleaned[0]
    if len(cleaned) > 1:
        st.info(t["multi"].format(ch=ch))
    return ch


# ── Language and theme selectors ──
col_lang, col_theme = st.columns(2)
with col_lang:
    lang = st.radio("🌐 Language / 語言", list(TRANSLATIONS.keys()), horizontal=True)
t = TRANSLATIONS[lang]
with col_theme:
    theme_choice = st.radio(t["theme_label"], [t["light"], t["dark"]], horizontal=True)
mode = "dark" if theme_choice == t["dark"] else "light"
apply_theme(mode)

# ── UI ──
st.title(t["title"])

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
            b64 = base64.b64encode(png_bytes).decode()

            # Download and Copy buttons: same row as Show.
            col_download.download_button(
                t["download"],
                data=png_bytes,
                file_name=f"{ch}.png",
                mime="image/png",
                use_container_width=True,
            )
            with col_copy:
                copy_button(b64, t)

            # Rendered character on a white card, below the action row.
            show_card(b64)
