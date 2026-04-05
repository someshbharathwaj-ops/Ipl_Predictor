const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchMetadata() {
  const response = await fetch(`${API_BASE}/metadata`);
  if (!response.ok) {
    throw new Error("Failed to load metadata");
  }
  return response.json();
}

export async function predictMatch(payload) {
  const response = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(errorPayload.detail ?? "Prediction request failed");
  }

  return response.json();
}
