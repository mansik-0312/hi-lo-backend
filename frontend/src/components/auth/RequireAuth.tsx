"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { isAuthenticated } from "@/lib/auth/authContext";

interface RequireAuthProps {
  children: React.ReactNode;
}

/**
 * Wraps a page/component that requires an authenticated session.
 * Redirects to /login if isAuthenticated() is false. Renders nothing
 * until the check completes, to avoid a flash of protected content
 * (e.g. game state, balance) before the redirect happens.
 */
export default function RequireAuth({ children }: RequireAuthProps) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }

    setChecked(true);
  }, [router]);

  if (!checked) {
    return null;
  }

  return <>{children}</>;
}
