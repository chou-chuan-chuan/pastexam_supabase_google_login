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
  assert.match(adminHtml, /使用者管理功能尚未完成資料庫部署/);
  assert.match(adminJs, /supabase\.rpc\("admin_list_users"/);
  assert.match(adminJs, /supabase\.rpc\("admin_set_user_role"/);
  assert.match(adminJs, /userRoleFilter = el\.userRole\.value;\s*userPage = 1/);
  assert.match(adminJs, /目前帳號/);
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
