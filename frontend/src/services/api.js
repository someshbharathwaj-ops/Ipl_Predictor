function resolveApiBaseUrls() {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configured) {
    return [configured.replace(/\/+$/, "")];
  }

  return ["/api"];
}

const API_BASE_URLS = resolveApiBaseUrls();

async function request(path, options = {}) {
  const baseUrl = API_BASE_URLS[0];
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? "Request failed.");
  }
  return payload;
}

export function getMetadata() {
  return request("/metadata");
}

export function predictMatch(body) {
  return request("/predict", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
