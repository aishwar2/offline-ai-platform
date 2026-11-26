import { useState, type FormEvent } from "react";
import { Bot, Database, Download, Menu, Send, Sparkles, User as UserIcon } from "lucide-react";
import type { ConversationDetail, Message, ModelInfo } from "../types/api";

interface ChatWorkspaceProps {
  conversation: ConversationDetail | null;
  models: ModelInfo[];
  streamingContent: string;
  isStreaming: boolean;
  temperature: number;
  onOpenMobileSidebar: () => void;
  onSendMessage: (content: string) => Promise<void>;
  onSwitchModel: (model: string) => Promise<void>;
  onToggleRag: (enabled: boolean) => Promise<void>;
  onExport: (format: "markdown" | "json") => void;
}

export function ChatWorkspace({
  conversation,
  models,
  streamingContent,
  isStreaming,
  temperature,
  onOpenMobileSidebar,
  onSendMessage,
  onSwitchModel,
  onToggleRag,
  onExport,
}: ChatWorkspaceProps) {
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!prompt.trim() || isStreaming) return;
    const text = prompt.trim();
    setPrompt("");
    setError(null);
    try {
      await onSendMessage(text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    }
  }

  const availableModels =
    models.length > 0
      ? models
      : [
          { name: "tinyllama", size_bytes: 0, is_default: true },
          { name: "qwen2.5:0.5b", size_bytes: 0, is_default: false },
        ];

  return (
    <div className="flex-1 flex flex-col h-full bg-white dark:bg-zinc-900">
      <header className="h-14 px-4 border-b border-slate-200 dark:border-zinc-800 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <button
            type="button"
            onClick={onOpenMobileSidebar}
            className="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-zinc-800"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <h2 className="font-semibold text-sm truncate">
            {conversation ? conversation.title : "Offline AI Chat"}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {conversation && (
            <>
              <label className="hidden sm:flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-zinc-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={conversation.use_rag}
                  onChange={(e) => onToggleRag(e.target.checked)}
                  className="accent-brand-500"
                />
                <Database className="h-3.5 w-3.5 text-brand-500" />
                RAG
              </label>

              <select
                value={conversation.model}
                onChange={(e) => onSwitchModel(e.target.value)}
                aria-label="Select AI Model"
                className="text-xs rounded-lg border border-slate-200 dark:border-zinc-700 bg-transparent px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                {availableModels.map((m) => (
                  <option key={m.name} value={m.name} className="dark:bg-zinc-900">
                    {m.name}
                  </option>
                ))}
              </select>

              <button
                type="button"
                onClick={() => onExport("json")}
                title="Export JSON"
                className="hidden sm:inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-zinc-700 hover:bg-slate-100 dark:hover:bg-zinc-800"
              >
                <Download className="h-3.5 w-3.5" />
                JSON
              </button>
            </>
          )}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {!conversation || conversation.messages.length === 0 ? (
            <div className="text-center py-20">
              <div className="h-12 w-12 rounded-2xl bg-brand-500/10 text-brand-500 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Ready for private offline inference</h3>
              <p className="text-sm text-slate-500 dark:text-zinc-400 max-w-md mx-auto">
                Running locally with TinyLlama or Qwen2.5 0.5B — optimized for 2 CPU / 4 GB RAM
                without GPU dependencies.
              </p>
            </div>
          ) : (
            conversation.messages.map((msg: Message) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role !== "user" && (
                  <div className="h-8 w-8 rounded-lg bg-brand-500 text-white flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed ${
                    msg.role === "user"
                      ? "bg-brand-500 text-white"
                      : "bg-slate-100 dark:bg-zinc-800 text-slate-900 dark:text-zinc-100"
                  }`}
                >
                  {msg.content}
                  {msg.role === "assistant" && (
                    <div className="mt-2 pt-2 border-t border-slate-200/70 dark:border-zinc-700/70 flex flex-wrap gap-3 text-[11px] text-slate-500 dark:text-zinc-400">
                      <span>Model: {msg.model || conversation.model}</span>
                      <span>Tokens: {msg.total_tokens}</span>
                      <span>Latency: {msg.response_time_ms.toFixed(0)} ms</span>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="h-8 w-8 rounded-lg bg-slate-200 dark:bg-zinc-700 flex items-center justify-center shrink-0 mt-0.5">
                    <UserIcon className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {isStreaming && (
            <div className="flex gap-3 justify-start">
              <div className="h-8 w-8 rounded-lg bg-brand-500 text-white flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="h-4 w-4" />
              </div>
              <div className="max-w-[82%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap bg-slate-100 dark:bg-zinc-800">
                {streamingContent || "Thinking..."}
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 p-3 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}
        </div>
      </div>

      <footer className="p-4 border-t border-slate-200 dark:border-zinc-800">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Message Offline AI..."
            disabled={isStreaming}
            className="flex-1 rounded-xl border border-slate-300 dark:border-zinc-700 bg-transparent px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            type="submit"
            disabled={isStreaming || !prompt.trim()}
            className="px-4 py-3 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm flex items-center gap-2 transition disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
        <p className="text-[11px] text-center text-slate-400 mt-2">
          Temperature: {temperature.toFixed(1)} • Fully offline local execution
        </p>
      </footer>
    </div>
  );
}
