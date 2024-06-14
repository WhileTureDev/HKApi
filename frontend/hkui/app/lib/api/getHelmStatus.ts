const getHelmStatus = async (name: string, namespace: string, token: string) => {
    const url = new URL(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/helm/status`);
    url.searchParams.append('name', name);
    url.searchParams.append('namespace', namespace);

    const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
    }

    return response.json();
};

export default getHelmStatus;
