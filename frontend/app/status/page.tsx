import StatusClient from './StatusClient';

export const dynamic = 'force-dynamic';

export default function StatusPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/base/yelia-theme-tokens.css" />
      <link rel="stylesheet" href="/static/css/pages/status.css" />
      <link rel="stylesheet" href="/static/css/base/base.panel-scrollbars.v2.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='status-page desktop-pro';" }} />
      <StatusClient />
    </>
  );
}
