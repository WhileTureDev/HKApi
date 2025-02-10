import { NextResponse } from 'next/server';
import { config } from '@/app/config';
import { cookies } from 'next/headers';

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
        const cookieStore = cookies();
        const token = cookieStore.get('token')?.value;
        
        if (!token) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        const response = await fetch(`${config.apiBaseUrl}/projects/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            // If no projects found, return empty array instead of error
            if (response.status === 404) {
                return NextResponse.json([]);
            }
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
        const cookieStore = cookies();
        const token = cookieStore.get('token')?.value;
        
        if (!token) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

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
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name: body.name,
                description: body.description || ''
            })
        });

        if (!response.ok) {
            const error = await response.json();
            // Handle specific error cases from backend
            if (response.status === 400 && error.detail === 'Project with this name already exists') {
                return NextResponse.json(
                    { error: 'A project with this name already exists' },
                    { status: 400 }
                );
            }
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
