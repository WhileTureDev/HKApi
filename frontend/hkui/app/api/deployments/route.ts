import { NextResponse } from 'next/server';
import { config } from '@/app/config';

interface Deployment {
    id: string;
    projectId: string;
    version: string;
    status: 'pending' | 'successful' | 'failed';
    timestamp: string;
    logs?: string[];
}

// GET /api/deployments
export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const projectId = searchParams.get('projectId');

        const response = await fetch(`${config.apiBaseUrl}/deployments/${projectId ? `?projectId=${projectId}` : ''}`, {
            headers: {
                // TODO: Add proper authentication token
                'Authorization': 'Bearer YOUR_TOKEN_HERE'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch deployments');
        }

        const deployments = await response.json();
        return NextResponse.json(deployments);
    } catch (error) {
        console.error('Error fetching deployments:', error);
        return NextResponse.json(
            { error: 'Failed to fetch deployments' },
            { status: 500 }
        );
    }
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
