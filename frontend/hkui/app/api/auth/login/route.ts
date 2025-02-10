import { NextResponse } from 'next/server';
import { config } from '@/app/config';

interface LoginData {
    username: string;
    password: string;
}

export async function POST(request: Request) {
    try {
        const body: LoginData = await request.json();

        if (!body.username || !body.password) {
            return NextResponse.json(
                { error: 'Username and password are required' },
                { status: 400 }
            );
        }

        const response = await fetch(`${config.apiBaseUrl}/api/v1/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                username: body.username,
                password: body.password,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(
                { error: error.detail || 'Invalid credentials' },
                { status: response.status }
            );
        }

        const data = await response.json();
        
        // Set the token in an HTTP-only cookie
        const cookieResponse = NextResponse.json(
            { success: true },
            { status: 200 }
        );
        
        cookieResponse.cookies.set('token', data.access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            path: '/',
            maxAge: 7200 // 2 hours
        });

        return cookieResponse;
    } catch (error) {
        console.error('Error during login:', error);
        return NextResponse.json(
            { error: 'Authentication failed' },
            { status: 500 }
        );
    }
}
