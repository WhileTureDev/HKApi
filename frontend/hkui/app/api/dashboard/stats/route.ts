import { NextResponse } from 'next/server';
import { mockStats } from '../../mock/data';

export async function GET() {
  // Simulate network latency
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return NextResponse.json(mockStats);
}
