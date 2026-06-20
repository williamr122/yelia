import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export async function GET() {
  const base = process.env.NEXT_PUBLIC_BASE_URL || '';
  const links = {
    launcher: '/launcher', demo: '/demo', chat: '/chat', status: '/status',
    health: '/health', openapi: '/openapi.json', docs: '/docs',
    adminLogin: '/admin/login', adminSetup: '/admin/setup', adminPanel: '/admin',
    teacherLogin: '/teacher/login', teacherPanel: '/teacher',
    metrics: '/metricas', adminMetrics: '/admin/metrics', dbViewer: '/db'
  };
  return NextResponse.json({ ok: true, service: 'YELIA4AP', base, links }, { headers: { 'cache-control': 'no-store' } });
}
