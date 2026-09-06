/**
 * Auth API client — registration and login against the backend's
 * /api/auth/* endpoints.
 *
 * Kept separate from lib/api/hilo.ts deliberately: these calls are
 * unauthenticated by nature (there's no token yet when registering
 * or logging in), so they don't go through the Hi-Lo wrapper that
 * attaches an Authorization header and redirects to /login on 401.
 */
import type {
  LoginRequest,
  LoginResponse,
  LogoutRequest,
  LogoutResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  RegisterRequest,
  RegisterResponse,
} from "@/types/auth";

import { clearAuthSession, getRefreshToken } from "@/lib/auth/authContext";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8001";

async function authRequest<T>(
  endpoint: string,
  options: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => null);

  if (!response.ok || data?.success === false) {
    const message = data?.message || "Something went wrong.";
    throw new Error(message);
  }

  return data as T;
}

export async function registerUser(
  payload: RegisterRequest,
): Promise<RegisterResponse> {
  return authRequest<RegisterResponse>("/api/auth/register?lang=en", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(
  payload: LoginRequest,
): Promise<LoginResponse> {
  return authRequest<LoginResponse>("/api/auth/login?lang=en", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * POST /api/auth/refresh-token.
 *
 * Called only from lib/api/hilo.ts's apiRequest() when a protected
 * Hi-Lo request gets a 401 — never called directly by UI code, and
 * never called for login/register/logout themselves (those go
 * through authRequest() above, a separate path that never triggers
 * refresh logic, so there's no risk of refreshing while refreshing).
 */
export async function refreshAccessToken(
  refreshToken: string,
): Promise<RefreshTokenResponse> {
  const payload: RefreshTokenRequest = { refresh_token: refreshToken };

  return authRequest<RefreshTokenResponse>("/api/auth/refresh-token", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * POST /api/auth/logout, sending the current refresh token.
 *
 * The local session is always cleared in `finally`, regardless of
 * whether the backend call succeeds — a network failure or an
 * already-expired token on the backend shouldn't leave the user
 * stuck "logged in" locally.
 */
export async function logoutUser(): Promise<void> {
  const refreshToken = getRefreshToken();

  try {
    if (refreshToken) {
      const payload: LogoutRequest = { refresh_token: refreshToken };

      await authRequest<LogoutResponse>("/api/auth/logout", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
  } catch {
    // Ignore — session is cleared below regardless.
  } finally {
    clearAuthSession();
  }
}
