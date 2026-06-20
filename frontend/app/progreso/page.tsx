import ProgresoClient from './ProgresoClient';

export const dynamic = 'force-dynamic';

export default function ProgresoPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/base/yelia-theme-tokens.css" />
      <link rel="stylesheet" href="/static/css/pages/progreso.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='student-progress-page ui desktop-pro';" }} />
      <ProgresoClient />
    </>
  );
}
