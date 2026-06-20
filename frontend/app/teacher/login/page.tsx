import { AuthLoginApp } from '../../_shared/react/AuthLogin';

export const dynamic = 'force-dynamic';

export default function TeacherLoginPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/pages/teacher-login.css" />
      <link rel="stylesheet" href="/static/css/base/base.panel-scrollbars.v2.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='teacher-login';" }} />
      <AuthLoginApp role="teacher" />
      <script defer src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js" />
    </>
  );
}
