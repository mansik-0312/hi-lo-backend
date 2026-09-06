/**
 * Centralized authentication/session module.
 *
 * Single source of truth for the JWT access/refresh tokens and the
 * authenticated user's basic info. Every other module (the Hi-Lo API
 * wrapper, the protected-route guard, the login/signup forms) reads
 * or writes session state exclusively through the functions here —
 * nothing else in the app should touch localStorage/sessionStorage
 * directly.
 *
 * Storage location depends on "remember me" at login time:
 *   - remember_me: true  -> localStorage   (persists across restarts)
 *   - remember_me: false -> sessionStorage (cleared when the tab closes)
 * setAuthSession() records which backend was used (as a small pointer
 * kept in localStorage) so the getters below know where to look
 * without guessing or checking both stores every time.
 *
 * SSR-safe: every exported function guards on
 * `typeof window === "undefined"`, since layout.tsx/page.tsx render
 * server-side in the Next.js App Router, where window/localStorage/
 * sessionStorage don't exist.
 */

import type { AuthSession, AuthUser } from "@/types/auth";

const SESSION_KEY = "hilo:auth-session";
// Points at which storage backend the live session lives in. Always
// kept in localStorage (even for a sessionStorage-backed session) —
// it's just a pointer, not sensitive data, so this is safe.
const STORAGE_MODE_KEY = "hilo:auth-storage-mode";

type StorageMode = "local" | "session";

function getBackend(mode: StorageMode): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }
  return mode === "local" ? window.localStorage : window.sessionStorage;
}

function readSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const mode = window.localStorage.getItem(STORAGE_MODE_KEY) as StorageMode | null;
  if (!mode) {
    return null;
  }

  const raw = getBackend(mode)?.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

/**
 * Store the session after a successful login.
 * @param rememberMe - mirrors the login form's "remember me" checkbox;
 *   true persists via localStorage, false uses sessionStorage.
 */
export function setAuthSession(
  session: AuthSession,
  rememberMe: boolean,
): void {
  if (typeof window === "undefined") {
    return;
  }

  const mode: StorageMode = rememberMe ? "local" : "session";

  // Clear the other backend first so a stale session there can never
  // be read by mistake later (e.g. user previously logged in with
  // the opposite remember-me setting).
  const otherMode: StorageMode = mode === "local" ? "session" : "local";
  getBackend(otherMode)?.removeItem(SESSION_KEY);

  getBackend(mode)?.setItem(SESSION_KEY, JSON.stringify(session));
  window.localStorage.setItem(STORAGE_MODE_KEY, mode);
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(SESSION_KEY);
  window.sessionStorage.removeItem(SESSION_KEY);
  window.localStorage.removeItem(STORAGE_MODE_KEY);
}

function getCurrentStorageMode(): StorageMode | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(STORAGE_MODE_KEY) as StorageMode | null;
}

/**
 * Replace both tokens in the existing session after a successful
 * refresh, preserving the stored user info and writing back to
 * whichever storage backend (local/session) the session already
 * lives in — the caller doesn't need to know or pass rememberMe
 * again. No-ops if there's no active session to update.
 *
 * The backend rotates refresh tokens, so this always overwrites the
 * old refresh_token with the new one — never keep using a stale one.
 */
export function updateTokens(accessToken: string, refreshToken: string): void {
  const mode = getCurrentStorageMode();
  const current = readSession();

  if (!mode || !current) {
    return;
  }

  const updated: AuthSession = {
    ...current,
    access_token: accessToken,
    refresh_token: refreshToken,
  };

  getBackend(mode)?.setItem(SESSION_KEY, JSON.stringify(updated));
}

export function getAccessToken(): string | null {
  return readSession()?.access_token ?? null;
}

export function getRefreshToken(): string | null {
  return readSession()?.refresh_token ?? null;
}

export function getCurrentUser(): AuthUser | null {
  return readSession()?.user ?? null;
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  userId: string | null;
  playerId: string | null;
  operatorId: string | null;
  username: string | null;
  role: string | null;
  isAuthenticated: boolean;
}

/**
 * Convenience getter returning the full auth state shape in one call
 * (e.g. for a header component showing the username). The individual
 * getters above still exist and are what the API wrapper/guard use —
 * this is purely additive, nothing was removed.
 */
export function getAuthState(): AuthState {
  const session = readSession();

  return {
    accessToken: session?.access_token ?? null,
    refreshToken: session?.refresh_token ?? null,
    userId: session?.user.user_id ?? null,
    playerId: session?.user.player_id ?? null,
    operatorId: session?.user.operator_id ?? null,
    username: session?.user.username ?? null,
    role: session?.user.role ?? null,
    isAuthenticated: session !== null,
  };
}
