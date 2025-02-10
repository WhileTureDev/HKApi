import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { config } from '@/app/config';

export async function GET(request: Request) {
  try {
    const headersList = headers();
    const authHeader = headersList.get('authorization');

    if (!authHeader) {
      return NextResponse.json(
        { error: 'No token provided' },
        { status: 401 }
      );
    }

    const response = await fetch(`${config.apiBaseUrl}/api/v1/users/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': authHeader,
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Invalid token' },
        { status: response.status }
      );
    }

    const user = await response.json();
    return NextResponse.json({ user });
  } catch (error) {
    console.error('Auth check error:', error);
    return NextResponse.json(
      { error: 'Auth check failed' },
      { status: 500 }
    );
  }
}
