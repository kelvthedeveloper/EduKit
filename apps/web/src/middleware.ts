import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Route protection categories:
 *
 * PUBLIC   - Anyone can access (no auth required): /login, /forgot-password, /reset-password
 * PROTECTED - Auth required; redirect to /login if unauthenticated
 * ADMIN    - Auth + staff check; redirect to /dashboard if not staff
 *
 * IMPORTANT: Next.js middleware is the FIRST LINE of defense for route-level UX.
 * Django remains the AUTHORITATIVE backend authorization layer.
 * Never rely solely on this middleware for security.
 */

const PUBLIC_PATHS = new Set([
  "/login",
  "/forgot-password",
  "/reset-password",
  "/verify",
]);

const STATIC_PREFIXES = ["/_next", "/static", "/api", "/favicon", "/public"];

function isStaticPath(pathname: string): boolean {
  return STATIC_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return true;
  for (const publicPath of PUBLIC_PATHS) {
    if (pathname.startsWith(publicPath + "/")) return true;
  }
  return false;
}

function hasSessionCookie(request: NextRequest): boolean {
  const sessionCookie =
    request.cookies.get("edukit_sessionid") ||
    request.cookies.get("sessionid");
  return Boolean(sessionCookie?.value);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Never intercept static assets or API routes
  if (isStaticPath(pathname)) {
    return NextResponse.next();
  }

  const authenticated = hasSessionCookie(request);

  // Authenticated users visiting login/public pages → redirect to dashboard
  if (authenticated && isPublicPath(pathname)) {
    const dashboardUrl = request.nextUrl.clone();
    dashboardUrl.pathname = "/dashboard";
    return NextResponse.redirect(dashboardUrl);
  }

  // Unauthenticated users visiting protected pages → redirect to login
  if (!authenticated && !isPublicPath(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Pass through with security headers
  const response = NextResponse.next();

  // Security headers for browser protection
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except static files, images, and api routes
     * that are handled by nginx.
     */
    "/((?!_next/static|_next/image|favicon.ico|icons|images).*)",
  ],
};
