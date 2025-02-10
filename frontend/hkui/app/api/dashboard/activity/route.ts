import { NextResponse } from 'next/server';
import { mockActivity } from '../../mock/data';

export async function GET() {
  // Simulate network latency
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return NextResponse.json(mockActivity);
}
