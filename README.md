# 歌曲歌詞 PDF 資料庫

這個專案已從「考古題 PDF 檔案庫」完整改造成 GitHub Pages 相容的歌曲歌詞資料庫。使用者可以上傳有權使用的歌詞 PDF、搜尋歌曲、播放 YouTube 官方嵌入影片，並在獨立閱讀頁依播放時間查看同步歌詞；管理員負責審核、同步歌詞與標籤。

## 功能

- Google OAuth PKCE、session persistence、安全 callback 清理與首頁／管理頁 redirect。
- `pending`、`approved`、`rejected` 審核流程與 RLS 權限邊界。
- 私有 `lyrics-pdfs` bucket、短效 signed URL PDF 預覽與下載。
- 歌曲名稱、歌手、專輯、年份、語言、曲風、備註與多標籤搜尋／篩選。
- YouTube watch、`youtu.be`、embed、shorts URL 正規化，只儲存 11 字元 video ID。
- YouTube IFrame Player API；不自動播放、不下載影音、不使用 Data API key。
- 同步歌詞依 cue 原始時間高亮，支援 seek 與自動捲動。
- 管理員 LRC 匯入、逐行手動打點、metadata 與 tags 管理。
- 31 個 Node 內建 test runner 測試；沒有 build step 或大型 framework。

## 標題字體

