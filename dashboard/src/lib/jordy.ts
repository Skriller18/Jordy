export const JORDY_BASE = process.env.JORDY_BASE_URL || "http://127.0.0.1:8000";

export async function jordyFetch(path: string, init?: RequestInit) {
  const url = `${JORDY_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      Accept: "application/json",
    },
    // No caching; we want fresh sample for now
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Jordy error ${res.status}: ${text}`);
  }
  return res.json();
}
