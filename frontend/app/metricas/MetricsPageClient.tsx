'use client';

import dynamic from 'next/dynamic';

const MetricsApp = dynamic(() => import('./react/MetricsApp'), {
  ssr: false,
  loading: () => <div className="metrics-empty">Cargando metricas...</div>,
});

type MetricsPageClientProps = {
  mode: 'admin' | 'teacher' | 'general';
};

export default function MetricsPageClient({ mode }: MetricsPageClientProps) {
  return <MetricsApp mode={mode} />;
}
