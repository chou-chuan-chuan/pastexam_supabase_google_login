import test from "node:test";
import assert from "node:assert/strict";

import {
  SUPABASE_CLIENT_OPTIONS,
  cleanOAuthCallbackUrl,
  oauthRedirectUrl,
  parseOAuthResponse,
  verifyGoogleAuthConfiguration
} from "../assets/auth.js";

const LOCAL_HOME = "http://localhost:8000/";
const LOCAL_ADMIN = "http://localhost:8000/admin.html";
const PRODUCTION_HOME = "https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/";
const PRODUCTION_ADMIN = `${PRODUCTION_HOME}admin.html`;

test("computes exact localhost redirect URLs", () => {
  assert.equal(oauthRedirectUrl(LOCAL_HOME, "home"), LOCAL_HOME);
  assert.equal(oauthRedirectUrl(LOCAL_ADMIN, "admin"), LOCAL_ADMIN);
});

test("computes exact GitHub Pages redirect URLs and preserves the repository path", () => {
  assert.equal(oauthRedirectUrl(PRODUCTION_HOME, "home"), PRODUCTION_HOME);
  assert.equal(oauthRedirectUrl(PRODUCTION_ADMIN, "admin"), PRODUCTION_ADMIN);
});

test("ignores current query and hash when computing a redirect", () => {
  assert.equal(
    oauthRedirectUrl(`${PRODUCTION_ADMIN}?code=old#access_token=old`, "admin"),
    PRODUCTION_ADMIN
  );
});

test("rejects arbitrary or external return-to destinations", () => {
  assert.throws(
    () => oauthRedirectUrl(PRODUCTION_HOME, "https://evil.example/steal"),
    /home or admin/
  );
  assert.throws(
    () => oauthRedirectUrl("javascript:alert(1)", "home"),
    /HTTP or HTTPS/
  );
});

test("parses OAuth errors from query and hash parameters", () => {
  assert.deepEqual(
    parseOAuthResponse(`${LOCAL_HOME}?error=server_error&error_description=Provider+failed`),
    { isCallback: true, error: "Provider failed", errorCode: "server_error" }
  );
  assert.deepEqual(
    parseOAuthResponse(`${LOCAL_HOME}#error=access_denied&error_description=User+cancelled`),
    { isCallback: true, error: "User cancelled", errorCode: "access_denied" }
  );
});

test("cleans PKCE query parameters without removing unrelated state", () => {
  assert.equal(
    cleanOAuthCallbackUrl(`${PRODUCTION_ADMIN}?view=pending&code=one-time-code`),
    `${PRODUCTION_ADMIN}?view=pending`
  );
});

test("cleans implicit-flow tokens and errors without destroying a normal hash", () => {
  assert.equal(
    cleanOAuthCallbackUrl(
      `${LOCAL_HOME}?error_description=failed&lang=en#access_token=secret&token_type=bearer&section=recent`
    ),
    `${LOCAL_HOME}?lang=en#section=recent`
  );
  assert.equal(cleanOAuthCallbackUrl(`${LOCAL_HOME}#faq`), `${LOCAL_HOME}#faq`);
});

test("enables PKCE, callback detection, persistence, and refresh", () => {
  assert.deepEqual(SUPABASE_CLIENT_OPTIONS.auth, {
    flowType: "pkce",
    detectSessionInUrl: true,
    persistSession: true,
    autoRefreshToken: true
  });
});

test("Google provider preflight accepts an enabled provider", async () => {
  const calls = [];
  await verifyGoogleAuthConfiguration("https://project.supabase.co", "publishable", async (...args) => {
    calls.push(args);
    return { ok: true, json: async () => ({ external: { google: true } }) };
  });
  assert.equal(calls[0][0], "https://project.supabase.co/auth/v1/settings");
  assert.equal(calls[0][1].headers.apikey, "publishable");
});

test("Google provider preflight reports unreachable and disabled projects", async () => {
  await assert.rejects(
    verifyGoogleAuthConfiguration("https://missing.supabase.co", "publishable", async () => {
      throw new TypeError("Failed to fetch");
    }),
    /Cannot reach Supabase Authentication/
  );

  await assert.rejects(
    verifyGoogleAuthConfiguration("https://project.supabase.co", "publishable", async () => ({
      ok: true,
      json: async () => ({ external: { google: false } })
    })),
    /not enabled/
  );
});
