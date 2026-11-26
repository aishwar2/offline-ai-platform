import {
  Download,
  LogOut,
  MessageSquare,
  Moon,
  Plus,
  Settings,
  Sun,
  Trash2,
  X,
} from "lucide-react";
import type { Conversation, User } from "../types/api";

interface SidebarProps {
  user: User;
  conversations: Conversation[];
  activeId: string | null;
  activeTab: "chat" | "settings";
  darkMode: boolean;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: string) => void;
  onExportConversation: (id: string, format: "markdown" | "json") => void;
  onOpenSettings: () => void;
  onToggleDarkMode: () => void;
  onLogout: () => void;
}

export function Sidebar({
  user,
  conversations,
  activeId,
  activeTab,
  darkMode,
  mobileOpen,
  onCloseMobile,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  onExportConversation,
  onOpenSettings,
  onToggleDarkMode,
  onLogout,
}: SidebarProps) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-72 flex flex-col bg-slate-900 text-slate-100 dark:bg-zinc-950 border-r border-slate-800 dark:border-zinc-800 transform transition-transform md:static md:translate-x-0 ${
        mobileOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      <div className="p-3 space-y-2 border-b border-slate-800 dark:border-zinc-800">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <img src="./logo.svg" alt="Offline AI Logo" className="h-6 w-6 rounded-md" />
            <span className="text-sm font-semibold tracking-tight">Offline AI</span>
          </div>
          <button
            type="button"
            onClick={onCloseMobile}
            className="md:hidden p-1.5 rounded-lg hover:bg-slate-800"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <button
          type="button"
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 rounded-lg border border-slate-700 hover:bg-slate-800 py-2 px-3 text-sm font-medium transition"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {conversations.length === 0 ? (
          <p className="text-xs text-slate-400 px-3 py-4 text-center">
            No conversations yet. Start a new chat!
          </p>
        ) : (
          conversations.map((conv) => {
            const selected = activeTab === "chat" && conv.id === activeId;
            return (
              <div
                key={conv.id}
                className={`group flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm cursor-pointer transition ${
                  selected ? "bg-slate-800 text-white" : "text-slate-300 hover:bg-slate-800/60"
                }`}
                onClick={() => {
                  onSelectConversation(conv.id);
                  onCloseMobile();
                }}
              >
                <MessageSquare className="h-4 w-4 shrink-0 text-slate-400" />
                <span className="truncate flex-1">{conv.title}</span>
                <div className="hidden group-hover:flex items-center gap-1">
                  <button
                    type="button"
                    title="Export Markdown"
                    onClick={(e) => {
                      e.stopPropagation();
                      onExportConversation(conv.id, "markdown");
                    }}
                    className="p-1 rounded hover:bg-slate-700 text-slate-300"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    title="Delete Conversation"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    className="p-1 rounded hover:bg-red-900/60 text-red-400"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="p-3 border-t border-slate-800 dark:border-zinc-800 space-y-1">
        <button
          type="button"
          onClick={onToggleDarkMode}
          className="w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 transition"
        >
          {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {darkMode ? "Light Mode" : "Dark Mode"}
        </button>

        <button
          type="button"
          onClick={() => {
            onOpenSettings();
            onCloseMobile();
          }}
          className={`w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition ${
            activeTab === "settings"
              ? "bg-slate-800 text-white"
              : "text-slate-300 hover:bg-slate-800"
          }`}
        >
          <Settings className="h-4 w-4" />
          Settings
        </button>

        <div className="pt-2 mt-2 border-t border-slate-800 flex items-center justify-between px-2">
          <div className="min-w-0">
            <p className="text-xs font-medium truncate">{user.username}</p>
            <p className="text-[11px] text-slate-400 uppercase">{user.role}</p>
          </div>
          <button
            type="button"
            onClick={onLogout}
            title="Sign Out"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
