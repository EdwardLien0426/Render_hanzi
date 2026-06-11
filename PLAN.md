# 開發計畫 / TODO（接續用）

> 最後更新：2026-06-10
> Live demo: <https://renderhanzigit-ra9powgf4tbak6besj8wje.streamlit.app/>
> Repo: <https://github.com/EdwardLien0426/Render_hanzi>

這份檔案記錄目前進度與「下次要繼續處理的事」，方便下次接手。

---

## 待辦（下次優先）

### 1. 筆順數字還是怪怪的，要再調 ⭐
目前數字（白字 + 淡黑描邊、size 10、放在筆畫中點）雖然比之前融入，但**整體看起來還是怪**，需要再想辦法。可考慮的方向：

- **位置**：現在用 `median[len(median)//2]`（筆畫中點）。複雜字（如「驚」23 畫）數字會擠在一起、互相重疊。可考慮：
  - 偵測重疊並自動微調位置；或
  - 放在筆畫「起點」但往內縮一點；或
  - 限制只有筆畫夠長才標數字。
- **樣式**：目前是白字 + `rgba(0,0,0,0.45)` 淡描邊。可試：
  - 小圓底（badge）襯底，數字放圓內；
  - 跟著「該筆畫的顏色」做深一階／淺一階，讓它像同一筆的一部分；
  - 兩位數時自動再縮小。
- **要不要改預設**：目前 `顯示筆順號碼` 預設**開**。若覺得太干擾，可改成預設關。

相關程式：`render_hanzi.py` → `build_figure()` 裡的 `ax.text(...)` 區塊。
可調參數：`fontsize`、`color`、`alpha`、`path_effects` 的 `linewidth`/`foreground`、以及取點的 index。

---

## 目前已完成（現況）

- 單檔 Streamlit app：`render_hanzi.py`，資料 `graphics.txt`（makemeahanzi）。
- 筆畫顏色固定順序：紅橙黃綠藍紫粉黑棕，超過 9 畫循環。
- **下載 PNG / 複製圖片**：都是透明去背；畫面上的白卡片只是顯示用。
- **中文 / English** 語言切換（radio）。
- **黑夜模式**：用 `st.toggle`（不是 radio）。原因：radio + 多語言會出現「點一下被拉扯回去 / 切語言把主題重置 / 勾選狀態消失」等 Streamlit 怪象，toggle 沒有這些問題。`.streamlit/config.toml` 把 light 設成底層主題，dark 用 CSS 疊加。
- **效能快取**：`load_index()`（`st.cache_resource`，整檔解析成 dict，查字 O(1)）+ `render_png(ch, show_numbers)`（`st.cache_data`，每個字的 PNG 快取）。切主題／語言從 ~0.57s 降到 ~0.01s。
- **筆順數字**：toggle 開關 + 畫在筆畫上（見上方待辦，還要再調）。

---

## 本機開發 / 測試方式

```bash
pip install -r requirements.txt
streamlit run render_hanzi.py     # http://localhost:8501
```

### ⚠️ 重要踩雷紀錄
- 在 Windows 上，**git-bash 的 `pkill -f "streamlit run"` 殺不掉**那個 python 程序（ps 看不到），會留下一堆殭屍 streamlit 程序佔著 8501，導致「改了程式卻沒生效」。
- 要重啟請用 PowerShell 殺乾淨：
  ```powershell
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*streamlit*run*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
  ```
- 用瀏覽器（chrome-devtools）實際點過再下結論，不要只靠語法檢查。

---

## 已知小事項
- 執行時會出現 `st.components.v1.html will be removed` 的 deprecation 警告（複製按鈕用到的 iframe）。目前仍可運作；未來 Streamlit 真的移除時要換新 API。
- chrome-devtools 的 `fill` 對已有值的輸入框會「接在後面」而不是覆蓋；測試換字時要先清空。
