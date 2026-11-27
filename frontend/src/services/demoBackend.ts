import type {
  Conversation,
  ConversationDetail,
  Message,
  ModelInfo,
  RagDocument,
  TokenResponse,
  User,
} from "../types/api";

const STORAGE_KEY = "offline_ai_demo_state_v1";

interface DemoState {
  user: User;
  users: User[];
  conversations: ConversationDetail[];
  documents: RagDocument[];
}

function nowIso(): string {
  return new Date().toISOString();
}

function uid(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `demo-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

function initialDemoState(): DemoState {
  const created = nowIso();
  const demoUser: User = {
    id: "demo-admin-1",
    email: "demo@offline-ai.local",
    username: "demo_admin",
    full_name: "Demo Administrator",
    role: "admin",
    is_active: true,
    preferred_model: "tinyllama",
    created_at: created,
  };

  const conv1Id = "demo-conv-1";
  const conv2Id = "demo-conv-2";

  return {
    user: demoUser,
    users: [
      demoUser,
      {
        id: "demo-user-2",
        email: "analyst@offline-ai.local",
        username: "analyst",
        full_name: "Offline Analyst",
        role: "user",
        is_active: true,
        preferred_model: "qwen2.5:0.5b",
        created_at: created,
      },
    ],
    conversations: [
      {
        id: conv1Id,
        user_id: demoUser.id,
        title: "TinyLlama 4 GB RAM Architecture",
        model: "tinyllama",
        system_prompt: null,
        use_rag: true,
        created_at: created,
        updated_at: created,
        messages: [
          {
            id: "demo-msg-1",
            conversation_id: conv1Id,
            role: "user",
            content: "How does Offline AI Platform fit inside 2 vCPU and 4 GB RAM?",
            model: "tinyllama",
            prompt_tokens: 15,
            completion_tokens: 0,
            total_tokens: 15,
            response_time_ms: 0,
            created_at: created,
          },
          {
            id: "demo-msg-2",
            conversation_id: conv1Id,
            role: "assistant",
            content:
              "Offline AI Platform enforces strict container memory limits (~3.28 GiB total):\n\n" +
              "• Ollama runs TinyLlama (~637 MB) or Qwen2.5 0.5B (~398 MB) with OLLAMA_NUM_PARALLEL=1 and OLLAMA_MAX_LOADED_MODELS=1.\n" +
              "• FastAPI runs with a single Uvicorn worker (512 MiB cap) so ChromaDB is never duplicated across processes.\n" +
              "• PostgreSQL 16 Alpine (256 MiB), Prometheus (256 MiB), Grafana (192 MiB), Nginx (96 MiB), and Node Exporter (64 MiB) leave over 700 MiB of headroom.",
            model: "tinyllama",
            prompt_tokens: 34,
            completion_tokens: 92,
            total_tokens: 126,
            response_time_ms: 412.6,
            created_at: created,
          },
        ],
      },
      {
        id: conv2Id,
        user_id: demoUser.id,
        title: "Kubernetes & Prometheus Setup",
        model: "qwen2.5:0.5b",
        system_prompt: null,
        use_rag: false,
        created_at: created,
        updated_at: created,
        messages: [
          {
            id: "demo-msg-3",
            conversation_id: conv2Id,
            role: "user",
            content: "Which Prometheus metrics are exported?",
            model: "qwen2.5:0.5b",
            prompt_tokens: 8,
            completion_tokens: 0,
            total_tokens: 8,
            response_time_ms: 0,
            created_at: created,
          },
          {
            id: "demo-msg-4",
            conversation_id: conv2Id,
            role: "assistant",
            content:
              "The /metrics endpoint exports:\n• offline_ai_http_requests_total\n• offline_ai_http_request_duration_seconds\n• offline_ai_llm_tokens_total\n• offline_ai_llm_response_duration_seconds\n• offline_ai_active_conversations\n\nCombined with Node Exporter CPU & memory metrics in Grafana.",
            model: "qwen2.5:0.5b",
            prompt_tokens: 22,
            completion_tokens: 46,
            total_tokens: 68,
            response_time_ms: 285.4,
            created_at: created,
          },
        ],
      },
    ],
    documents: [
      {
        id: "demo-doc-1",
        filename: "offline-ai-architecture.md",
        content_type: "text/markdown",
        chunk_count: 6,
        size_bytes: 2840,
        created_at: created,
      },
    ],
  };
}

function loadState(): DemoState {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    const fresh = initialDemoState();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh));
    return fresh;
  }
  try {
    return JSON.parse(raw) as DemoState;
  } catch {
    const fresh = initialDemoState();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh));
    return fresh;
  }
}

function saveState(state: DemoState): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function toSummary(conv: ConversationDetail): Conversation {
  return {
    id: conv.id,
    user_id: conv.user_id,
    title: conv.title,
    model: conv.model,
    system_prompt: conv.system_prompt,
    use_rag: conv.use_rag,
    created_at: conv.created_at,
    updated_at: conv.updated_at,
  };
}

function generateDemoReply(
  prompt: string,
  model: string,
  useRag: boolean,
  docs: RagDocument[]
): string {
  const trimmed = prompt.trim();
  const lower = trimmed.toLowerCase();

  // Natural conversational greetings without injecting RAG noise
  if (/^(hi+|hello+|hey+|hola|namaste|yo|good\s*(morning|afternoon|evening))[\s!?.]*$/i.test(trimmed)) {
    return (
      `Hello! I am running in the **Offline AI Platform Live UI Demo** with \`${model}\` selected.\n\n` +
      `Ask me about:\n` +
      `• **Architecture & 4 GB RAM optimization** (TinyLlama / Qwen2.5 0.5B)\n` +
      `• **Docker Compose** or **Kubernetes** deployment\n` +
      `• **Prometheus & Grafana** monitoring metrics\n` +
      `• **JWT Auth, RAG, or MCP** tool integration\n\n` +
      `_(Note: GitHub Pages hosts a static UI simulator. For live local LLM inference, run \`./scripts/setup.sh\` with Docker & Ollama.)_`
    );
  }

  const matchedDoc = docs[0]?.filename || "offline-ai-architecture.md";
  const ragPrefix = useRag ? `[RAG Context: ${matchedDoc} matched]\n\n` : "";

  if (lower.includes("docker") || lower.includes("compose")) {
    return (
      ragPrefix +
      `Launch the full stack locally with \`./scripts/setup.sh\` or \`docker compose up -d --build\`.\n\n` +
      `All services (PostgreSQL, Ollama, FastAPI, Nginx, Prometheus, Grafana, Node Exporter) run as non-root containers with strict CPU/RAM limits totaling ~3.28 GiB.`
    );
  }
  if (lower.includes("kubernetes") || lower.includes("k8s")) {
    return (
      ragPrefix +
      `Deploy to Kubernetes with \`kubectl apply -k kubernetes/\`.\n\n` +
      `Manifests include Namespace, ConfigMap, Secrets, PVCs, PostgreSQL, Ollama, FastAPI Backend, unprivileged Nginx Frontend, and Ingress with liveness/readiness probes.`
    );
  }
  if (lower.includes("model") || lower.includes("qwen") || lower.includes("tinyllama")) {
    return (
      ragPrefix +
      `You currently have \`${model}\` selected.\n\n` +
      `• **tinyllama** (~637 MB): Default balanced model for 2 vCPU / 4 GB RAM hosts.\n` +
      `• **qwen2.5:0.5b** (~398 MB): Ultra-lightweight model for faster CPU token generation.\n\n` +
      `Switch models anytime from the header dropdown or Settings.`
    );
  }
  if (lower.includes("monitor") || lower.includes("prometheus") || lower.includes("grafana")) {
    return (
      ragPrefix +
      `Observability is built in via \`GET /metrics\`, Prometheus (:9090), Node Exporter (:9100), and Grafana (:3001).\n\n` +
      `Tracked metrics include host CPU/Memory %, API requests/sec, p95 API latency, prompt/completion token counts, and model response times.`
    );
  }
  if (lower.includes("rag") || lower.includes("pdf") || lower.includes("chroma") || lower.includes("mcp")) {
    return (
      ragPrefix +
      `You can upload PDF, Markdown, or TXT documents in **Settings -> Local Knowledge Base** to index chunks into ChromaDB.\n\n` +
      `The backend also exposes a JSON-RPC 2.0 MCP server at \`POST /api/v1/rag/mcp\` and a 3-step Plan-Retrieve-Synthesize agent at \`POST /api/v1/rag/agent\`.`
    );
  }
  if (lower.includes("auth") || lower.includes("jwt") || lower.includes("security")) {
    return (
      ragPrefix +
      `Security includes HS256 JWT authentication, bcrypt password hashing, role-based access control (first registered user becomes \`admin\`), sliding-window rate limiting, strict CORS, and non-root containers.`
    );
  }

  return (
    ragPrefix +
    `Here is a simulated \`${model}\` response to "${trimmed}":\n\n` +
    `• In this static GitHub Pages demo, responses are simulated client-side and saved in your browser's \`localStorage\`.\n` +
    `• In a full local deployment (\`./scripts/setup.sh\`), FastAPI streams real NDJSON tokens from Ollama while logging token usage and latency to PostgreSQL and Prometheus.`
  );
}

