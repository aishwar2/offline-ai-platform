import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { ArrowLeft, FileText, Trash2, Upload, Users } from "lucide-react";
import { api } from "../services/api";
import type { ModelInfo, RagDocument, User } from "../types/api";

interface SettingsViewProps {
  user: User;
  models: ModelInfo[];
  darkMode: boolean;
  temperature: number;
  onChangeTemperature: (value: number) => void;
  onToggleDarkMode: () => void;
  onUserUpdated: (user: User) => void;
  onBackToChat: () => void;
}

export function SettingsView({
  user,
  models,
  darkMode,
  temperature,
  onChangeTemperature,
  onToggleDarkMode,
  onUserUpdated,
  onBackToChat,
}: SettingsViewProps) {
  const [fullName, setFullName] = useState(user.full_name || "");
  const [preferredModel, setPreferredModel] = useState(user.preferred_model);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [documents, setDocuments] = useState<RagDocument[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);

  useEffect(() => {
    api.listDocuments().then(setDocuments).catch(() => {});
    if (user.role === "admin") {
      api.listUsers().then(setAllUsers).catch(() => {});
    }
  }, [user.role]);

  async function saveProfile(e: FormEvent) {
    e.preventDefault();
    const updated = await api.updateMe({
      full_name: fullName,
      preferred_model: preferredModel,
    });
    onUserUpdated(updated);
    setStatusMsg("Profile settings saved.");
  }

  async function handleFileUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const uploaded = await api.uploadDocument(file);
      setDocuments((prev) => [uploaded, ...prev]);
      setStatusMsg(`Indexed ${uploaded.filename} (${uploaded.chunk_count} chunks).`);
    } catch (err) {
      setStatusMsg(err instanceof Error ? err.message : "Upload failed");
    }
  }

  async function handleDeleteDoc(id: string) {
    await api.deleteDocument(id);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }

  async function toggleUserActive(target: User) {
    const updated = await api.adminUpdateUser(target.id, { is_active: !target.is_active });
    setAllUsers((prev) => prev.map((u) => (u.id === target.id ? updated : u)));
  }

  const modelChoices =
    models.length > 0
      ? models.map((m) => m.name)
      : ["tinyllama", "qwen2.5:0.5b"];

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-zinc-900 p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onBackToChat}
              className="p-2 rounded-lg border border-slate-200 dark:border-zinc-700 hover:bg-white dark:hover:bg-zinc-800"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
            <h1 className="text-xl font-bold">Platform Settings</h1>
          </div>
          <button
            type="button"
            onClick={onToggleDarkMode}
            className="text-xs px-3 py-1.5 rounded-lg border border-slate-300 dark:border-zinc-700"
          >
            Theme: {darkMode ? "Dark" : "Light"}
          </button>
        </div>

        {statusMsg && (
          <div className="rounded-xl bg-brand-500/10 border border-brand-500/30 px-4 py-2.5 text-sm text-brand-600 dark:text-brand-500">
            {statusMsg}
          </div>
        )}

        <form
          onSubmit={saveProfile}
          className="rounded-2xl bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 p-6 space-y-4"
        >
          <h2 className="font-semibold">Profile &amp; Inference Defaults</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium mb-1">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 bg-transparent text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Default Model</label>
              <select
                value={preferredModel}
                onChange={(e) => setPreferredModel(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 bg-transparent text-sm"
              >
                {modelChoices.map((name) => (
                  <option key={name} value={name} className="dark:bg-zinc-900">
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">
              Sampling Temperature: {temperature.toFixed(1)}
            </label>
            <input
              type="range"
              min="0"
              max="1.5"
              step="0.1"
              value={temperature}
              onChange={(e) => onChangeTemperature(parseFloat(e.target.value))}
              className="w-full accent-brand-500"
            />
          </div>

          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium"
          >
            Save Preferences
          </button>
        </form>

        <section className="rounded-2xl bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold">Local Knowledge Base (RAG / PDF Upload)</h2>
              <p className="text-xs text-slate-500 dark:text-zinc-400">
                Upload PDF, Markdown, or TXT files for ChromaDB retrieval.
              </p>
            </div>
            <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-900 dark:bg-zinc-800 text-white text-xs font-medium">
              <Upload className="h-3.5 w-3.5" />
              Upload Document
              <input
                type="file"
                accept=".pdf,.txt,.md,.csv,.json"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>

          {documents.length === 0 ? (
            <p className="text-xs text-slate-500">No documents uploaded yet.</p>
          ) : (
            <ul className="divide-y divide-slate-200 dark:divide-zinc-800">
              {documents.map((doc) => (
                <li key={doc.id} className="py-2.5 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2.5">
                    <FileText className="h-4 w-4 text-brand-500" />
                    <span>{doc.filename}</span>
                    <span className="text-xs text-slate-400">{doc.chunk_count} chunks</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteDoc(doc.id)}
                    className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-950/50 text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {user.role === "admin" && (
          <section className="rounded-2xl bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 p-6 space-y-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-brand-500" />
              <h2 className="font-semibold">User Management (Admin)</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-zinc-800 text-xs text-slate-500">
                    <th className="py-2">Username</th>
                    <th className="py-2">Email</th>
                    <th className="py-2">Role</th>
                    <th className="py-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-zinc-800">
                  {allUsers.map((u) => (
                    <tr key={u.id}>
                      <td className="py-2 font-medium">{u.username}</td>
                      <td className="py-2 text-slate-500">{u.email}</td>
                      <td className="py-2 uppercase text-xs">{u.role}</td>
                      <td className="py-2">
                        <button
                          type="button"
                          disabled={u.id === user.id}
                          onClick={() => toggleUserActive(u)}
                          className={`text-xs px-2 py-1 rounded ${
                            u.is_active
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                              : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300"
                          }`}
                        >
                          {u.is_active ? "Active" : "Disabled"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
