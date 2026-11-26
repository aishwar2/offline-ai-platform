import type {
  Conversation,
  ConversationDetail,
  Message,
  ModelInfo,
  RagDocument,
  TokenResponse,
  User,
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...(init.headers || {}),
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  register: (payload: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) => request<User>("/auth/register", { method: "POST", body: JSON.stringify(payload) }),

  login: (username_or_email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username_or_email, password }),
    }),

  getMe: () => request<User>("/users/me"),

  updateMe: (payload: { full_name?: string; preferred_model?: string; password?: string }) =>
    request<User>("/users/me", { method: "PATCH", body: JSON.stringify(payload) }),

  listUsers: () => request<User[]>("/users"),

  adminUpdateUser: (userId: string, payload: { role?: "user" | "admin"; is_active?: boolean }) =>
    request<User>(`/users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) }),

  deleteUser: (userId: string) => request<void>(`/users/${userId}`, { method: "DELETE" }),

  listModels: () => request<ModelInfo[]>("/chat/models"),

  listConversations: () => request<Conversation[]>("/conversations"),

  createConversation: (payload: { title?: string; model?: string; use_rag?: boolean }) =>
    request<Conversation>("/conversations", { method: "POST", body: JSON.stringify(payload) }),

  getConversation: (id: string) => request<ConversationDetail>(`/conversations/${id}`),

  updateConversation: (
    id: string,
    payload: { title?: string; model?: string; system_prompt?: string; use_rag?: boolean }
  ) => request<Conversation>(`/conversations/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  deleteConversation: (id: string) =>
    request<void>(`/conversations/${id}`, { method: "DELETE" }),

  exportConversation: async (id: string, format: "markdown" | "json") => {
    const res = await fetch(`${API_BASE}/conversations/${id}/export?format=${format}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Export failed");
    return res.blob();
  },

  streamChat: async (
    payload: {
      conversation_id: string;
      message: string;
      model: string;
      temperature?: number;
      use_rag?: boolean;
    },
    onToken: (token: string) => void,
    onDone: (assistantMessage: Message) => void
  ) => {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ ...payload, stream: true }),
    });

    if (!res.ok || !res.body) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Streaming chat failed");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const evt of events) {
        const line = evt.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;
        const parsed = JSON.parse(line.slice(6));
        if (parsed.type === "token" && parsed.content) {
          onToken(parsed.content);
        } else if (parsed.type === "done" && parsed.assistant_message) {
          onDone(parsed.assistant_message as Message);
        } else if (parsed.type === "error") {
          throw new Error(parsed.detail || "Inference error");
        }
      }
    }
  },

  listDocuments: () => request<RagDocument[]>("/rag/documents"),

  uploadDocument: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/rag/documents`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "Upload failed");
    }
    return res.json() as Promise<RagDocument>;
  },

  deleteDocument: (id: string) => request<void>(`/rag/documents/${id}`, { method: "DELETE" }),
};
