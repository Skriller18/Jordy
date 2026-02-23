import { NextRequest, NextResponse } from "next/server";

// Edge-safe middleware: only enforce presence of session cookie.
// All sensitive authorization (role checks, token verification) is enforced
// inside Node.js route handlers.
const COOKIE_NAME = "jd_session";

const PUBLIC_PATHS = [
  /^\/invite\//,
  /^\/api\/health$/,
  /^\/_next\//,
  /^\/favicon\.ico$/,
];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (PUBLIC_PATHS.some((re) => re.test(pathname))) {
    return NextResponse.next();
  }

  const hasCookie = !!req.cookies.get(COOKIE_NAME)?.value;
  if (!hasCookie) {
    const url = req.nextUrl.clone();
    url.pathname = "/unauthorized";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/:path*"],
};
