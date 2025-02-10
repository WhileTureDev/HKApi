import { NextResponse } from 'next/server';
import { config } from '@/app/config';

interface SignUpData {
    username: string;
    full_name?: string;
    email: string;
    password: string;
    disabled?: boolean;
}

export async function POST(request: Request) {
    try {
        const body: SignUpData = await request.json();

        // Basic validation
        if (!body.username || !body.email || !body.password) {
            return NextResponse.json(
                { error: 'Username, email, and password are required' },
                { status: 400 }
            );
        }

        const response = await fetch(`${config.apiBaseUrl}/users/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(
                { error: error.detail || 'Failed to create user' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data, { status: 201 });
    } catch (error) {
        console.error('Error creating user:', error);
        return NextResponse.json(
            { error: 'Failed to create user' },
            { status: 500 }
        );
    }
}
