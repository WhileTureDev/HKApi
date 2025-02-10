import { NextResponse } from 'next/server';
import { mockDeployments } from '../mock/data';

interface Deployment {
    id: string;
    projectId: string;
    version: string;
    status: 'pending' | 'successful' | 'failed';
    timestamp: string;
    logs?: string[];
    namespace: string;
}

// GET /api/deployments
export async function GET(request: Request) {
  // Simulate network latency
  await new Promise(resolve => setTimeout(resolve, 500));

  const { searchParams } = new URL(request.url);
  const namespace = searchParams.get('namespace');

  if (namespace) {
    const filteredDeployments = mockDeployments.filter(
      deployment => deployment.namespace === namespace
    );
    return NextResponse.json(filteredDeployments);
  }

  return NextResponse.json(mockDeployments);
}

// POST /api/deployments
export async function POST(request: Request) {
    try {
        const body = await request.json();
        
        if (!body.projectId || !body.version) {
            return NextResponse.json(
                { error: 'Project ID and version are required' },
                { status: 400 }
            );
        }

        const response = await fetch(`${config.apiBaseUrl}/deployments/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // TODO: Add proper authentication token
                'Authorization': 'Bearer YOUR_TOKEN_HERE'
            },
            body: JSON.stringify({
                projectId: body.projectId,
                version: body.version
            })
        });

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(
                { error: error.detail || 'Failed to create deployment' },
                { status: response.status }
            );
        }

        const newDeployment = await response.json();
        return NextResponse.json(newDeployment, { status: 201 });
    } catch (error) {
        console.error('Error creating deployment:', error);
        return NextResponse.json(
            { error: 'Failed to create deployment' },
            { status: 500 }
        );
    }
}
