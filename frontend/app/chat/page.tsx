"use client";

import { useEffect, useRef, useState } from "react";
import { connectSocket } from "@/lib/websocket";
import { logout } from "@/lib/auth";
import { useRouter } from "next/dist/client/components/navigation";
import { AUTH_API, MESSAGING_API } from "@/lib/api";


// token helpers
function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function parseUserIdFromToken(token: string | null) {
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub;
  } catch {
    return null;
  }
}

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return null;

  const res = await fetch(`${AUTH_API}/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) return null;

  const data = await res.json();

  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);

  return data.access_token;
}

// API helper
async function api(path: string, options: RequestInit = {}, api: string = MESSAGING_API) {
  const token = getToken();

  const res = await fetch(`${api}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
      ...(options.headers || {}),
    },
  });

  // If token expired -> refresh and retry once
  if (res.status === 401) {
    const newToken = await refreshAccessToken();

    if (!newToken) {
      logout(); // force login
      throw new Error("Session expired");
    }

    // retry original request with new token
    const res = await fetch(`${api}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: newToken ? `Bearer ${newToken}` : "",
        ...(options.headers || {}),
      },
    });
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "API error");
  }

  return res.json();
}

type Message = {
  id: string;
  content: string;
  sender_id: string;
  created_at: string;

  reply_to?: {
    id: string;
    content: string;
    sender_id: string;
  } | null;
};


// page
export default function ChatPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeConv, setActiveConv] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const [user, setUser] = useState<any>(null);
  const [userMap, setUserMap] = useState<Record<string, string>>({});
  const [editingConv, setEditingConv] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [replyingTo, setReplyingTo] = useState<Message | null>(null);
  const [allowed, setAllowed] = useState<any>(false);
  const [messageSearch, setMessageSearch] = useState("");
  const [filteredMessages, setFilteredMessages] = useState<any[]>([]);

  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) router.replace("/login");
    else setAllowed(true);
  }, [router]);

  useEffect(() => {
    const saved = localStorage.getItem("userMap");
    if (saved) {
      setUserMap(JSON.parse(saved));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("userMap", JSON.stringify(userMap));
  }, [userMap]);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    fetch(`${AUTH_API}/users/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((r) => r.json())
      .then(setUser)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!activeConv) return;

    socketRef.current = connectSocket(activeConv, (msg) => {
      setMessages((prev) => {
        const map = new Map(prev.map(m => [m.id, m]));
        map.set(msg.id, msg);
        return Array.from(map.values());
      });

      scrollToBottom();
    });

    return () => socketRef.current?.close();
  }, [activeConv]);

  useEffect(() => {
    const token = getToken();
    setCurrentUserId(parseUserIdFromToken(token));
  }, []);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (!conversations.length) return;

    async function loadUsernames() {
      try {
        // collect all participant ids
        const ids = new Set<string>();

        conversations.forEach(c =>
          c.participant_ids.forEach((id: string) => ids.add(id))
        );

        if (!ids.size) return;

        const query = Array.from(ids)
          .map(id => `ids=${encodeURIComponent(id)}`)
          .join("&");

        const users = await api(
          `/auth/users/by_id/?${query}`,
          { method: "POST" },
          AUTH_API
        );

        const map: Record<string, string> = {};
        users.forEach((u: any) => {
          map[u.id] = u.username;
        });

        setUserMap(map);

      } catch (err) {
        console.error("Failed to load usernames", err);
      }
    }

    loadUsernames();
  }, [conversations]);

   useEffect(() => {
    if (!activeConv) return;

    if (!messageSearch.trim()) {
      setFilteredMessages(messages); // show normal messages
      return;
    }

    const delay = setTimeout(async () => {
      try {
        const results = await searchMessagesAPI(activeConv, messageSearch);
        setFilteredMessages(results);
      } catch (e) {
        console.error("Message search failed:", e);
      }
    }, 300);

    return () => clearTimeout(delay);
  }, [messageSearch, activeConv, messages]);


  // load conversations
  async function loadConversations() {
    try {
      const data = await api("/conversations/");
      setConversations(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Load conversations failed:", err);
    } finally {
      setLoading(false);
    }
  }

  // load messages
  async function selectConversation(id: string) {
    setActiveConv(id);

    try {
      const data = await api(`/messages/${id}`);
      setMessages(Array.isArray(data) ? data : []);
      scrollToBottom();
    } catch (err) {
      console.error("Load messages failed:", err);
    }
  }

  // send message
  function sendMessage() {
    if (!text.trim() || !socketRef.current) return;

    const payload = {
        content: text,
        conversation_id: activeConv,
        reply_to_message_id: replyingTo?.id ?? null,
        }

    socketRef.current.send(
        JSON.stringify(payload)
    );

    setReplyingTo(null);
  }

  function resetTextarea() {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = "auto";
  }

  function handleSend() {
    if (!text.trim()) return;
    sendMessage();
    setText("");
    resetTextarea();
  }


  // get conversation display
  function getConversationDisplay(
    conversation: any,
    currentUserId: string | null,
    userMap: Record<string, string>
  ) {
    // remove duplicates first
    const uniqueIds: string[] = Array.from(
      new Set((conversation.participant_ids || []).map((id: any) => String(id)))
    );

    // private chat -> show only the other person's name (exclude self)
    if (conversation.type === "private") {
      const otherId = uniqueIds.find(id => id !== currentUserId) || null;

      const name =
        (otherId && userMap[otherId]) ||
        (otherId ? otherId : "Unknown");

      return {
        title: name,
        participants: name ? [name] : [],
        isGroup: false,
      };
    }

    // group chat -> show all names (including self as "You")
    const names = uniqueIds.map(id => {
      if (id === currentUserId) return "You";
      return userMap[id] || id;
    });

    return {
      title: conversation.name || "Unnamed Group",
      participants: names,
      isGroup: true,
    };
  }

  // create conversation
  async function createConversation() {
    const emailInput = prompt("Enter participant email(s), comma-separated");
    if (!emailInput) return;

    const emails = emailInput
      .split(",")
      .map(e => e.trim())
      .filter(Boolean);

    try {
      // build query string: emails=a&emails=b
      const query = emails
        .map(e => `emails=${encodeURIComponent(e)}`)
        .join("&");

      const userDetails = await api(
        `/auth/users/by_email/?${query}`,
        { method: "POST" },
        AUTH_API
      );

      const newUsers: Record<string, string> = {};
      for (const u of userDetails) {
        newUsers[u.id] = u.username;
      }

      setUserMap(prev => ({ ...prev, ...newUsers }));

      const userIds = [];
      for (const u of userDetails) {
        userIds.push(u.id);
      }

      let groupName: string | null = null;
      // if more than 1 other participant -> group chat
      if (userIds.length > 1) {
        groupName = prompt("Enter group name");
      }

      // create conversation with resolved user IDs
      const conv = await api("/conversations/", {
        method: "POST",
        body: JSON.stringify({ participant_ids: userIds,  name: groupName }),
      });

      setConversations(prev => {
        const exists = prev.some(c => c.id === conv.id);
        if (exists) return prev;
        return [conv, ...prev];
      });

      selectConversation(conv.id);
    } catch (err) {
      console.error("Create conversation failed:", err);
    }
  }

  // rename conversation
  async function saveConversationName(convId: string) {
    try {
      const updated = await api(`/conversations/${convId}`, {
        method: "PATCH",
        body: JSON.stringify({ name: editName }),
      });

      setConversations(prev =>
        prev.map(c => (c.id === convId ? { ...c, name: updated.name } : c))
      );

      setEditingConv(null);
      setEditName("");
    } catch (err) {
      console.error("Rename failed:", err);
    }
  }

  function getConversationSearchText(
    conversation: any,
    currentUserId: string | null,
    userMap: Record<string, string>
  ) {
    const ids: string[] = (conversation.participant_ids || []).map((id: any) =>
      String(id)
    );

    const me = currentUserId ? String(currentUserId) : null;

    const uniqueIds = Array.from(new Set(ids));

    const participantNames = uniqueIds.map(id => {
      if (id === me) return "You";
      return userMap[id] || id;
    });

    const title = conversation.name || "";

    return `${title} ${participantNames.join(" ")}`.toLowerCase();
  }

  // delete message
  async function deleteMessage(messageId: string) {
    if (!messageId) {
      console.error("No message ID provided for deletion");
      return;
    }
    
    const token = localStorage.getItem("access_token");

    if (!token) {
      console.error("User not authenticated");
      return;
    }
    
    const res = await fetch(`${MESSAGING_API}/messages/${messageId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` }
    });

    if (res.ok) {
      setMessages(prev => prev.filter(m => m.id !== messageId));
    } else {
      console.error("Failed to delete message:");
    }
  }

  // delete conversation
  async function deleteConversation(id: string | null) {
    if (!id) {
      console.error("No conversation ID provided for deletion");
      return;
    }
    const token = localStorage.getItem("access_token");
    await fetch(`${MESSAGING_API}/conversations/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` }
    });

    setActiveConv(null);
    loadConversations();
  }

  async function searchMessagesAPI(conversationId: string, query: string) {
    if (!query.trim()) return;

    return api(
      `/search/messages?conversation_id=${conversationId}&query=${encodeURIComponent(query)}`
    );
  }


  // auto scrollreturn
  function scrollToBottom() {
    setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  }

  if (loading) return <div className="p-6">Loading chat...</div>;

  const filteredConversations = conversations
  .map(c => ({
    conv: c,
    text: getConversationSearchText(c, currentUserId, userMap)
  }))
  .filter(x => x.text.includes(searchTerm.toLowerCase()))
  .sort((a, b) =>
    a.text.indexOf(searchTerm) - b.text.indexOf(searchTerm)
  )
  .map(x => x.conv);

  if (!allowed) return null;

  return (
  <div className="flex flex-col h-screen bg-gray-100">

    {/* Profile Header */}
    <div className="px-5 py-4 border-b bg-white/70 backdrop-blur flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center text-sm font-semibold text-gray-600">
          {user?.username?.[0]?.toUpperCase()}
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-xs text-gray-400">Logged in as</span>
          <span className="font-semibold text-gray-800">
            {user?.username || "Loading..."}
          </span>
        </div>
      </div>

      <button
        onClick={logout}
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-xl border border-red-200 hover:bg-red-100 hover:border-red-300 active:scale-95 transition"
      >
        Logout
      </button>
    </div>

    {/* Main Area */}
    <div className="flex flex-1 min-h-0">

      {/* sidebar */}
      <div className="w-80 border-r bg-white text-gray-900 p-4 flex flex-col min-h-0">
        <button
          onClick={createConversation}
          className="w-full mb-4 bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700"
        >
          + New Conversation
        </button>

        <input
          type="text"
          placeholder="Search conversations..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full mb-3 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring"
        />

        <div className="space-y-2 overflow-y-auto">
          {filteredConversations.map((c) => {
              const display = getConversationDisplay(c, currentUserId, userMap);

              return (
                <div
                  key={c.id}
                  onClick={() => selectConversation(c.id)}
                  className={`p-3 rounded-lg cursor-pointer border transition ${
                    activeConv === c.id
                      ? "bg-blue-100 border-blue-300"
                      : "hover:bg-gray-100"
                  }`}
                >
                  {editingConv === c.id ? (
                    <input
                      autoFocus
                      value={editName}
                      onChange={e => setEditName(e.target.value)}
                      onBlur={() => saveConversationName(c.id)}
                      onKeyDown={e => e.key === "Enter" && saveConversationName(c.id)}
                      className="text-sm font-medium border rounded px-2 py-1 w-full"
                    />
                  ) : (
                    <div
                      className="text-sm font-medium truncate"
                      onDoubleClick={() => {
                        setEditingConv(c.id);
                        setEditName(c.name || display.title);
                      }}
                    >
                      {c.name || display.title}
                    </div>
                  )}

                  {/* show participants for the group */}
                  {display.isGroup && (
                    <div className="text-xs text-gray-500 truncate">
                      {display.participants.join(", ")}
                    </div>
                  )}

                  <div className="text-xs text-gray-500">
                    {new Date(c.created_at).toLocaleString()}
                  </div>
                    <div className="flex justify-end">
                      <button
                        onClick={() => deleteConversation(activeConv)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded-lg border border-red-200 hover:bg-red-100 hover:border-red-300 active:scale-95 transition"
                        >
                        Delete Conversation
                      </button>
                    </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex flex-col flex-1 min-h-0 text-gray-900">
        <div className="p-3 border-b bg-white">
          <input
            placeholder="Search messages..."
            value={messageSearch}
            onChange={(e) => setMessageSearch(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
          />
        </div>

        {/* messages */}
        {activeConv && (
          <div className="flex-1 overflow-y-auto p-6 space-y-2 bg-[#F4F1EC]">
            {/* empty search result message */}
            {messageSearch && filteredMessages.length === 0 && (
              <div className="text-center text-gray-400 text-sm mt-4">
                No messages found
              </div>
            )}
            {filteredMessages.map((m) => {
              const isMe = currentUserId && m.sender_id === currentUserId;
              const isGroup = conversations.find(c => c.id === m.conversation_id)?.type === "group";

              return (
                <div
                  key={m.id}
                  className={`flex ${isMe ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`px-4 py-2 rounded-2xl max-w-xs shadow-sm ${
                      isMe
                        ? "bg-[#DCF8C6] text-[#111B21] rounded-br-sm"
                        : "bg-white border text-[#111B21] rounded-bl-sm"
                    }`}
                  >
                    {/* replied message preview */}
                    {m.reply_to && (
                      <div className={`text-xs border-l-2 pl-2 mb-1 ${
                        isMe ? "border-l-4 border-[#25D366]" : "border-l-4 border-[#4F46E5]"
                      }`}>
                        <div className={`font-semibold ${
                          isMe ? "text-[#25D366]" : "text-[#4F46E5]"
                        }`}>
                          {m.reply_to.sender_id === currentUserId
                            ? "You"
                            : userMap[m.reply_to.sender_id] || m.reply_to.sender_id}
                        </div>

                        <div className="truncate text-gray-500">
                          {m.reply_to.content}
                        </div>
                      </div>
                    )}
                    <div className="text-sm whitespace-pre-wrap break-words">
                      {isGroup && (
                        <div className="text-xs font-semibold text-blue-500 mb-1">
                          {m.sender_id === currentUserId ? "You" : userMap[m.sender_id] || m.sender_id}
                        </div>
                      )}
                      {m.content}
                    </div>
                    <div className="text-[10px] opacity-70 mt-1 text-right">
                      {new Date(m.created_at).toLocaleString()}
                    </div>
                    <div className="flex justify-end gap-2 mt-1">
                      {/* delete message button */}
                      <button
                        onClick={() => deleteMessage(m.id)}
                        className="text-[10px] text-red-600 hover:underline"
                      >
                        Delete
                      </button>
                    </div>
                    {/* reply button */}
                    <button
                      onClick={() => setReplyingTo(m)}
                      className="text-[10px] text-blue-600 hover:underline ml-2"
                    >
                      Reply
                    </button>
                  </div>
                </div>
              );
            })}

            {activeConv && messages.length === 0 && (
              <div className="text-gray-400 text-sm">
                No messages yet. Start the conversation.
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}

        {/* Input */}
        {activeConv && (
          <div className="border-t bg-white px-4 py-3">
            <div className="flex items-end gap-2">

              {/* reply preview */}
              {replyingTo && (
                <div className="border-l-4 border-green-400 pl-3 py-1 text-sm bg-gray-50 rounded flex justify-between items-start">
                  <div>
                    <div className="font-medium">
                      {replyingTo.sender_id === currentUserId
                        ? "You"
                        : userMap[replyingTo.sender_id] || "Unknown"}
                    </div>
                    <div className="truncate text-gray-600">
                      {replyingTo.content}
                    </div>
                  </div>

                  <button
                    onClick={() => setReplyingTo(null)}
                    className="text-gray-500 hover:text-black ml-3"
                  >
                    ✕
                  </button>
                </div>
              )}

              {/* chat input box */}
              <div className="flex-1 bg-gray-100 rounded-2xl px-4 py-2 focus-within:ring-2 focus-within:ring-[#DCF8C6]">
                <textarea
                  ref={textareaRef}
                  rows={1}
                  value={text}
                  placeholder="Type a message"
                  onChange={(e) => setText(e.target.value)}
                  onInput={(e) => {
                    const el = e.currentTarget;
                    el.style.height = "auto";
                    el.style.height = Math.min(el.scrollHeight, 120) + "px";
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  className="
                    w-full
                    bg-transparent
                    outline-none
                    resize-none
                    max-h-[120px]
                    overflow-y-auto
                    text-sm
                    leading-relaxed
                    placeholder-gray-400
                  "
                />
              </div>

              {/* send button */}
              <button
                onClick={handleSend}
                disabled={!text.trim()}
                className="
                  h-11 w-11
                  flex items-center justify-center
                  rounded-full
                  bg-[#008069]
                  hover:bg-[#006d5b]
                  disabled:opacity-40
                  text-white
                  shrink-0
                  transition
                "
              >
               &#x27A4;
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  </div>
);
}
