"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { loginUser } from "@/lib/api/auth";
import { setAuthSession } from "@/lib/auth/authContext";

export default function LoginForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await loginUser({
        email,
        password,
        remember_me: rememberMe,
      });

      const sessionData = response.data?.[0];

      if (!response.success || !sessionData) {
        throw new Error(response.message || "Login failed.");
      }

      const {
        access_token,
        refresh_token,
        user_id,
        player_id,
        operator_id,
        username,
        role,
      } = sessionData;

      setAuthSession(
        {
          access_token,
          refresh_token,
          user: { user_id, player_id, operator_id, username, role },
        },
        rememberMe,
      );

      router.push("/hi-lo");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to log in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-sm space-y-5 rounded-2xl border border-white/10 bg-white/5 p-8"
    >
      <div>
        <h1 className="text-2xl font-bold text-white">Welcome back</h1>
        <p className="mt-1 text-sm text-white/60">Log in to keep playing.</p>
      </div>

      {error && (
        <div className="rounded-lg bg-rose-500/10 px-4 py-3 text-sm text-rose-400">
          {error}
        </div>
      )}

      <div>
        <label className="mb-2 block text-sm text-white/60">Email</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition focus:border-white/30"
        />
      </div>

      <div>
        <label className="mb-2 block text-sm text-white/60">Password</label>
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition focus:border-white/30"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-white/60">
        <input
          type="checkbox"
          checked={rememberMe}
          onChange={(e) => setRememberMe(e.target.checked)}
          className="h-4 w-4 rounded border-white/20 bg-white/5"
        />
        Remember me
      </label>

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-white px-5 py-4 font-bold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {loading ? "Logging in..." : "Log In"}
      </button>

      <p className="text-center text-sm text-white/60">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="font-semibold text-white">
          Sign up
        </Link>
      </p>
    </form>
  );
}
