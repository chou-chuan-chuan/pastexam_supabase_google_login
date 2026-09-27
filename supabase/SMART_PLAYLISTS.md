# 標籤自動歌單部署

既有專案請先在 Supabase SQL Editor 執行 `tag_playlist_read_policy_migration.sql`，再部署前端。全新專案的 `setup.sql` 已包含修正。

這份 migration 只修正 `Visible tags are readable` SELECT policy 的欄位引用：原本 `st.tag_id = id` 的 `id` 會指向內層 `songs.id`，導致訪客讀不到已公開歌曲的標籤名稱；修正為 `st.tag_id = tags.id`。不建立資料表、不複製歌單成員、不修改歌曲或標籤資料、不更動寫入權限。

- 管理員建立標籤後，登入者重新載入歌單頁就會看到同名自動歌單，即使目前為 0 首。
- 訪客只會看到至少有一首 approved 歌曲的標籤；不公開只用於 pending/rejected 歌曲或尚未使用的標籤。
- 所有歌單只收 approved 歌曲，並沿用 catalog 顯示排序。新增／移除歌曲標籤及審核狀態變更會在下次載入時反映。
- 標籤歌單以 tag id 作為連結：`playlist.html?tag=<UUID>`。標籤改名或改 slug 不影響成員或連結；刪除標籤後歌單消失。
- Favorite 也使用實際標籤名稱，無固定的「My favorite」顯示名稱。既有 `?smart=my-favorite` 連結仍可使用，指向既有 Favorite tag id。
- 所有標籤歌單均共用私人歌單卡片樣式及既有播放、上一首／下一首與自動接續機制。

部署後以未登入瀏覽器確認標籤卡片有名稱，開啟歌單及歌曲播放頁，確認只出現 approved 歌曲；登入後確認剛建立的空標籤也有 0 首歌單。
