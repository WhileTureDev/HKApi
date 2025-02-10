import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { config } from '@/app/config';

export async function GET(request: Request) {
  return handleRequest(request);
}

export async function POST(request: Request) {
  return handleRequest(request);
}

export async function PUT(request: Request) {
  return handleRequest(request);
}

export async function DELETE(request: Request) {
  return handleRequest(request);
}

async function handleRequest(request: Request) {
  try {
    const headersList = headers();
    const authHeader = headersList.get('authorization');
    const { pathname, search } = new URL(request.url);
    
    // Remove /api/proxy from the pathname
    const targetPath = pathname.replace('/api/proxy', '');
    const targetUrl = `${config.apiBaseUrl}/api/v1${targetPath}${search}`;

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(authHeader ? { 'Authorization': authHeader } : {}),
      },
      ...(request.method !== 'GET' && request.body ? { body: request.body } : {}),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'API request failed' }));
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to proxy request' },
      { status: 500 }
    );
  }
}
