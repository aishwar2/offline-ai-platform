import { useCallback, useEffect, useState } from "react";
import { AuthView } from "./components/AuthView";
import { ChatWorkspace } from "./components/ChatWorkspace";
import { SettingsView } from "./components/SettingsView";
import { Sidebar } from "./components/Sidebar";
import { api, isDemoMode, setDemoMode } from "./services/api";
import type { Conversation, ConversationDetail, ModelInfo, User } from "./types/api";

export function App() {
  const [token, setToken] = useState<string | null>(() => {
    if (isDemoMode()) {
      setDemoMode(true);
      return "demo-jwt-token";
    }
    return localStorage.getItem("auth_token");
  });
  const [user, setUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<ConversationDetail | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [activeTab, setActiveTab] = useState<"chat" | "settings">("chat");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [darkMode, setDarkMode] = useState<boolean>(
    () => localStorage.getItem("theme") !== "light"
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const loadConversation = useCallback(async (id: string) => {
    const detail = await api.getConversation(id);
    setActiveConversation(detail);
    setActiveTab("chat");
  }, []);

  const bootstrapSession = useCallback(async () => {
    try {
      const [me, convs, availableModels] = await Promise.all([
        api.getMe(),
        api.listConversations(),
        api.listModels().catch(() => []),
      ]);
      setUser(me);
      setConversations(convs);
      setModels(availableModels);
      if (convs.length > 0) {
        await loadConversation(convs[0].id);
      } else {
        const created = await api.createConversation({
          title: "New Conversation",
          model: me.preferred_model,
        });
        setConversations([created]);
        setActiveConversation({ ...created, messages: [] });
      }
    } catch {
      localStorage.removeItem("auth_token");
      setToken(null);
      setUser(null);
    }
  }, [loadConversation]);

  useEffect(() => {
    if (token) {
      bootstrapSession();
    }
  }, [token, bootstrapSession]);

  async function handleNewChat() {
    if (!user) return;
    const created = await api.createConversation({
      title: "New Conversation",
      model: user.preferred_model,
    });
    setConversations((prev) => [created, ...prev]);
    setActiveConversation({ ...created, messages: [] });
    setActiveTab("chat");
  }

  async function handleDeleteConversation(id: string) {
    await api.deleteConversation(id);
    const remaining = conversations.filter((c) => c.id !== id);
    setConversations(remaining);
    if (activeConversation?.id === id) {
      if (remaining.length > 0) {
        await loadConversation(remaining[0].id);
      } else {
        await handleNewChat();
      }
    }
  }

  async function handleExportConversation(id: string, format: "markdown" | "json") {
    const blob = await api.exportConversation(id, format);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `conversation-${id}.${format === "json" ? "json" : "md"}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleSendMessage(content: string) {
    if (!activeConversation) return;
    const convId = activeConversation.id;
    const optimisticUserMsg = {
      id: `temp-${Date.now()}`,
      conversation_id: convId,
      role: "user" as const,
      content,
      model: activeConversation.model,
      prompt_tokens: 0,
      completion_tokens: 0,
      total_tokens: 0,
      response_time_ms: 0,
      created_at: new Date().toISOString(),
    };

    setActiveConversation((prev) =>
      prev ? { ...prev, messages: [...prev.messages, optimisticUserMsg] } : prev
    );
    setIsStreaming(true);
    setStreamingContent("");

    try {
      await api.streamChat(
        {
          conversation_id: convId,
          message: content,
          model: activeConversation.model,
          temperature,
          use_rag: activeConversation.use_rag,
        },
        (chunk) => setStreamingContent((prev) => prev + chunk),
        async () => {
          setStreamingContent("");
          const refreshed = await api.getConversation(convId);
          setActiveConversation(refreshed);
          const list = await api.listConversations();
          setConversations(list);
        }
      );
    } finally {
      setIsStreaming(false);
    }
  }

  async function handleSwitchModel(model: string) {
    if (!activeConversation) return;
    const updated = await api.updateConversation(activeConversation.id, { model });
    setActiveConversation((prev) => (prev ? { ...prev, model: updated.model } : prev));
    setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
  }

  async function handleToggleRag(use_rag: boolean) {
    if (!activeConversation) return;
    const updated = await api.updateConversation(activeConversation.id, { use_rag });
    setActiveConversation((prev) => (prev ? { ...prev, use_rag: updated.use_rag } : prev));
  }

  function handleLogout() {
    setDemoMode(false);
    localStorage.removeItem("auth_token");
    setToken(null);
    setUser(null);
    setConversations([]);
    setActiveConversation(null);
  }

  if (!token || !user) {
    return <AuthView onAuthSuccess={(newToken) => setToken(newToken)} />;
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {isDemoMode() && (
        <div className="bg-brand-500/15 border-b border-brand-500/30 px-4 py-1.5 text-xs flex items-center justify-between text-emerald-700 dark:text-emerald-300">
          <span>
            Interactive Live Demo Mode — simulated TinyLlama / Qwen2.5 streaming stored in browser
            localStorage
          </span>
          <button
            type="button"
            onClick={handleLogout}
            className="underline font-medium hover:opacity-80"
          >
            Exit Demo
          </button>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          user={user}
          conversations={conversations}
          activeId={activeConversation?.id || null}
          activeTab={activeTab}
          darkMode={darkMode}
          mobileOpen={mobileSidebarOpen}
          onCloseMobile={() => setMobileSidebarOpen(false)}
          onSelectConversation={loadConversation}
          onNewChat={handleNewChat}
          onDeleteConversation={handleDeleteConversation}
          onExportConversation={handleExportConversation}
          onOpenSettings={() => setActiveTab("settings")}
          onToggleDarkMode={() => setDarkMode((d) => !d)}
          onLogout={handleLogout}
        />

        {activeTab === "settings" ? (
          <SettingsView
            user={user}
            models={models}
            darkMode={darkMode}
            temperature={temperature}
            onChangeTemperature={setTemperature}
            onToggleDarkMode={() => setDarkMode((d) => !d)}
            onUserUpdated={setUser}
            onBackToChat={() => setActiveTab("chat")}
          />
        ) : (
          <ChatWorkspace
            conversation={activeConversation}
            models={models}
            streamingContent={streamingContent}
            isStreaming={isStreaming}
            temperature={temperature}
            onOpenMobileSidebar={() => setMobileSidebarOpen(true)}
            onSendMessage={handleSendMessage}
            onSwitchModel={handleSwitchModel}
            onToggleRag={handleToggleRag}
            onExport={(fmt) =>
              activeConversation && handleExportConversation(activeConversation.id, fmt)
            }
          />
        )}
      </div>
    </div>
  );
}

export default App;
