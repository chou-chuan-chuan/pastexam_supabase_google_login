# 歌曲歌詞 PDF 資料庫 — 管理員操作

管理頁：

```text
http://localhost:8000/admin.html
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/admin.html
```

完整 Supabase、Google OAuth、schema、Storage 與 migration 說明請見 `README.md`。

## 建立管理員

1. 新 project 執行 `supabase/setup.sql`；舊 project 執行 `supabase/lyrics_library_migration.sql`。
2. 啟用 Google Provider，讓預定管理員登入一次。
3. 修改 `supabase/admin_setup.sql` 中的 email（若需要），再執行該檔案。
4. 確認最後查詢回傳帳號。

非管理員完成 Google 登入後會看到明確 Access denied。這代表 authentication 成功、authorization 被 RLS 正確拒絕。

`admin_setup.sql` 只用於建立第一位管理員。網站更新並另行執行 `supabase/admin_user_management_migration.sql` 後，既有管理員可在管理頁的「使用者管理」區查看安全的帳號欄位與投稿統計，並升級或移除其他管理員。已部署前版 RPC 的環境另需執行一次 `supabase/admin_user_management_remove_uuid_search_migration.sql`，讓 server-side 搜尋與目前介面一致。該區只透過受保護的 RPC 操作；migration 未部署時會顯示提示，不影響既有歌曲與標籤管理。

## 審核歌曲

歌曲卡可預覽 private PDF、開啟播放閱讀頁、編輯 metadata／同步歌詞，以及切換 pending、approved、rejected。只有 approved songs、cues、tags 與 PDF 對公開使用者可見。

永久刪除會先刪 `songs` row；FK cascade 在同一 database transaction 清除 `lyric_cues` 與 `song_tags`。接著前端刪除 Storage PDF。若第二步失敗，畫面會明確回報 orphan PDF，避免假稱全部成功。

## LRC 與手動同步

在歌曲卡選擇「編輯與同步」：

- 上傳 `.lrc` 或貼上 `[mm:ss]`、`[mm:ss.xx]`、`[mm:ss.xxx]` 內容。
- 可使用 `[offset:]`、`[ar:]`、`[ti:]`、`[al:]` metadata。
- 或貼上逐行歌詞，播放 YouTube 後逐行標記時間。
- 選取某行可編輯秒數與文字、調整順序、刪除或試聽 seek。
- Enter、↑/↓、Ctrl/Cmd+S 只在非輸入欄位聚焦時生效。
- 儲存呼叫 `replace_song_lyric_cues`，整批替換在單一 transaction 中完成。

## 標籤

標籤區可搜尋、建立、改名、修改 slug 及刪除。每列顯示使用歌曲數；刪除使用中的標籤必須再次確認，並由 `delete_tag` RPC 原子清除關聯。

## 內容責任

僅審核並發布已取得權利、授權或依法可使用的歌詞 PDF／同步歌詞。管理頁不提供從 YouTube 或第三方網站抓取、下載或規避限制的功能。

2026-08-02 重測時，`hxzbuupsbawfeosnboie.supabase.co` 已可解析，Auth settings 使用目前 publishable key 回覆 200 且 Google Provider 已啟用；但 `songs` REST endpoint 回覆 404，而舊 `exams` endpoint 回覆 200。這表示 project 已恢復連線、lyrics migration 尚未套用。執行 `supabase/lyrics_library_migration.sql` 前，不得宣稱真實歌曲、Storage、RLS 或管理員流程已通過。
