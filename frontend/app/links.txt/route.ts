import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export async function GET() {
  const lines = [
    'YELIA4AP - Links rápidos',
    '/launcher', '/demo', '/chat', '/status', '/health', '/openapi.json', '/docs',
    '/admin/login', '/admin/setup', '/admin', '/teacher/login', '/teacher',
    '/metricas', '/admin/metrics', '/db'
  ];
  return new NextResponse(lines.join('\n'), { status: 200, headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' } });
}
