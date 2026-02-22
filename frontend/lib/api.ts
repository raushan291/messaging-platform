export const AUTH_API = process.env.NEXT_PUBLIC_AUTH_API!;
export const MESSAGING_API = process.env.NEXT_PUBLIC_MESSAGING_API!;
export const WS_API = process.env.NEXT_PUBLIC_WS_API!;


export function getAccessToken() {
  return localStorage.getItem("access_token");
}

export async function apiFetch(url: string, options: RequestInit = {}) {
  const token = getAccessToken();

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
      ...options.headers,
    },
  });

  if (!res.ok) {
    throw new Error("API request failed");
  }

  return res.json();
}
