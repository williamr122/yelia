import MetricsPageClient from '../../metricas/MetricsPageClient';

export const dynamic = 'force-dynamic';

export default function TeacherMetricsPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link rel="stylesheet" href="/static/css/pages/metrics.css" />
      <link rel="stylesheet" href="/static/css/base/base.panel-scrollbars.v2.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='metrics-page desktop-pro';" }} />
      <MetricsPageClient mode="teacher" />
      <script defer src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" />
    </>
  );
}
