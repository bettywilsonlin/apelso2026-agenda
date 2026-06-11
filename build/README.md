# build/ — 生成議程 HTML 的原始檔

`../index.html`（成品）是由這裡的腳本生成的，**不要手改 index.html**，改這裡再重跑。

## 檔案

| 檔案 | 用途 |
|---|---|
| `build_data.py` | 解析資料 + 注入模板，一鍵產出 `../index.html` |
| `template.html` | HTML 模板（含 `/*__DATA__*/{}` 注入點） |
| `apelso_program.md` | 官網 program.html 抓下來的原始 markdown（SY 講題來源） |
| `apelso_data.json` | 腳本產出的中繼資料（可不管，每次重跑會覆寫） |

## 怎麼補講題（最常見）

大會 App（Conference Navi）截圖補進來時，改 `build_data.py` 對應的字典：

- **FC／午餐會等場次層級補講題** → 改 `MANUAL_TALKS`
- **SY 官網原本 T.B.A.、App 才公布** → 改 `SY_TALK_OVERRIDES`

## 重新生成（一個指令）

```bash
cd build && python3 build_data.py
```

會同時更新 `apelso_data.json` 和 `../index.html`。接著：

```bash
git add -A && git commit -m "補講題" && git push
```

Google Drive 副本（`我的雲端硬碟/APELSO/APELSO2026_我的議程.html`）若也要更新，手動複製 `../index.html` 過去。
