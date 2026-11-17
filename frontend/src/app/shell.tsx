import { Activity, Bot, FileWarning, LayoutDashboard, LogOut, ScrollText, ShieldCheck } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/auth-context";

const navigation = [
  { label: "Overview", icon: LayoutDashboard, to: "/overview" },
  { label: "Incidents", icon: FileWarning, to: "/incidents", disabled: false },
  { label: "Endpoints", icon: Activity, to: "/endpoints", disabled: false },
  { label: "Audit", icon: ScrollText, to: "/audit", disabled: false, adminOnly: true },
  { label: "AI Workspace", icon: Bot, to: "/ai", disabled: true },
];

export function AppShell() {
  const { user, signOut } = useAuth();
  return <div className="min-h-screen bg-[#07130f] text-stone-100"><div className="pointer-events-none fixed inset-0 grid-bg opacity-35" /><aside className="fixed inset-y-0 left-0 z-10 hidden w-64 border-r border-emerald-100/10 bg-[#081a14]/90 p-5 backdrop-blur-xl lg:block"><div className="mb-14 flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-300 text-[#06100c] shadow-[0_0_30px_rgba(110,231,183,.25)]"><ShieldCheck size={23} strokeWidth={2.4} /></span><div><p className="font-display text-lg font-bold tracking-tight">SentinelAI</p><p className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-300/65">Security operations</p></div></div><nav className="space-y-1">{navigation.filter((item) => !item.adminOnly || user?.role === "admin").map(({ label, icon: Icon, to, disabled }) => <NavLink key={label} to={to} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""} ${disabled ? "pointer-events-none opacity-35" : ""}`}><Icon size={17} />{label}{disabled && <span className="ml-auto font-mono text-[9px] uppercase tracking-wider">Soon</span>}</NavLink>)}</nav><div className="absolute bottom-6 left-5 right-5 rounded-xl border border-emerald-100/10 bg-emerald-300/[.045] p-3"><p className="truncate text-sm text-emerald-100">{user?.full_name}</p><p className="mt-1 truncate font-mono text-[10px] text-emerald-100/45">{user?.email}</p><button onClick={signOut} className="mt-3 inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-emerald-300/80 hover:text-emerald-100"><LogOut size={13} /> Sign out</button></div></aside><main className="relative min-h-screen lg:ml-64"><header className="flex h-20 items-center justify-between border-b border-emerald-100/10 px-6 lg:px-10"><p className="font-mono text-xs uppercase tracking-[.18em] text-emerald-100/50">Live investigation workspace</p><div className="flex items-center gap-3 font-mono text-xs text-emerald-100/70"><span className="h-2 w-2 rounded-full bg-emerald-300" /> System online</div></header><Outlet /></main></div>;
}


