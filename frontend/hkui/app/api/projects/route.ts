import { NextResponse } from 'next/server';
import { config } from '@/app/config';

// Types matching backend schema
interface Project {
    id: number;
    name: string;
    description: string;
    owner_id: number;
    created_at: string;
    updated_at: string;
}

// GET /api/projects
export async function GET() {
    try {
        const response = await fetch(`${config.apiBaseUrl}/projects/`, {
            headers: {
                // TODO: Add proper authentication token
                'Authorization': 'Bearer YOUR_TOKEN_HERE'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch projects');
        }

        const projects = await response.json();
        return NextResponse.json(projects);
    } catch (error) {
        console.error('Error fetching projects:', error);
        return NextResponse.json(
            { error: 'Failed to fetch projects' },
            { status: 500 }
        );
    }
}

// POST /api/projects
export async function POST(request: Request) {
    try {
        const body = await request.json();
        
        if (!body.name) {
            return NextResponse.json(
                { error: 'Project name is required' },
                { status: 400 }
            );
        }

        const response = await fetch(`${config.apiBaseUrl}/projects/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // TODO: Add proper authentication token
                'Authorization': 'Bearer YOUR_TOKEN_HERE'
            },
            body: JSON.stringify({
                name: body.name,
                description: body.description || ''
            })
        });

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(
                { error: error.detail || 'Failed to create project' },
                { status: response.status }
            );
        }

        const newProject = await response.json();
        return NextResponse.json(newProject, { status: 201 });
    } catch (error) {
        console.error('Error creating project:', error);
        return NextResponse.json(
            { error: 'Failed to create project' },
            { status: 500 }
        );
    }
}
