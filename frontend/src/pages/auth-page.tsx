import { ShieldCheck } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../auth/auth-context";

export function AuthPage() {
  const { user, signIn, signUp } = useAuth();
  const location = useLocation();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate replace to={(location.state as { from?: string } | null)?.from ?? "/overview"} />;

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(null); setSubmitting(true);
    try {
      if (mode === "login") await signIn({ email, password });
      else await signUp({ email, password, full_name: fullName });
    } catch { setError(mode === "login" ? "Invalid credentials or unavailable API." : "Unable to create the account. The email may already be in use."); }
    finally { setSubmitting(false); }
  }

  return <main className="auth-page"><div className="auth-orb auth-orb-one" /><div className="auth-orb auth-orb-two" /><section className="auth-card"><div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-emerald-300 text-[#06100c]"><ShieldCheck size={24} /></span><div><p className="font-display text-xl font-bold">SentinelAI</p><p className="font-mono text-[10px] uppercase tracking-[.2em] text-emerald-300/70">Security operations</p></div></div><div className="mt-10"><p className="eyebrow text-emerald-300">Analyst access</p><h1 className="mt-3 font-display text-3xl font-semibold">{mode === "login" ? "Enter the workspace." : "Create your analyst account."}</h1><p className="mt-3 text-sm leading-6 text-stone-400">Use your SentinelAI account to keep investigation actions attributable.</p></div><form onSubmit={submit} className="mt-8 space-y-4">{mode === "register" && <label className="block"><span className="auth-label">Full name</span><input required minLength={2} value={fullName} onChange={(event) => setFullName(event.target.value)} className="input-field mt-2" /></label>}<label className="block"><span className="auth-label">Email</span><input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="input-field mt-2" /></label><label className="block"><span className="auth-label">Password</span><input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="input-field mt-2" /></label>{error && <p className="rounded-lg border border-red-300/20 bg-red-400/10 p-3 text-xs text-red-100">{error}</p>}<button disabled={submitting} className="action-button mt-2 w-full py-3">{submitting ? "Verifying" : mode === "login" ? "Sign in" : "Create account"}</button></form><button onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }} className="mt-6 w-full text-center text-xs text-emerald-200/80 hover:text-emerald-100">{mode === "login" ? "Need an account? Register as an analyst" : "Already registered? Sign in"}</button></section></main>;
}

