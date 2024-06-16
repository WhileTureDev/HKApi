// app/lib/api/createHelmRelease.ts

const createHelmRelease = async (payload: any, token: string) => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/helm/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        if (res.status === 401) {
            throw new Error('Unauthorized: Invalid token or session expired');
        }
        throw new Error('Failed to create Helm release');
    }

    return await res.json();
};

export default createHelmRelease;
