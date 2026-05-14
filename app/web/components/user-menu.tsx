"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CurrentUser } from "@/lib/api";

export function UserMenu({ user }: { user: CurrentUser }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [logging, setLogging] = useState(false);

  async function onLogout() {
    setLogging(true);
    try {
      await api.logout();
    } finally {
      // Regardless of API outcome, force a navigation that the middleware
      // will reject and bounce to /login.
      router.push("/login");
      router.refresh();
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-full px-2 py-1 text-sm hover:bg-muted"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
          {user.name.charAt(0).toUpperCase()}
        </span>
        <span className="hidden md:inline">{user.email}</span>
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-56 rounded-md border border-border bg-background shadow-md">
          <div className="border-b border-border px-3 py-2 text-xs text-muted-foreground">
            <div className="text-foreground">{user.name}</div>
            <div>{user.email}</div>
            <div className="mt-1 font-mono uppercase tracking-wide">{user.role}</div>
          </div>
          <button
            onClick={onLogout}
            disabled={logging}
            className="block w-full px-3 py-2 text-left text-sm hover:bg-muted disabled:opacity-50"
          >
            {logging ? "Signing out…" : "Sign out"}
          </button>
        </div>
      )}
    </div>
  );
}
