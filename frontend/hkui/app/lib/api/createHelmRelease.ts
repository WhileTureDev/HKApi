// app/lib/api/createHelmRelease.ts

const createHelmRelease = async (payload: any, token: string) => {
    // Convert payload to query parameters
    const queryParams = new URLSearchParams({
        release_name: payload.release_name || payload.name,
        chart_name: payload.chart_name,
        chart_repo_url: payload.chart_repo_url,
        namespace: payload.namespace,
        project: payload.project || '',
        version: payload.version || '',
        debug: (payload.debug || false).toString()
    }).toString();

    // Use the local proxy endpoint
    const url = `/api/proxy/helm/releases?${queryParams}`;

    // Simple fetch call through our proxy
    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!res.ok) {
        if (res.status === 401) {
            throw new Error('Unauthorized: Invalid token or session expired');
        }
        const errorText = await res.text();
        throw new Error(`Failed to create Helm release: ${errorText}`);
    }

    return await res.json();
};

export default createHelmRelease;
