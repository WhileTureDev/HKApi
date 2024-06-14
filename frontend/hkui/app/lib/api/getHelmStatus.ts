// app/lib/api/getHelmStatus.ts

const getHelmStatus = async (name: string, namespace: string, token: string) => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/helm/status?name=${name}&namespace=${namespace}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!res.ok) {
        if (res.status === 401) {
            throw new Error('Unauthorized: Invalid token or session expired');
        }
        throw new Error('Failed to get Helm status');
    }

    return await res.json();
};

export default getHelmStatus;
