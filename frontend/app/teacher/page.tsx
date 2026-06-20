import TeacherPanel from './react/TeacherPanel';

export const dynamic = 'force-dynamic';

export default function TeacherPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/pages/teacher.css" />
      <link rel="stylesheet" href="/static/css/base/base.panel-scrollbars.v2.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='teacher-pro desktop-pro';" }} />
      <TeacherPanel />
    </>
  );
}