export const demoBackend = {
  login: async (): Promise<TokenResponse> => ({
    access_token: "demo-jwt-token",
    token_type: "bearer",
    expires_in_minutes: 60,
  }),

  register: async (payload: {
    email: string;
    username: string;
    full_name?: string;
  }): Promise<User> => {
    const state = loadState();
    state.user = {
      ...state.user,
      email: payload.email,
      username: payload.username,
      full_name: payload.full_name || state.user.full_name,
    };
    saveState(state);
    return state.user;
  },

  getMe: async (): Promise<User> => loadState().user,

  updateMe: async (payload: {
    full_name?: string;
    preferred_model?: string;
  }): Promise<User> => {
    const state = loadState();
    state.user = {
      ...state.user,
      full_name: payload.full_name ?? state.user.full_name,
      preferred_model: payload.preferred_model ?? state.user.preferred_model,
    };
    state.users = state.users.map((u) => (u.id === state.user.id ? state.user : u));
    saveState(state);
    return state.user;
  },

  listUsers: async (): Promise<User[]> => loadState().users,

  adminUpdateUser: async (
    userId: string,
    payload: { role?: "user" | "admin"; is_active?: boolean }
  ): Promise<User> => {
    const state = loadState();
    let updated: User | undefined;
    state.users = state.users.map((u) => {
      if (u.id === userId) {
        updated = { ...u, ...payload };
        return updated;
      }
      return u;
    });
    saveState(state);
    if (!updated) throw new Error("User not found");
    return updated;
  },

  deleteUser: async (userId: string): Promise<void> => {
    const state = loadState();
    state.users = state.users.filter((u) => u.id !== userId);
    saveState(state);
  },

  listModels: async (): Promise<ModelInfo[]> => [
    { name: "tinyllama", size_bytes: 637_000_000, is_default: true },
    { name: "qwen2.5:0.5b", size_bytes: 398_000_000, is_default: false },
  ],

  listConversations: async (): Promise<Conversation[]> =>
    loadState().conversations.map(toSummary),

  createConversation: async (payload: {
    title?: string;
    model?: string;
    use_rag?: boolean;
  }): Promise<Conversation> => {
    const state = loadState();
    const created = nowIso();
    const conv: ConversationDetail = {
      id: uid(),
      user_id: state.user.id,
      title: payload.title || "New Conversation",
      model: payload.model || state.user.preferred_model,
      system_prompt: null,
      use_rag: payload.use_rag ?? false,
      created_at: created,
      updated_at: created,
      messages: [],
    };
    state.conversations = [conv, ...state.conversations];
    saveState(state);
    return toSummary(conv);
  },

  getConversation: async (id: string): Promise<ConversationDetail> => {
    const found = loadState().conversations.find((c) => c.id === id);
    if (!found) throw new Error("Conversation not found");
    return found;
  },

  updateConversation: async (
    id: string,
    payload: { title?: string; model?: string; system_prompt?: string; use_rag?: boolean }
  ): Promise<Conversation> => {
    const state = loadState();
    let updated: ConversationDetail | undefined;
    state.conversations = state.conversations.map((c) => {
      if (c.id === id) {
        updated = { ...c, ...payload, updated_at: nowIso() };
        return updated;
      }
      return c;
    });
    saveState(state);
    if (!updated) throw new Error("Conversation not found");
    return toSummary(updated);
  },

  deleteConversation: async (id: string): Promise<void> => {
    const state = loadState();
    state.conversations = state.conversations.filter((c) => c.id !== id);
    saveState(state);
  },

  exportConversation: async (id: string, format: "markdown" | "json"): Promise<Blob> => {
    const conv = await demoBackend.getConversation(id);
    if (format === "json") {
      return new Blob([JSON.stringify(conv, null, 2)], { type: "application/json" });
    }
    const md = [
      `# ${conv.title}`,
      "",
      `- **Model:** \`${conv.model}\``,
      "",
      ...conv.messages.flatMap((m) => [`### ${m.role.toUpperCase()}`, "", m.content, ""]),
    ].join("\n");
    return new Blob([md], { type: "text/markdown" });
  },

  streamChat: async (
    payload: {
      conversation_id: string;
      message: string;
      model: string;
      use_rag?: boolean;
    },
    onToken: (token: string) => void,
    onDone: (assistantMessage: Message) => void
  ): Promise<void> => {
    const state = loadState();
    const conv = state.conversations.find((c) => c.id === payload.conversation_id);
    if (!conv) throw new Error("Conversation not found");

    if (conv.title === "New Conversation" && conv.messages.length === 0) {
      conv.title = payload.message.slice(0, 60) || "New Conversation";
    }
    conv.model = payload.model;

    const userMsg: Message = {
      id: uid(),
      conversation_id: conv.id,
      role: "user",
      content: payload.message,
      model: payload.model,
      prompt_tokens: payload.message.split(/\s+/).length,
      completion_tokens: 0,
      total_tokens: payload.message.split(/\s+/).length,
      response_time_ms: 0,
      created_at: nowIso(),
    };
    conv.messages.push(userMsg);

    const reply = generateDemoReply(
      payload.message,
      payload.model,
      Boolean(payload.use_rag),
      state.documents
    );
    const words = reply.split(" ");
    const start = performance.now();

    for (let i = 0; i < words.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 22));
      onToken((i === 0 ? "" : " ") + words[i]);
    }

    const elapsed = Math.round((performance.now() - start) * 10) / 10;
    const assistantMsg: Message = {
      id: uid(),
      conversation_id: conv.id,
      role: "assistant",
      content: reply,
      model: payload.model,
      prompt_tokens: userMsg.prompt_tokens + 12,
      completion_tokens: words.length,
      total_tokens: userMsg.prompt_tokens + 12 + words.length,
      response_time_ms: elapsed,
      created_at: nowIso(),
    };
    conv.messages.push(assistantMsg);
    conv.updated_at = nowIso();
    saveState(state);
    onDone(assistantMsg);
  },

  listDocuments: async (): Promise<RagDocument[]> => loadState().documents,

  uploadDocument: async (file: File): Promise<RagDocument> => {
    const state = loadState();
    const doc: RagDocument = {
      id: uid(),
      filename: file.name,
      content_type: file.type || "text/plain",
      chunk_count: Math.max(1, Math.ceil(file.size / 600)),
      size_bytes: file.size,
      created_at: nowIso(),
    };
    state.documents = [doc, ...state.documents];
    saveState(state);
    return doc;
  },

  deleteDocument: async (id: string): Promise<void> => {
    const state = loadState();
    state.documents = state.documents.filter((d) => d.id !== id);
    saveState(state);
  },
};
