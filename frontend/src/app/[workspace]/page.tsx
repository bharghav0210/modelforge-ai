import { Suspense } from 'react';
import { notFound } from 'next/navigation';

import { workspaces } from '@/lib/workspaces';
type WorkspaceProps = { params: Promise<{ workspace: string }> };

export function generateStaticParams() {
  return workspaces.map(workspace => ({ workspace }));
}

async function WorkspaceRoute({ params }: WorkspaceProps) {
  const { workspace } = await params;
  if (!workspaces.includes(workspace)) notFound();

  // The shared App in the root layout renders the selected workspace content.
  // This route component preserves the existing server-side validation gate.
  return null;
}

export default function Page({ params }: WorkspaceProps) {
  return (
    <Suspense fallback={<p role="status">Loading workspace…</p>}>
      <WorkspaceRoute params={params} />
    </Suspense>
  );
}
