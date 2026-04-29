import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

export async function GET(req: NextRequest) {
  const file = req.nextUrl.searchParams.get('file');
  const area = req.nextUrl.searchParams.get('area') ?? 'homepage';
  if (!file || !/^[a-z0-9_]+\.png$/.test(file)) {
    return new NextResponse('Bad request', { status: 400 });
  }
  if (!/^[a-z]+$/.test(area)) {
    return new NextResponse('Bad request', { status: 400 });
  }

  const imgPath = area === 'hospitality'
    ? join(process.cwd(), 'analysis', 'hospitality', 'evidence', 'features', file)
    : join(process.cwd(), 'analysis', 'homepage', 'crosscheck', 'img', file);

  if (!existsSync(imgPath)) {
    return new NextResponse(null, { status: 404 });
  }

  const buf = await readFile(imgPath);
  return new NextResponse(buf, {
    headers: {
      'Content-Type': 'image/png',
      'Cache-Control': 'public, max-age=86400',
    },
  });
}
