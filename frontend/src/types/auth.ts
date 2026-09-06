/**
 * Types for the authentication API and the session stored client-side.
 * Shapes match the backend's actual /api/auth/register and
 * /api/auth/login responses exactly — nothing invented here.
 */

/** Basic identity info extracted from a successful login and kept in session. */
export interface AuthUser {
  user_id: string;
  player_id: string;
  operator_id: string;
  username: string;
  role: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface RegisterResponseUser {
  user_id: string;
  username: string;
  email: string;
  player_id: string;
  operator_id: string;
}

export interface RegisterResponse {
  message: string;
  data: RegisterResponseUser[];
  success: boolean;
  status_code: number;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me: boolean;
}

/** The single object inside login's `data` array — user info plus tokens. */
export interface LoginResponseData extends AuthUser {
  access_token: string;
  refresh_token: string;
}

export interface LoginResponse {
  message: string;
  data: LoginResponseData[];
  success: boolean;
  status_code: number;
}

/** What's actually persisted in localStorage/sessionStorage after login. */
export interface AuthSession {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponseData {
  access_token: string;
  refresh_token: string;
}

export interface RefreshTokenResponse {
  message: string;
  data: RefreshTokenResponseData[];
  success: boolean;
  status_code: number;
}

export interface LogoutRequest {
  refresh_token: string;
}

export interface LogoutResponse {
  message: string;
  data: Record<string, never>;
  success: boolean;
  status_code: number;
}
