import { NextResponse } from 'next/server';
import { auth } from '@/lib/auth';

const PUBLIC_ROUTES = [
  '/',
  '/cli-auth',
  '/api/auth',
  '/api/pods/public',
  '/api/health',
];

export default auth((request) => {
  const { pathname } = request.nextUrl;

  const isPublicRoute = PUBLIC_ROUTES.some((route) => pathname.startsWith(route));
  if (isPublicRoute) {
    return NextResponse.next();
  }

  if (!request.auth) {
    const signInUrl = new URL('/', request.nextUrl.origin);
    return NextResponse.redirect(signInUrl);
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};