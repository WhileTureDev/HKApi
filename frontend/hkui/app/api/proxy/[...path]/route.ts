import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { config } from '@/app/config';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// List of paths that don't require authentication
const publicPaths = ['token', 'auth/login', 'auth/register'];

function getAuthToken(request: NextRequest): string | null {
    const token = request.cookies.get('token');
    return token?.value || null;
}

async function handleRequest(request: NextRequest, method: string) {
    const path = request.nextUrl.pathname.replace('/api/proxy/', '');
    const searchParams = request.nextUrl.searchParams.toString();
    // Remove any trailing slashes from path
    const cleanPath = path.replace(/\/*$/, '');

    // Special handling for stats endpoint
    if (cleanPath === 'stats') {
        try {
            const authHeader = request.headers.get('authorization');
            if (!authHeader) {
                return NextResponse.json(
                    { error: 'No authorization token provided' },
                    { status: 401 }
                );
            }

            const [projectsRes, namespacesRes] = await Promise.all([
                fetch(`${config.apiBaseUrl}/api/v1/projects/`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization': authHeader
                    }
                }),
                fetch(`${config.apiBaseUrl}/api/v1/namespaces/`, {
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
                const projectsData = await projectsRes.json().catch(() => ({ error: 'Failed to fetch projects' }));
                const namespacesData = await namespacesRes.json().catch(() => ({ error: 'Failed to fetch namespaces' }));
                
                // If projects succeeded but namespaces failed, still use the projects data
                if (projectsRes.ok && !namespacesRes.ok) {
                    return NextResponse.json({
                        deployments: 0,
                        helmReleases: 0,
                        projects: Array.isArray(projectsData) ? projectsData.length : 0,
                        namespaces: 0
                    });
                }

                // If both failed with auth errors, return 401
                if ((projectsRes.status === 401 || projectsRes.status === 403) && 
                    (namespacesRes.status === 401 || namespacesRes.status === 403)) {
                    return NextResponse.json(
                        { error: 'Unauthorized' },
                        { status: 401 }
                    );
                }

                console.error('API errors:', { projectsData, namespacesData });
                return NextResponse.json(
                    { error: 'Failed to fetch data' },
                    { status: 500 }
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
            console.error('Error fetching stats:', error);
            return NextResponse.json(
                { error: 'Failed to fetch stats' },
                { status: 500 }
            );
        }
    }

    const url = `${config.apiBaseUrl}/api/v1/${cleanPath}${searchParams ? '?' + searchParams : ''}`;

    try {
        const headers: Record<string, string> = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        };

        // Check if this is a public path
        const isPublicPath = publicPaths.some(p => cleanPath.startsWith(p));
        
        // If it's not a public path, we need auth
        if (!isPublicPath) {
            const authHeader = request.headers.get('authorization');
            if (!authHeader) {
                return NextResponse.json(
                    { error: 'No authorization token provided' }, 
                    { status: 401 }
                );
            }
            headers['Authorization'] = authHeader;
        }

        // Clone the request body for non-GET requests
        let body = undefined;
        if (method !== 'GET') {
            const contentType = request.headers.get('content-type');
            if (contentType?.includes('application/json')) {
                body = await request.json();
            } else {
                body = await request.text();
            }
        }

        console.log('Making request to:', url);
        console.log('Headers:', headers);

        const response = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined
        });

        console.log('Response status:', response.status);

        // If the backend returns 401/403, clear the token cookie
        if (response.status === 401 || response.status === 403) {
            const headers = new Headers();
            headers.append('Set-Cookie', 'token=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0');
            
            return NextResponse.json(
                { error: 'Authentication failed' },
                { status: response.status, headers }
            );
        }

        // For 422 errors, try to get the validation error details
        if (response.status === 422) {
            const errorData = await response.json();
            console.log('422 Error data:', errorData);
            return NextResponse.json(
                { error: errorData.detail || 'Validation error' },
                { status: 422 }
            );
        }

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        console.error('Proxy error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest(request, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest(request, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest(request, 'PUT');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return handleRequest(request, 'DELETE');
}
