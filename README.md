# Skill Tree CLI

給 IC / connsys 設計團隊使用的本機樹狀終端介面。第一版專注瀏覽與選取知識，尚未掃描 RTL、推導 constraints 或自動更新 skills。

## 快速開始（macOS / Linux）

需要 Python 3.9+、Git，以及支援 curses 的終端。無第三方執行期套件。

```sh
git clone https://github.com/JohnnySung88/connsys-skill-tree.git
cd connsys-skill-tree
python3 -m skill_tree examples/connsys
```

不安裝即可試用。若想在任意目錄使用 `skill-tree`：

```sh
python3 install.py
export PATH="$HOME/.local/bin:$PATH"
skill-tree examples/connsys
```

此安裝不需 pip、網路或管理員權限。可將 PATH 那行加入 `~/.zshrc` 或 `~/.bashrc`。命令連回本專案，因此安裝後請保留此資料夾；`git pull` 即可更新程式。重新安裝前需自行移除舊的 `~/.local/bin/skill-tree`，安裝器不覆蓋現有命令。

也可用 `python3 -m pip install .` 安裝 Python 套件；此方式可能需要下載建置套件。

## 操作

| 按鍵 | 功能 |
|---|---|
| ↑ / ↓ 或 k / j | 選取節點 |
| → | 展開 |
| ← | 收合，或回到父節點 |
| Enter | 展開／收合 |
| / | 輸入節點路徑關鍵字搜尋 |
| Esc | 清除搜尋 |
| PageUp / PageDown | 捲動右側原始 Markdown 預覽 |
| r | 重新讀取資料夾 |
| e | 匯出選定節點與祖先 SKILL.md（需指定 --output） |
| q | 離開 |

終端至少 60 欄、10 列。預覽過長的單行會截斷；完整內容可透過 context 匯出。

```sh
skill-tree /path/to/company-knowledge --output /tmp/rx-context.md
```

匯出不覆蓋已存在的檔案。資料僅在本機讀取，不呼叫 AI、不上傳任何內容、不執行 SKILL.md 中的指令。

## Codex / Claude Code / ChipAgents

在一般 terminal 使用互動介面。如果 AI 的執行環境未提供互動 TTY，使用同一套 CLI 的非互動模式：

```sh
python3 -m skill_tree examples/connsys --list
python3 -m skill_tree examples/connsys --json
python3 -m skill_tree examples/connsys --context IC_A/PHY/RX/AGC
python3 -m skill_tree examples/connsys --context IC_A/PHY/RX/AGC --output /tmp/agc-context.md
```

可對 AI 說：「執行 skill-tree 的 --list 找到 AGC 節點，再以 --context 讀取該節點，依來源回答問題。」本版提供工具中立的命令介面；未宣稱已完成各 AI 產品的原生選單或 session 注入。是否支援直接開 TUI 取決於該工具的 TTY。

## 知識格式 v1

資料夾就是節點，節點內的 `SKILL.md` 就是內容。沒有 SKILL.md 的中間層仍會顯示，只要下面有 skill。空資料夾不顯示，隱藏資料夾與符號連結不掃描。支援 UTF-8、中文資料夾與內容。

範例路徑：`examples/connsys/IC_A/PHY/RX/AGC/SKILL.md`。

建議每份文件包含 YAML frontmatter 的 `name`、`description`，以及用途、來源位置、constraints 與待確認事項。TUI 不依賴 frontmatter 解析，因此未來不同 AI 生成的 Markdown 都可讀取。階層是本工具的資料組織慣例；各 AI 的原生 skill 載入仍需後續 adapter。

`--context NODE` 按根到葉的順序輸出該節點與祖先文件，不包含兄弟或子節點。根節點名稱為 `.`。來源路徑只當文字顯示，不會開啟或執行。

## 導入 SOP

1. 先用隨附的虛構 connsys 範例測試介面與命令。
2. 在公司建立獨立的知識資料夾，依 IC → PHY/MAC/Integrator → IP 組織。
3. 後續掃描器依上述格式產生 SKILL.md，透過 `r` 更新畫面。
4. 每筆 constraint 區分「文件規定／RTL 觀察／AI 推論」，附來源及待確認狀態。
5. 公司資料依內部管理方式保存，工具 repository 只保存程式與虛構範例。

第一階段不需要定義完整掃描器，但先固定此資料格式，可以避免第二階段接不上 UI。

## 開發與驗證

```sh
python3 -m unittest discover -s tests -v
```

CI 涵蓋 Ubuntu / macOS 與 Python 3.9 / 3.11 / 3.13。互動 TUI 仍需真實 terminal 操作確認。更新工具：在 repository 執行 `git pull --ff-only`。

License: MIT.
