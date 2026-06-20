import LauncherClient from './LauncherClient';

export const dynamic = 'force-dynamic';

export default function LauncherPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/base/yelia-theme-tokens.css" />
      <link rel="stylesheet" href="/static/css/pages/launcher.css" />
      <link rel="stylesheet" href="/static/css/base/base.profile-modal.css" />
      <link rel="stylesheet" href="/static/css/base/base.panel-scrollbars.v2.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='launcher ui desktop-pro';" }} />
      <LauncherClient />
    </>
  );
}
