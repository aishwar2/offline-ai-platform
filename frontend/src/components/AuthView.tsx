import { useState, type FormEvent } from "react";
import { Lock, Mail, Sparkles, User as UserIcon } from "lucide-react";
import { api, setDemoMode } from "../services/api";

interface AuthViewProps {
  onAuthSuccess: (token: string) => void;
}

export function AuthView({ onAuthSuccess }: AuthViewProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await api.register({
          email,
          username,
          password,
          full_name: fullName || undefined,
        });
      }
      const tokenRes = await api.login(username, password);
      localStorage.setItem("auth_token", tokenRes.access_token);
      onAuthSuccess(tokenRes.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  function handleLaunchDemo() {
    setDemoMode(true);
    onAuthSuccess("demo-jwt-token");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 dark:bg-zinc-950 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-xl p-8">
        <div className="flex items-center gap-3 mb-6">
          <img
            src="./logo.svg"
            alt="Offline AI Platform Logo"
            className="h-10 w-10 rounded-xl shadow-sm"
          />
          <div>
            <h1 className="text-xl font-bold tracking-tight">Offline AI Platform</h1>
            <p className="text-xs text-slate-500 dark:text-zinc-400">
              Private local inference via TinyLlama &amp; Qwen2.5
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 rounded-lg bg-slate-100 dark:bg-zinc-800 p-1 mb-6">
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`py-2 text-sm font-medium rounded-md transition ${
              mode === "login"
                ? "bg-white dark:bg-zinc-900 shadow text-slate-900 dark:text-white"
                : "text-slate-500 dark:text-zinc-400"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`py-2 text-sm font-medium rounded-md transition ${
              mode === "register"
                ? "bg-white dark:bg-zinc-900 shadow text-slate-900 dark:text-white"
                : "text-slate-500 dark:text-zinc-400"
            }`}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 px-3 py-2 text-sm text-red-700 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <>
              <div>
                <label className="block text-xs font-medium mb-1">Email</label>
                <div className="relative">
                  <Mail className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@local.dev"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Full Name (optional)</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Alex Rivera"
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-medium mb-1">
              {mode === "login" ? "Username or Email" : "Username"}
            </label>
            <div className="relative">
              <UserIcon className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={mode === "login" ? "username or email" : "alex_r"}
                className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">Password</label>
            <div className="relative">
              <Lock className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="password"
                required
                minLength={mode === "register" ? 8 : 1}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-300 dark:border-zinc-700 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm transition disabled:opacity-60"
          >
            {loading
              ? "Please wait..."
              : mode === "login"
                ? "Sign In"
                : "Register & Sign In"}
          </button>
        </form>

        <div className="mt-5 pt-5 border-t border-slate-200 dark:border-zinc-800">
          <button
            type="button"
            onClick={handleLaunchDemo}
            className="w-full py-2.5 rounded-lg border border-brand-500/40 bg-brand-500/10 hover:bg-brand-500/20 text-brand-600 dark:text-emerald-400 font-medium text-sm flex items-center justify-center gap-2 transition"
          >
            <Sparkles className="h-4 w-4" />
            Launch Interactive Live Demo
          </button>
        </div>
      </div>
    </div>
  );
}
