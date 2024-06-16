// app/lib/api/deleteHelmRelease.ts

const deleteHelmRelease = async (name: string, namespace: string, token: string) => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/helm/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ name, namespace }),
    });

    if (!res.ok) {
        if (res.status === 401) {
            throw new Error('Unauthorized: Invalid token or session expired');
        }
        throw new Error('Failed to delete Helm release');
    }

    return await res.json();
};

export default deleteHelmRelease;
