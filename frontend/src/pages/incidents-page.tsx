import { ArrowUpRight, Filter, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getIncidents, type Incident, type Severity } from "../lib/api";

const severityOrder: Severity[] = ["critical", "high", "medium", "low"];

export function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    getIncidents(controller.signal).then(setIncidents).catch(() => setError("Unable to load the incident queue.")).finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  return <section className="mx-auto max-w-7xl px-6 py-10 lg:px-10 lg:py-14">
    <div className="animate-rise flex flex-col justify-between gap-6 md:flex-row md:items-end">
      <div><p className="eyebrow text-emerald-300">Investigation queue</p><h1 className="mt-3 font-display text-4xl font-semibold tracking-tight md:text-5xl">Incidents <span className="text-emerald-300">awaiting judgment.</span></h1></div>
      <p className="font-mono text-xs uppercase tracking-[.14em] text-stone-500">{loading ? "Synchronizing" : `${incidents.length} total investigations`}</p>
    </div>
    <div className="panel mt-10 animate-rise-delay">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-emerald-100/10 pb-5"><div className="flex items-center gap-2 text-sm text-stone-300"><Filter size={16} className="text-emerald-300" /> All severities</div><div className="flex items-center gap-2 font-mono text-xs text-stone-500"><Search size={14} /> Search and filtering arrive next</div></div>
      {loading && <p className="py-14 text-center font-mono text-xs uppercase tracking-widest text-emerald-100/45">Loading incidents...</p>}
      {error && <p className="mt-6 rounded-lg border border-red-300/20 bg-red-400/10 p-4 text-sm text-red-100">{error}</p>}
      {!loading && !error && incidents.length === 0 && <p className="py-14 text-center text-sm text-stone-500">No correlated incidents have been recorded yet.</p>}
      {!loading && !error && incidents.length > 0 && <div className="divide-y divide-emerald-100/10">{[...incidents].sort((a, b) => severityOrder.indexOf(a.severity) - severityOrder.indexOf(b.severity)).map((incident) => <IncidentListItem key={incident.id} incident={incident} />)}</div>}
    </div>
  </section>;
}

function IncidentListItem({ incident }: { incident: Incident }) {
  return <Link to={`/incidents/${incident.id}`} className="group flex items-center gap-4 py-5 transition hover:bg-emerald-100/[.025] sm:px-3"><span className={`severity-dot severity-${incident.severity}`} /><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-stone-100 group-hover:text-emerald-200">{incident.title}</p><p className="mt-1 truncate text-xs text-stone-500">{incident.summary}</p><p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-stone-600">{incident.endpoint_id} · {new Date(incident.last_event_at).toLocaleString()}</p></div><div className="hidden text-right sm:block"><span className={`severity-label severity-${incident.severity}`}>{incident.severity}</span><p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-stone-500">{incident.status.replace("_", " ")}</p></div><ArrowUpRight size={18} className="text-emerald-300/50 transition group-hover:text-emerald-300" /></Link>;
}
