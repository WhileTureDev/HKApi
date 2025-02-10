import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { config } from '@/app/config';

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

    const [projectsRes, namespacesRes] = await Promise.all([
      fetch(`${config.apiBaseUrl}/api/v1/projects`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': authHeader
        }
      }),
      fetch(`${config.apiBaseUrl}/api/v1/namespaces`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': authHeader
        }
      })
    ]);

    if (!projectsRes.ok || !namespacesRes.ok) {
      const status = projectsRes.status === 401 || namespacesRes.status === 401 ? 401 : 500;
      const projectsError = await projectsRes.json().catch(() => ({ error: 'Failed to fetch projects' }));
      const namespacesError = await namespacesRes.json().catch(() => ({ error: 'Failed to fetch namespaces' }));
      
      console.error('API errors:', { projectsError, namespacesError });
      return NextResponse.json(
        { error: status === 401 ? 'Unauthorized' : 'Failed to fetch data' },
        { status }
      );
    }

    const [projects, namespaces] = await Promise.all([
      projectsRes.json(),
      namespacesRes.json()
    ]);

    return NextResponse.json({
      deployments: 0, // TODO: Add deployments endpoint
      helmReleases: 0, // TODO: Add helm releases endpoint
      projects: Array.isArray(projects) ? projects.length : 0,
      namespaces: Array.isArray(namespaces) ? namespaces.length : 0,
    });
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch dashboard stats' },
      { status: 500 }
    );
  }
}
