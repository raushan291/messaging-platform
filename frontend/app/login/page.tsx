"use client";

import { useEffect, useState } from "react";
import { login, getCurrentUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const setUser = useAuthStore((s) => s.setUser);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const form = e.currentTarget;
    const email = (form.elements.namedItem("email") as HTMLInputElement).value;
    const password = (form.elements.namedItem("password") as HTMLInputElement).value;

    try {
        await login(email, password);

        const user = await getCurrentUser();

        setUser(user);

        router.replace("/chat");
    } catch (err) {
        console.error("Login flow failed:", err);
        setError("Login failed");
    }

  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white text-gray-900 p-8 rounded-xl shadow w-96 space-y-4">
        <h1 className="text-xl font-semibold text-center">Login</h1>

        <input name="email" placeholder="Email" className="w-full border px-3 py-2 rounded" required />
        <input name="password" type="password" placeholder="Password" className="w-full border px-3 py-2 rounded" required />

        {error && <div className="text-red-600 text-sm">{error}</div>}

        <button disabled={loading} className="w-full bg-black text-white p-2 rounded-lg">
          {loading ? "Signing in..." : "Login"}
        </button>

        <div className="text-center text-sm text-gray-600 mt-2">
          No account?{" "}
          <a href="/register" className="text-blue-600 hover:underline">
            Please register
          </a>
        </div>
      </form>
    </div>
  );
}
