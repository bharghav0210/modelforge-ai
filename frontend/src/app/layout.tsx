import type { Metadata } from 'next';
import { Suspense } from 'react';
import './globals.css';
import App from '@/components/app';

export const metadata: Metadata = { title: 'ModelForge AI — Your experiment workspace', description: 'Local model development, honest evaluation, and real inference.' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Suspense fallback={<p role="status">Loading workspace…</p>}>
          <App>{children}</App>
        </Suspense>
      </body>
    </html>
  );
}
