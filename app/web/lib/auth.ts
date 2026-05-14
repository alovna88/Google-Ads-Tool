// Server-side auth helpers for use in route handlers / server components.

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { api, ApiError, type CurrentUser } from "@/lib/api";

/**
 * Return the inbound request's Cookie header as a single string, ready
 * to be forwarded to the API via `{ cookie: ... }`. Server components
 * don't forward cookies automatically — call this and pass the result.
 */
export async function serverCookieHeader(): Promise<string> {
  return (await cookies()).toString();
}

/**
 * Read the current user using the request's Cookie header. Returns null
 * when not authenticated. Safe to call from any server component.
 */
export async function getCurrentUser(): Promise<CurrentUser | null> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) return null;
  try {
    return await api.me({ cookie: cookieHeader });
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null;
    throw e;
  }
}

/**
 * Use at the top of a server component to guarantee an authenticated
 * user. Returns the user when present; redirects to /login (with the
 * current path as `next`) otherwise.
 */
export async function requireUser(currentPath: string): Promise<CurrentUser> {
  const user = await getCurrentUser();
  if (!user) {
    const next = encodeURIComponent(currentPath || "/");
    redirect(`/login?next=${next}`);
  }
  return user;
}
