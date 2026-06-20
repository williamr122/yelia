import AdminSetupClient from './AdminSetupClient';

export const dynamic = 'force-dynamic';

export default function AdminSetupPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/pages/admin-setup.css" />
      <link rel="stylesheet" href="/static/css/base/base.panel-scrollbars.v2.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='admin-setup-page desktop-pro';" }} />
      <AdminSetupClient />
    </>
  );
}
