import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  USER_PAGE_SIZE,
  adminListParams,
  clampUserPage,
  isCurrentAccount,
  userManagementUnavailable,
  userPageCount,
  userRoleLabel
} from "../assets/admin-users.js";

const adminHtml = await readFile(new URL("../admin.html", import.meta.url), "utf8");
const adminJs = await readFile(new URL("../assets/admin.js", import.meta.url), "utf8");
const styleCss = await readFile(new URL("../assets/style.css", import.meta.url), "utf8");
const browserSources = await Promise.all([
  "app.js", "admin.js", "admin-users.js", "song.js"
].map((file) => readFile(new URL(`../assets/${file}`, import.meta.url), "utf8")));

test("user pagination and RPC parameters are deterministic and bounded", () => {
  assert.equal(USER_PAGE_SIZE, 25);
  assert.equal(userPageCount(0), 1);
  assert.equal(userPageCount(51), 3);
  assert.equal(clampUserPage(9, 51), 3);
  assert.deepEqual(adminListParams({ query: "  hannah ", role: "admin", page: 3 }), {
    p_query: "hannah",
    p_role: "admin",
    p_limit: 25,
    p_offset: 50
  });
  assert.deepEqual(adminListParams({ role: "invalid", page: -2, pageSize: 999 }), {
    p_query: null,
    p_role: null,
    p_limit: 100,
    p_offset: 0
  });
});

test("user role helpers identify roles, the current account, and missing RPC deployment", () => {
  assert.equal(userRoleLabel({ is_admin: true }), "管理員");
  assert.equal(userRoleLabel({ is_admin: false }), "一般使用者");
  assert.equal(isCurrentAccount({ user_id: "one" }, "one"), true);
  assert.equal(isCurrentAccount({ user_id: "one" }, "two"), false);
  assert.equal(userManagementUnavailable({ code: "PGRST202" }), true);
  assert.equal(userManagementUnavailable({ code: "42883" }), true);
  assert.equal(userManagementUnavailable({ message: "Could not find admin_list_users in the schema cache" }), true);
  assert.equal(userManagementUnavailable({ code: "42501", message: "denied" }), false);
});

test("admin page exposes search, server role filter, states, and pagination controls", () => {
  for (const id of [
    "userAdminSearchForm", "userAdminSearchInput", "userAdminRoleFilter",
    "userAdminRefreshButton", "userAdminDeploymentNotice", "userAdminLoadingState",
    "userAdminList", "userAdminEmptyState", "userAdminPagination",
    "userAdminPreviousButton", "userAdminNextButton"
  ]) assert.match(adminHtml, new RegExp(`id=["']${id}["']`), id);
  assert.match(adminHtml, /placeholder="搜尋名稱、Email 或登入方式"/);
  assert.doesNotMatch(adminHtml, /搜尋[^"<]*UUID/);
  assert.match(adminHtml, /使用者管理功能尚未完成資料庫部署/);
  assert.match(adminJs, /supabase\.rpc\("admin_list_users"/);
  assert.match(adminJs, /supabase\.rpc\("admin_set_user_role"/);
  assert.match(adminJs, /userRoleFilter = el\.userRole\.value;\s*userPage = 1/);
  assert.match(adminJs, /目前帳號/);
});

test("user identity contains only the name while actions show the appropriate control", () => {
  const identityStart = adminJs.indexOf('const identity = node("div", "user-admin-identity")');
  const roleStart = adminJs.indexOf('const role = node("span"', identityStart);
  const identitySource = adminJs.slice(identityStart, roleStart);
  assert.match(identitySource, /identity\.append\(node\("strong", "", userDisplayName\(user\)\)\)/);
  assert.doesNotMatch(identitySource, /user-current-badge|目前帳號/);
  assert.match(adminJs, /if \(current\) \{\s*action\.append\(node\("span", "user-current-badge", "目前帳號"\)\)/);
  assert.doesNotMatch(adminJs, /node\("span", "muted", "目前帳號"\)/);
  assert.match(adminJs, /user\.is_admin \? "移除管理員" : "設為管理員"/);
  assert.match(adminJs, /userRoleLabel\(user\)/);
  assert.doesNotMatch(adminJs, /user-admin-uuid/);
  assert.doesNotMatch(adminJs, /node\("code"[^\n]*user\.user_id/);
  assert.match(adminJs, /isCurrentAccount\(user, currentUser\?\.id\)/);
  assert.match(adminJs, /p_user_id: user\.user_id/);
  assert.doesNotMatch(styleCss, /\.user-admin-name-line/);
  assert.doesNotMatch(styleCss, /\.user-admin-uuid/);
});

test("desktop user columns share a content-aware table layout with compact actions", () => {
  assert.match(styleCss, /\.user-admin-list\s*\{[^}]*display:\s*table[^}]*width:\s*100%[^}]*table-layout:\s*auto/s);
  assert.match(styleCss, /\.user-admin-row\s*\{[^}]*display:\s*table-row/s);
  assert.match(styleCss, /\.user-admin-header > div, \.user-admin-cell\s*\{[^}]*display:\s*table-cell/s);
  assert.match(styleCss, /\.user-admin-action \.button\s*\{[^}]*width:\s*auto/s);
  assert.doesNotMatch(styleCss, /minmax\(170px,\s*1\.55fr\)/);
  assert.match(styleCss, /@media \(max-width: 1000px\)[\s\S]*\.user-admin-list\s*\{[^}]*display:\s*grid/);
  assert.match(styleCss, /@media \(max-width: 1000px\)[\s\S]*\.user-admin-row:not\(\.user-admin-header\) > \.user-admin-cell\s*\{[^}]*display:\s*flex[^}]*width:\s*auto/);
});

test("browser code cannot access privileged auth or admin membership tables directly", () => {
  for (const source of browserSources) {
    assert.doesNotMatch(source, /supabase\.auth\.admin/);
    assert.doesNotMatch(source, /service_role|sb_secret_/i);
    assert.doesNotMatch(source, /\.from\(["']admin_users["']\)/);
    assert.doesNotMatch(source, /auth\.users/);
    assert.doesNotMatch(source, /raw_(?:app|user)_meta_data/);
  }
});
