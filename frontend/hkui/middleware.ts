import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Paths that don't require authentication
const publicPaths = ['/login', '/register', '/api/auth/login', '/api/auth/check'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('token');

  // Skip middleware for static files and API routes
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api/') ||
    pathname.includes('favicon.ico')
  ) {
    return NextResponse.next();
  }

  // If it's a public path, allow access
  if (publicPaths.includes(pathname)) {
    return NextResponse.next();
  }

  // If no token and not a public path, redirect to login
  if (!token) {
    const url = new URL('/login', request.url);
    return NextResponse.redirect(url);
  }

  // Allow access to all other paths if token exists
  return NextResponse.next();
}

export const config = {
  matcher: [
    // Skip all internal paths (_next)
    // Skip all API routes
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
