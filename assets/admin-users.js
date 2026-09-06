export const USER_PAGE_SIZE = 25;

export function userPageCount(total, pageSize = USER_PAGE_SIZE) {
  const size = Math.max(1, Math.trunc(Number(pageSize) || USER_PAGE_SIZE));
  return Math.max(1, Math.ceil(Math.max(0, Number(total) || 0) / size));
}

export function clampUserPage(page, total, pageSize = USER_PAGE_SIZE) {
  const requested = Math.max(1, Math.trunc(Number(page) || 1));
  return Math.min(requested, userPageCount(total, pageSize));
}

export function adminListParams({ query = "", role = "", page = 1, pageSize = USER_PAGE_SIZE } = {}) {
  const safePageSize = Math.min(100, Math.max(1, Math.trunc(Number(pageSize) || USER_PAGE_SIZE)));
  const safePage = Math.max(1, Math.trunc(Number(page) || 1));
  const normalizedQuery = String(query || "").trim();
  const normalizedRole = ["admin", "user"].includes(role) ? role : "";
  return {
    p_query: normalizedQuery || null,
    p_role: normalizedRole || null,
    p_limit: safePageSize,
    p_offset: (safePage - 1) * safePageSize
  };
}

export function userRoleLabel(user) {
  return user?.is_admin ? "管理員" : "一般使用者";
}

export function isCurrentAccount(user, currentUserId) {
  return Boolean(user?.user_id && currentUserId && user.user_id === currentUserId);
}

export function userManagementUnavailable(error) {
  const code = String(error?.code || "").toUpperCase();
  const message = String(error?.message || "").toLocaleLowerCase();
  return code === "PGRST202"
    || code === "42883"
    || (message.includes("admin_list_users") && (message.includes("schema cache") || message.includes("does not exist") || message.includes("could not find")));
}
