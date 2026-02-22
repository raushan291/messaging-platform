import { AUTH_API, WS_API } from "./api";


export function connectSocket(
  conversationId: string,
  onMessage: (msg: any) => void
) {
  function createSocket(token: string | null) {
    return new WebSocket(
      `${WS_API}/ws/chat/${conversationId}?token=${token}`
    );
  }

  let token = localStorage.getItem("access_token")
  let ws = createSocket(token);

  ws.onopen = () => {
    console.log("WS connected");
  };

  ws.onmessage = (event) => {
    onMessage(JSON.parse(event.data));
  };

  ws.onerror = async () => {
    console.log("WS error -> trying token refresh...");

    try {
      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) throw new Error("No refresh token");

      const res = await fetch(`${AUTH_API}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!res.ok) throw new Error("Refresh failed");

      const data = await res.json();

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);

      console.log("Token refreshed -> reconnecting WS");

      ws.close();
      ws = createSocket(data.access_token);

      ws.onmessage = (event) => {
        onMessage(JSON.parse(event.data));
      };

    } catch (err) {
      console.error("WS reconnect failed:", err);
    }
  };

  ws.onclose = () => {
    console.log("WS closed");
  };

  return ws;
}
