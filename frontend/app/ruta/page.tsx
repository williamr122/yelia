import RutaClient from './RutaClient';

export const dynamic = 'force-dynamic';

export default function RutaPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/base/yelia-theme-tokens.css" />
      <link rel="stylesheet" href="/static/css/pages/ruta.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='ruta-page ui desktop-pro';" }} />
      <RutaClient />
    </>
  );
}
