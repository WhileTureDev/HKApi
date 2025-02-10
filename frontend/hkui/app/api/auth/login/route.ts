import { NextResponse } from 'next/server';
import { config } from '@/app/config';

interface LoginData {
    username: string;
    password: string;
}

interface TokenResponse {
    access_token: string;
    token_type: string;
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
                'Accept': 'application/json',
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

        const data: TokenResponse = await response.json();

        // Create the response with token in body
        const cookieResponse = NextResponse.json({ 
            success: true,
            token: data.access_token 
        });

        // Set the token as an HTTP-only cookie
        cookieResponse.cookies.set('token', data.access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            path: '/',
            maxAge: 60 * 60 * 24 // 24 hours
        });

        return cookieResponse;
    } catch (error) {
        console.error('Login error:', error);
        return NextResponse.json(
            { error: 'Login failed' },
            { status: 500 }
        );
    }
}
