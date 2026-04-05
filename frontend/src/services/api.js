function resolveApiBaseUrls() {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configured) {
    return [configured.replace(/\/+$/, "")];
  }

  if (import.meta.env.DEV) {
    return [""];
  }

  return ["/api", ""];
}

const API_BASE_URLS = resolveApiBaseUrls();

async function request(path, options = {}) {
  let lastError = null;

  for (const baseUrl of API_BASE_URLS) {
    const response = await fetch(`${baseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
      ...options,
    });

    const payload = await response.json().catch(() => ({}));
    if (response.ok) {
      return payload;
    }

    lastError = new Error(payload.detail ?? "Request failed.");
    if (response.status !== 404) {
      throw lastError;
    }
  }

  throw lastError ?? new Error("Request failed.");
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
