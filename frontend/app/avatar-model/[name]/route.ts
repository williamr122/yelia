import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { NextRequest, NextResponse } from 'next/server';

const ALLOWED = new Set(['gato.glb', 'perro.glb', 'buho.glb']);

type Params = {
  params: Promise<{ name: string }>;
};

export async function GET(_request: NextRequest, { params }: Params) {
  const { name } = await params;
  const fileName = path.basename(name || '');

  if (!ALLOWED.has(fileName)) {
    return NextResponse.json({ ok: false, error: 'Modelo no permitido.' }, { status: 404 });
  }

  const filePath = path.join(process.cwd(), 'public', 'avatars3d', fileName);
  const bytes = await readFile(filePath);

  return new NextResponse(bytes, {
    status: 200,
    headers: {
      'content-type': 'model/gltf-binary',
      'cache-control': 'public, max-age=31536000, immutable',
    },
  });
}
