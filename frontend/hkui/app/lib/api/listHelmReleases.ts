// app/lib/api/listHelmReleases.ts

const listHelmReleases = async (namespace: string, token: string) => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/helm/list?namespace=${namespace}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!res.ok) {
        if (res.status === 401) {
            throw new Error('Unauthorized: Invalid token or session expired');
        }
        throw new Error('Failed to list Helm releases');
    }

    return await res.json();
};

export default listHelmReleases;
