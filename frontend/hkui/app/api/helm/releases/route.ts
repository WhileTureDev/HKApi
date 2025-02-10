import { NextResponse } from 'next/server';
import { mockHelmReleases } from '../../mock/helm-data';

export async function GET(request: Request) {
  // Simulate network latency
  await new Promise(resolve => setTimeout(resolve, 500));

  const { searchParams } = new URL(request.url);
  const namespace = searchParams.get('namespace');

  if (namespace) {
    const filteredReleases = mockHelmReleases.filter(
      release => release.namespace === namespace
    );
    return NextResponse.json(filteredReleases);
  }

  return NextResponse.json(mockHelmReleases);
}
