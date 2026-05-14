import { NextResponse, type NextRequest } from "next/server";

// Public paths that never require a session.
const PUBLIC_PATHS = ["/login"];
// Static assets + the API proxy itself are skipped via the `matcher` below.

const SESSION_COOKIE = "session";

function withPathnameHeader(request: NextRequest): NextResponse {
  // Expose the current pathname to server components via a request header
  // — Next.js doesn't surface the path to layouts otherwise.
  const headers = new Headers(request.headers);
  headers.set("x-pathname", request.nextUrl.pathname);
  return NextResponse.next({ request: { headers } });
}

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  if (PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return withPathnameHeader(request);
  }

  const hasSession = request.cookies.has(SESSION_COOKIE);
  if (hasSession) return withPathnameHeader(request);

  // Bounce to /login with the original path so we can return after auth.
  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", `${pathname}${search}`);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  // Skip Next internals and the API rewrite (the API enforces auth itself).
  matcher: ["/((?!_next/|api/|favicon.ico).*)"],
};
