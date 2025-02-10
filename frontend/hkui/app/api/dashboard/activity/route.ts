import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { config } from '@/app/config';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function GET(request: Request) {
  try {
    const headersList = headers();
    const authHeader = headersList.get('authorization');

    if (!authHeader) {
      return NextResponse.json(
        { error: 'No authorization token provided' },
        { status: 401 }
      );
    }

    const response = await fetch(`${config.apiBaseUrl}/api/v1/changelogs`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': authHeader
      }
    });

    if (!response.ok) {
      const status = response.status === 401 ? 401 : 500;
      const errorData = await response.json().catch(() => ({ error: 'Failed to fetch activity' }));
      console.error('Activity error:', errorData);
      
      return NextResponse.json(
        { error: status === 401 ? 'Unauthorized' : 'Failed to fetch activity' },
        { status }
      );
    }

    const changelogs = await response.json();
    
    // Transform changelogs into activity format
    const activity = Array.isArray(changelogs) ? changelogs.map(log => ({
      id: log.id.toString(),
      type: log.type || 'Activity',
      name: log.description || 'Unknown',
      status: log.status || 'success',
      timestamp: log.created_at
    })) : [];

    return NextResponse.json(activity);
  } catch (error) {
    console.error('Error fetching activity:', error);
    return NextResponse.json(
      { error: 'Failed to fetch activity' },
      { status: 500 }
    );
  }
}
