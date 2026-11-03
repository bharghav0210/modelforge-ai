import { NextResponse, type NextRequest } from 'next/server';
import { workspaces } from '@/lib/workspaces';

export function proxy(request: NextRequest) {
  const workspace = request.nextUrl.pathname.split('/')[1];
  if (!workspaces.includes(workspace)) {
    // Reject unknown workspaces before Suspense starts streaming a 200 response.
    return NextResponse.rewrite(new URL('/_not-found', request.url), { status: 404 });
  }
  return NextResponse.next();
}

export const config = {
  // Only workspace-shaped paths; leave the overview, assets and internal URLs alone.
  matcher: '/:workspace((?!_)[^/.]+)',
};