展示標題使用「辰宇落雁體」不等寬 2.0 細體，原始檔取自[官方 `Chenyu-otf/chenyuluoyan_thin` repository](https://github.com/Chenyu-otf/chenyuluoyan_thin)，依 SIL Open Font License 1.1 隨網站散布。未修改的字體與官方授權檔位於：

- `assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf`
- `assets/fonts/chenyuluoyan/license.txt`

`assets/style.css` 以 `@font-face` 將它註冊為 `ChenYuluoyan Web`，並透過 `--font-ui` 套用到全站文字，包括 header、內文、標題、卡片、表單、按鈕、dialog、管理頁、歌曲頁與 footer。網站統一使用原生細體 `font-weight: 400` 並停用瀏覽器人工粗體；若字體因網路或瀏覽器限制無法載入，才會依序 fallback 到 `Noto Serif TC`、系統宋體與通用 serif。

## 品牌圖像

三個頁面的 header 與 browser tab favicon 均使用 `assets/branding/logo-retro.png` 復古唱片／歌詞圖像。PNG 保持原始透明背景，CSS 只以等比例縮放和裁切透明留白來適應桌機與手機頁首，不會加上白底或實色底塊；舊的 `LY` 漸層方塊已移除。

## Supabase project 現況

`config.js` 目前仍指向：

```text
https://hxzbuupsbawfeosnboie.supabase.co
```

這個 hostname 先前曾回覆 DNS `NXDOMAIN`，因此不應在未驗證時自行替換 project。2026-08-02 重新檢查的結果是：DNS 已可解析、`/auth/v1/settings` 使用目前的 publishable key 回覆 HTTP 200，且 Google Provider 為 enabled。舊 `exams` REST endpoint 回覆 200，但新 `songs` endpoint 回覆 404，表示這個 project 目前可連線、但尚未套用 lyrics migration。

因此現階段仍不能宣稱真實歌曲資料、PDF Storage、lyrics RLS 或完整 Google 登入已驗收。請先依下方「既有 project」步驟執行 `supabase/lyrics_library_migration.sql`，再完成真實帳號登入、上傳、審核與公開讀取測試。不要混用不同 project 的 URL 與 key。

瀏覽器端只可使用 `sb_publishable_...` 或 legacy anon key。不要把 Database password、`service_role`、`sb_secret_...` 或 Google Client Secret 放進 repository 或對話。

## 資料庫 schema

### `songs`

儲存 `title`、`artist`、`album`、`release_year`、`language`、`genre`、`notes`、正規化後的 `youtube_video_id`、`pdf_path`、原始檔名、上傳者、審核狀態及建立／更新／審核時間。video ID 有格式 constraint，status 只有三種值，`updated_at` 由 trigger 維護。

### `lyric_cues`

每句歌詞一列，包含 `song_id`、`line_index`、`start_ms`、可選 `end_ms` 與純文字 `text`。歌曲刪除時 cascade；同一首歌的 line index 唯一，時間有非負與 end-after-start constraints。

### `tags` / `song_tags`

Tags 有唯一名稱與 slug；`song_tags` 使用 composite primary key。管理員可 CRUD，使用中的 tag 必須在確認影響歌曲數後透過 `delete_tag` RPC 原子移除關聯。

### Functions 與 RLS

- `is_admin()`：security-definer 管理員檢查，不向前端暴露名單。
- `set_song_tags()`：上傳者只能設定自己 pending song 的既有 tags；管理員可管理全部。
- `replace_song_lyric_cues()`：僅管理員可用；在單一 transaction 中 delete + insert，失敗時整批回滾，避免半套同步資料。
- `delete_tag()`：僅管理員可用；使用中的 tag 需要 `p_confirm_used=true`。
- 公開訪客只能讀 approved songs 及其 cues/tags/PDF。
- 登入者另可讀自己的 pending／rejected songs；只能新增自己的 pending song、修改／刪除自己的 pending song 與其 tag relations。
- 同步歌詞預設只由管理員維護；前端隱藏按鈕不是權限邊界。
- 管理員可管理所有 songs、cues、tags 與審核狀態。

## Storage

新 bucket：

```text
lyrics-pdfs
```

Bucket 是 private，限制 `application/pdf` 與 50 MB（必須和 `MAX_FILE_SIZE_BYTES` 一致）。檔案路徑是：

```text
user-id/unique-file-name.pdf
```

公開 approved PDF 透過 RLS 授權後建立短效 signed URL。使用者只能清理自己 pending song 的 PDF 或尚未建立 row 的 orphan upload；管理員可刪除全部。網站不會把 YouTube 音訊上傳到 Supabase。

## 新 Supabase project 安裝

1. 在 SQL Editor 執行 `supabase/setup.sql`。
2. 設定 Google Provider，並讓預定管理員先登入一次，使帳號出現在 `auth.users`。
3. 如需更換管理員 email，先編輯 `supabase/admin_setup.sql` 最後的 email，再執行該檔案。
4. 確認 SQL 最後查詢回傳管理員 email。
5. 更新 `config.js` 的 Project URL 與匹配的 browser-safe publishable/anon key。
6. 執行本機測試與真實 OAuth／上傳／審核驗收後才 merge 或部署。

`setup.sql` 會建立完整 lyrics schema、indexes、functions、policies、triggers 與 `lyrics-pdfs` bucket。

## 既有舊 project migration

在已經有 `public.exams` 與 `past-exams` bucket 的 project，執行：

1. `supabase/lyrics_library_migration.sql`
2. `supabase/admin_setup.sql`

Migration 是可重複執行且自包含的版本，會在舊 schema 旁新增 lyrics schema。它不會 drop `exams`、刪除 `past-exams`，也不搬移舊 PDF。新版前端只使用 `songs` 與 `lyrics-pdfs`。

確認新版資料與備份無誤後，可日後由 project owner 在維護時段人工評估是否移除舊 table/bucket；repository 不提供自動永久刪除舊資料的 migration。

## Google OAuth 設定

Google Cloud Console 的 Web application OAuth client：

Authorized JavaScript origins（只能是 origin）：

```text
http://localhost:8000
https://chou-chuan-chuan.github.io
```

Authorized redirect URI 必須是實際 Supabase callback，不是 GitHub Pages：

```text
https://ACTUAL_PROJECT_REFERENCE.supabase.co/auth/v1/callback
```

若原 project 恢復，預期 callback 是：

```text
https://hxzbuupsbawfeosnboie.supabase.co/auth/v1/callback
```

Google Client Secret 只貼到 Supabase Dashboard → Authentication → Providers → Google。External consent screen 若在 Testing，必須加入測試帳號。

## Supabase URL Configuration

Site URL：

```text
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/
```

Redirect URLs：

```text
http://localhost:8000/
http://localhost:8000/admin.html
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/admin.html
```

首頁與管理頁分別傳入固定、同 origin 的 return destination；任意外部 return-to 會被拒絕。

## 上傳歌曲

登入後選擇「上傳歌詞」，填入歌曲名稱、歌手、專輯、年份、語言、曲風、YouTube URL、既有標籤、備註與 PDF。YouTube 欄位會即時顯示解析出的 video ID 與安全 thumbnail；不接受 iframe HTML、`javascript:` 或非 YouTube domain。

一般使用者不能建立 tags，也不能送出 `approved` status。上傳永遠建立 pending song。Storage 成功但 row/tag 建立失敗時，前端會嘗試回復 row 與 PDF；若清理失敗會顯示明確訊息。

## 播放與同步閱讀

`song.html?id=SONG_ID` 只為該歌曲建立一個官方 YouTube player。IFrame API 提供事件、目前播放時間與 `seekTo()`；同步輪詢每 250 ms 使用二分搜尋，以 cue 原始時間找出 active cue。點擊歌詞可跳到該時間，並可選擇是否自動捲動。

沒有 cues 時播放器與 PDF 仍正常，歌詞區顯示「此歌曲尚未建立同步歌詞」。若影片是私人、刪除或禁止嵌入，顯示錯誤並保留安全的 YouTube 新分頁連結。

## LRC 匯入

管理員在「編輯與同步」可上傳 `.lrc` 或貼上文字。Parser 支援：

```text
[mm:ss]
[mm:ss.xx]
[mm:ss.xxx]
[offset:500]
[ar:Artist]
[ti:Title]
[al:Album]
```

一行多 timestamp 會展開成多筆 cue；metadata 與空行不會成為歌詞；錯誤行會列出，不會讓編輯器崩潰。系統不會從網路抓 LRC、歌詞或 YouTube captions。

## 手動同步歌詞

1. 貼上逐行歌詞並建立未標記行，或逐行新增。
2. 播放 YouTube，點選一行後按「標記目前時間」。
3. 可直接修改秒數／文字、上移、下移、刪除或按「試聽」seek。
4. 非輸入欄位聚焦時可用 Enter 標記、↑/↓ 選行、Ctrl/Cmd+S 儲存。
5. 修正空文字／負時間；重複時間允許並穩定排序，逆序會提醒並在儲存時排序。
6. 按「儲存」會呼叫原子替換 transaction RPC；任何 constraint 或權限錯誤會整批回滾。

## Tags 管理

管理員可建立、搜尋、改名、修改 slug 及刪除 tags。名稱會產生 Unicode-safe slug 建議；database 以唯一 name、case-insensitive name index 與唯一 slug 防重複。每列顯示使用歌曲數，刪除使用中的 tag 會先要求確認影響數量。

## 本機測試

```bash
python -m http.server 8000
```

開啟：

```text
http://localhost:8000/
http://localhost:8000/song.html?id=VALID_SONG_UUID
http://localhost:8000/admin.html
```

自動化與語法檢查：

```bash
npm test
node --check assets/auth.js
node --check assets/app.js
node --check assets/admin.js
node --check assets/song.js
node --check assets/youtube.js
node --check assets/youtube-player.js
node --check assets/lyrics-sync.js
node --check assets/lrc.js
node --check assets/catalog.js
git diff --check
```

PowerShell 若阻擋 `npm.ps1`，使用 `npm.cmd test`。

## GitHub Pages 部署

在有效 Supabase project 完成真實首頁／管理頁 OAuth、上傳、signed PDF、審核、RLS、YouTube 播放與同步測試後，才將 feature branch merge。然後在 GitHub Settings → Pages 選擇 `main` 與 `/(root)`。不要從未驗證的 feature branch 部署。

## 版權與內容限制

> 僅上傳你擁有權利、取得授權，或依法可使用的歌詞 PDF 與同步歌詞內容。

本網站不下載 YouTube 影片／音訊、不抓取 captions、不爬第三方歌詞網站、不規避地區／廣告／嵌入限制、不接受任意 iframe HTML，也不宣稱 YouTube 內容由本站託管。
