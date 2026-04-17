import streamlit as st
import json
from svgpath2mpl import parse_path
from matplotlib.patches import PathPatch
import matplotlib.pyplot as plt

STROKE_COLORS = [
    "#E24B4A", "#378ADD", "#1D9E75", "#EF9F27",
    "#D4537E", "#7F77DD", "#D85A30", "#639922",
    "#BA7517", "#185FA5",
]

def get_char_data(ch, filepath="graphics.txt"):
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("character") == ch:
                    return data
            except json.JSONDecodeError:
                continue
    return None


def render_char(ch):
    data = get_char_data(ch)
    if not data:
        st.error(f"找不到字「{ch}」")
        return

    strokes = data.get("strokes", [])
    if not strokes:
        st.error("此字沒有筆畫資料")
        return

    # 1. 建立畫布時，將面色 (facecolor) 設為 None (代表透明)
    fig, ax = plt.subplots(figsize=(5, 5), facecolor='none')
    ax.set_aspect("equal")
    ax.axis("off")

    # 2. 強制設定軸的背景也為透明
    ax.set_facecolor("none")

    # 座標設定 (使用之前修正過的 Y 軸朝上邏輯)
    ax.set_xlim(-50, 1074)
    ax.set_ylim(-150, 950)

    errors = []
    for i, d in enumerate(strokes):
        try:
            path = parse_path(d)
            color = STROKE_COLORS[i % len(STROKE_COLORS)]
            patch = PathPatch(
                path,
                facecolor=color,
                edgecolor=color,
                lw=0,
                alpha=0.9
            )
            ax.add_patch(patch)
        except Exception as e:
            errors.append(f"第 {i + 1} 筆：{e}")

    # 3. 關鍵：在 streamlit 顯示時，告知 matplotlib 使用透明背景
    st.pyplot(fig, transparent=True)
    plt.close(fig)

# ── 介面 ──
st.title("漢字筆畫顯示器")
st.caption("使用 makemeahanzi graphics.txt 資料，每筆不同顏色顯示")


word_input = st.text_input(
    "請輸入一個漢字：",
    placeholder="輸入完成後按 Enter 或點顯示",
    help="支援注音、拼音輸入法，輸入完成選字後按 Enter"
)

show_btn = st.button("顯示", use_container_width=False)

if show_btn or word_input:
    # 取輸入的第一個字元（過濾掉空白）
    cleaned = word_input.strip()
    if cleaned:
        ch = cleaned[0]  # 只取第一個字
        if len(cleaned) > 1:
            st.info(f"偵測到多個字元，只顯示第一個字：「{ch}」")
        render_char(ch)