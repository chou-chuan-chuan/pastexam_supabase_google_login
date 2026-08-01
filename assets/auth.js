const OAUTH_QUERY_KEYS = [
  "code",
  "error",
  "error_code",
  "error_description"
];

const OAUTH_HASH_KEYS = [
  "access_token",
  "refresh_token",
  "expires_at",
  "expires_in",
  "provider_token",
  "provider_refresh_token",
  "token_type",
  "type",
  "error",
  "error_code",
  "error_description"
];

export const SUPABASE_CLIENT_OPTIONS = Object.freeze({
  auth: Object.freeze({
    flowType: "pkce",
    detectSessionInUrl: true,
    persistSession: true,
    autoRefreshToken: true
  })
});

function httpUrl(value) {
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new TypeError("OAuth redirects require an HTTP or HTTPS page.");
  }
  return url;
}

function pageBaseUrl(currentUrl) {
  const url = httpUrl(currentUrl);
  url.search = "";
  url.hash = "";

  if (!url.pathname.endsWith("/")) {
    url.pathname = url.pathname.slice(0, url.pathname.lastIndexOf("/") + 1);
  }

  return url;
}

export function oauthRedirectUrl(currentUrl, destination) {
  const baseUrl = pageBaseUrl(currentUrl);

  if (destination === "home") {
    return baseUrl.href;
  }
  if (destination === "admin") {
    return new URL("admin.html", baseUrl).href;
  }

  throw new TypeError("OAuth destination must be either home or admin.");
}

function hashParams(url) {
  return new URLSearchParams(url.hash.startsWith("#") ? url.hash.slice(1) : url.hash);
}

export function parseOAuthResponse(currentUrl) {
  const url = httpUrl(currentUrl);
  const hash = hashParams(url);
  const hasQueryCallback = OAUTH_QUERY_KEYS.some((key) => url.searchParams.has(key));
  const hasHashCallback = OAUTH_HASH_KEYS.some((key) => hash.has(key));
  const error =
    url.searchParams.get("error_description") ||
    hash.get("error_description") ||
    url.searchParams.get("error") ||
    hash.get("error") ||
    null;
  const errorCode =
    url.searchParams.get("error_code") ||
    hash.get("error_code") ||
    url.searchParams.get("error") ||
    hash.get("error") ||
    null;

  return {
    isCallback: hasQueryCallback || hasHashCallback,
    error,
    errorCode
  };
}

export function cleanOAuthCallbackUrl(currentUrl) {
  const url = httpUrl(currentUrl);
  const response = parseOAuthResponse(url.href);

  if (!response.isCallback) {
    return url.href;
  }

  for (const key of OAUTH_QUERY_KEYS) {
    url.searchParams.delete(key);
  }

  const hash = hashParams(url);
  for (const key of OAUTH_HASH_KEYS) {
    hash.delete(key);
  }
  url.hash = hash.size ? `#${hash.toString()}` : "";

  return url.href;
}

export function cleanOAuthCallbackFromBrowser(browserWindow = window) {
  const currentUrl = browserWindow.location.href;
  const cleanUrl = cleanOAuthCallbackUrl(currentUrl);

  if (cleanUrl !== currentUrl) {
    browserWindow.history.replaceState(browserWindow.history.state, "", cleanUrl);
  }
}

export async function verifyGoogleAuthConfiguration(
  supabaseUrl,
  publishableKey,
  fetchImplementation = fetch
) {
  let response;

  try {
    response = await fetchImplementation(`${supabaseUrl}/auth/v1/settings`, {
      headers: { apikey: publishableKey }
    });
  } catch (error) {
    throw new Error(
      `Cannot reach Supabase Authentication at ${supabaseUrl}. Verify config.js and that the project is active.`,
      { cause: error }
    );
  }

  if (!response.ok) {
    throw new Error(`Supabase Authentication preflight failed (HTTP ${response.status}).`);
  }

  const settings = await response.json();
  if (settings?.external?.google !== true) {
    throw new Error("Google sign-in is not enabled in this Supabase project.");
  }
}
