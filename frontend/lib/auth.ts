import { AUTH_API } from "./api";


export async function login(email: string, password: string) {
  const res = await fetch(`${AUTH_API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) throw new Error("Login failed");

  const data = await res.json();

  // localStorage -> for fetch Authorization header
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);

  // cookie -> for Next.js middleware
  document.cookie = `access_token=${data.access_token}; path=/`;

  return data;
}


export async function getCurrentUser() {
  const token = localStorage.getItem("access_token");

  const res = await fetch(`${AUTH_API}/users/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) throw new Error("Unauthorized");

  return res.json();
}


export async function logout() {
  const refresh = localStorage.getItem("refresh_token");

  await fetch(`${AUTH_API}/auth/logout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  localStorage.clear();
  window.location.href = "/login";
}

export async function register(
  email: string,
  username: string,
  password: string
) {
  const res = await fetch(`${AUTH_API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Registration failed");
  }

  return res.json();
}
