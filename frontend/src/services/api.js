function resolveApiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/+$/, "");
  }
  return import.meta.env.DEV ? "" : "/api";
}

const API_BASE_URL = resolveApiBaseUrl();

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
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
