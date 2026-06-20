'use client';

import dynamic from 'next/dynamic';

const DbViewer = dynamic(() => import('./react/DbViewer'), {
  ssr: false,
  loading: () => <div className="db-viewer-loading">Cargando visor...</div>,
});

export default function DbPageClient() {
  return <DbViewer />;
}
