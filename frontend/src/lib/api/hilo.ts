import {
  GameRoundsResponse,
  GameState,
  PlayRoundRequest,
  PlayRoundResponse,
  RoundHistoryResponse,
  StartGameResponse,
} from "@/types/hilo";

import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  updateTokens,
} from "@/lib/auth/authContext";
import { refreshAccessToken } from "@/lib/api/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8001";

/**
 * Thrown for any non-2xx Hi-Lo API response. Carries the HTTP status
 * so callers can distinguish cases (400 validation, 404 not found,
 * 409 conflict) if they want to — HiLoGame.tsx just shows `.message`,
 * which is already tailored per status below.
 */
export class HiLoApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "HiLoApiError";
    this.status = status;
  }
}

function friendlyMessageForStatus(status: number): string {
  switch (status) {
    case 401:
      return "Your session has expired. Please log in again.";
    case 400:
      return "That request wasn't valid. Please check your input and try again.";
    case 404:
      return "That game or round could not be found.";
    case 409:
      return "This game is no longer active and can't be modified.";
    default:
      return "Something went wrong.";
  }
}

/**
 * Module-level in-flight refresh promise. If several Hi-Lo requests
 * hit 401 at the same moment (e.g. balance + rounds fetched in
 * parallel), only the first caller actually starts a refresh request
 * — every other caller awaits this same promise instead of firing
 * its own POST /api/auth/refresh-token. Cleared once the refresh
 * settles (success or failure) so a later 401 can trigger a fresh
 * refresh attempt.
 */
let refreshPromise: Promise<boolean> | null = null;

function ensureTokenRefreshed(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const currentRefreshToken = getRefreshToken();

      if (!currentRefreshToken) {
        return false;
      }

      try {
        const response = await refreshAccessToken(currentRefreshToken);
        const tokens = response.data?.[0];

        if (!response.success || !tokens) {
          return false;
        }

        // Backend rotates refresh tokens — always store the new one,
        // never keep reusing the old refresh_token after this point.
        updateTokens(tokens.access_token, tokens.refresh_token);
        return true;
      } catch {
        return false;
      }
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

function redirectToLogin(): void {
  clearAuthSession();

  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

/**
 * Shared fetch wrapper for every Hi-Lo API call.
 *
 * On a 401:
 *   - If this is the first attempt (isRetry is false), try to refresh
 *     the access token once (deduplicated via ensureTokenRefreshed),
 *     then retry the original request exactly once with isRetry=true.
 *   - If it's already a retry and still 401, or the refresh itself
 *     failed, give up: clear the session and redirect to /login.
 * This two-state (isRetry) flag is what prevents an infinite refresh
 * loop — a request can trigger at most one refresh-and-retry cycle.
 *
 * Login/register/refresh/logout never go through this function (they
 * use the separate authRequest() helper in lib/api/auth.ts), so this
 * refresh logic can never recursively trigger itself.
 */
async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit,
  isRetry = false,
): Promise<T> {
  const accessToken = getAccessToken();

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(accessToken
          ? { Authorization: `Bearer ${accessToken}` }
          : {}),
        ...(options?.headers || {}),
      },
    },
  );

  if (response.status === 401 && !isRetry) {
    const refreshed = await ensureTokenRefreshed();

    if (refreshed) {
      return apiRequest<T>(endpoint, options, true);
    }

    redirectToLogin();
    throw new HiLoApiError(friendlyMessageForStatus(401), 401);
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      // Already retried once (isRetry === true) and still 401 —
      // the refreshed token isn't working either. Give up.
      redirectToLogin();
    }

    const message =
      data?.detail ||
      data?.message ||
      friendlyMessageForStatus(response.status);

    throw new HiLoApiError(message, response.status);
  }

  return data as T;
}

export async function startGame(
  initialBalance: number,
): Promise<StartGameResponse> {
  return apiRequest<StartGameResponse>(
    "/games/hi-lo",
    {
      method: "POST",
      body: JSON.stringify({
        initial_balance: initialBalance,
      }),
    },
  );
}

export async function getGame(
  gameId: string,
): Promise<GameState> {
  return apiRequest<GameState>(
    `/games/hi-lo/${gameId}`,
  );
}

export async function playRound(
  gameId: string,
  request: PlayRoundRequest,
): Promise<PlayRoundResponse> {
  return apiRequest<PlayRoundResponse>(
    `/games/hi-lo/${gameId}/play`,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

export async function getRoundHistory(
  skip = 0,
  limit = 20,
): Promise<RoundHistoryResponse> {
  return apiRequest<RoundHistoryResponse>(
    `/games/hi-lo/rounds/history?skip=${skip}&limit=${limit}`,
  );
}

export async function getGameRounds(
  gameId: string,
): Promise<GameRoundsResponse> {
  return apiRequest<GameRoundsResponse>(
    `/games/hi-lo/${gameId}/rounds`,
  );
}

/**
 * GET /games/hi-lo/history — player-level game history. Not currently
 * called from any component. Response shape hasn't been confirmed by
 * the backend contract, so this is typed `unknown` rather than
 * guessed — narrow it once the shape is known.
 */
export async function getGameHistory(
  skip = 0,
  limit = 20,
): Promise<unknown> {
  return apiRequest<unknown>(
    `/games/hi-lo/history?skip=${skip}&limit=${limit}`,
  );
}

/**
 * GET /games/hi-lo/{game_id}/rounds/{round_id} — single round detail.
 * Not currently called from any component; see getGameHistory's note
 * above re: unknown return type.
 */
export async function getRound(
  gameId: string,
  roundId: string,
): Promise<unknown> {
  return apiRequest<unknown>(
    `/games/hi-lo/${gameId}/rounds/${roundId}`,
  );
}

/**
 * POST /games/hi-lo/hi-lo/{game_id}/cancel — cancel an active game.
 * Not currently called from any component; see getGameHistory's note
 * above re: unknown return type. The doubled "hi-lo/hi-lo" segment is
 * copied verbatim from the integration contract — double-check it
 * against the real backend route before relying on it.
 */
export async function cancelGame(
  gameId: string,
): Promise<unknown> {
  return apiRequest<unknown>(
    `/games/hi-lo/hi-lo/${gameId}/cancel`,
    { method: "POST" },
  );
}
