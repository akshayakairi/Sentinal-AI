import { ArrowLeft, BrainCircuit, CircleAlert, ExternalLink, FileSearch, Network, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../auth/auth-context";

import { addNote, getIncident, getReasoning, getThreatIntelligence, getTimeline, type Incident, type ReasoningResult, type ThreatIntelligenceResult, type TimelineEntry } from "../lib/api";

export function IncidentDetailPage() {
  const { incidentId = "" } = useParams();
  const { user } = useAuth();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [reasoning, setReasoning] = useState<ReasoningResult | null>(null);
  const [intelligence, setIntelligence] = useState<ThreatIntelligenceResult | null>(null);
  const [cveIds, setCveIds] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reasoningLoading, setReasoningLoading] = useState(false);
  const [intelligenceLoading, setIntelligenceLoading] = useState(false);
  const [noteBody, setNoteBody] = useState("");
  const [noteSaving, setNoteSaving] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([getIncident(incidentId, controller.signal), getTimeline(incidentId, controller.signal)])
      .then(([loadedIncident, loadedTimeline]) => { setIncident(loadedIncident); setTimeline(loadedTimeline); })
      .catch(() => setError("Unable to load this investigation. It may not exist or the API is unavailable."))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [incidentId]);

  async function runReasoning() { setReasoningLoading(true); try { setReasoning(await getReasoning(incidentId)); } catch { setError("AI reasoning could not be generated. The incident evidence is still available below."); } finally { setReasoningLoading(false); } }
  async function submitNote() {
    if (!user || !noteBody.trim()) return;
    setNoteSaving(true);
    try {
      const note = await addNote(incidentId, user.id, noteBody.trim());
      setTimeline((entries) => [...entries, { entry_type: "note", occurred_at: note.created_at, title: "Analyst Note", detail: note.body, actor_user_id: note.author_user_id, related_id: note.id }]);
      setNoteBody("");
    } catch { setError("Unable to add the analyst note."); } finally { setNoteSaving(false); }
  }

  async function enrichThreats() { setIntelligenceLoading(true); try { setIntelligence(await getThreatIntelligence(incidentId, cveIds.split(/[\s,]+/).filter(Boolean))); } catch { setError("Threat intelligence enrichment is unavailable. Check CVE format and NVD connectivity."); } finally { setIntelligenceLoading(false); } }

  if (loading) return <PageMessage message="Loading investigation evidence..." />;
  if (!incident) return <PageMessage message={error ?? "Investigation not found."} error />;

  return <section className="mx-auto max-w-7xl px-6 py-8 lg:px-10 lg:py-12">
    <Link to="/incidents" className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[.14em] text-emerald-300 transition hover:text-emerald-100"><ArrowLeft size={15} /> Investigation queue</Link>
    {error && <p className="mt-5 rounded-lg border border-red-300/20 bg-red-400/10 p-4 text-sm text-red-100">{error}</p>}
    <div className="mt-7 animate-rise flex flex-col gap-5 border-b border-emerald-100/10 pb-8 lg:flex-row lg:items-end lg:justify-between"><div><div className="flex items-center gap-3"><span className={`severity-label severity-${incident.severity}`}>{incident.severity}</span><span className="font-mono text-[10px] uppercase tracking-widest text-stone-500">{incident.status.replace("_", " ")}</span></div><h1 className="mt-4 max-w-3xl font-display text-3xl font-semibold tracking-tight text-stone-50 md:text-5xl">{incident.title}</h1><p className="mt-4 max-w-3xl text-sm leading-6 text-stone-400">{incident.summary}</p></div><div className="rounded-lg border border-emerald-100/10 bg-emerald-100/[.035] px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-stone-400">Endpoint <span className="ml-2 text-emerald-200">{incident.endpoint_id}</span></div></div>
    <div className="mt-8 grid gap-6 xl:grid-cols-[1.35fr_.9fr]">
      <div className="space-y-6"><TimelinePanel entries={timeline} /><NoteComposer body={noteBody} setBody={setNoteBody} saving={noteSaving} onSubmit={submitNote} /><ReasoningPanel result={reasoning} loading={reasoningLoading} onRun={runReasoning} /></div>
      <div className="space-y-6"><ContextPanel incident={incident} /><IntelligencePanel result={intelligence} cveIds={cveIds} setCveIds={setCveIds} loading={intelligenceLoading} onRun={enrichThreats} /></div>
    </div>
  </section>;
}

function TimelinePanel({ entries }: { entries: TimelineEntry[] }) { return <div className="panel animate-rise-delay"><div className="flex items-center gap-3"><Network size={19} className="text-emerald-300" /><div><p className="eyebrow">Evidence sequence</p><h2 className="mt-1 font-display text-2xl font-semibold">Investigation timeline</h2></div></div><div className="mt-7 space-y-0">{entries.length === 0 && <p className="text-sm text-stone-500">No timeline entries yet.</p>}{entries.map((entry) => <div key={entry.related_id} className="relative border-l border-emerald-100/15 pb-7 pl-6 last:pb-0"><span className={`absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full ${entry.entry_type === "alert" ? "bg-amber-300" : "bg-emerald-300"}`} /><p className="font-mono text-[10px] uppercase tracking-wider text-stone-500">{new Date(entry.occurred_at).toLocaleString()} · {entry.entry_type}</p><p className="mt-2 text-sm font-semibold text-stone-100">{entry.title}</p><p className="mt-1 text-sm leading-6 text-stone-400">{entry.detail}</p></div>)}</div></div>; }

function NoteComposer({ body, setBody, saving, onSubmit }: { body: string; setBody: (value: string) => void; saving: boolean; onSubmit: () => void }) { return <div className="panel"><p className="eyebrow">Analyst record</p><h2 className="mt-1 font-display text-xl font-semibold">Add investigation note</h2><textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="Record a validation step, evidence finding, or handoff note..." className="input-field mt-4 min-h-28 resize-y" /><button onClick={onSubmit} disabled={saving || !body.trim()} className="action-button mt-3">{saving ? "Saving note" : "Add note"}</button></div>; }
function ReasoningPanel({ result, loading, onRun }: { result: ReasoningResult | null; loading: boolean; onRun: () => void }) { return <div className="panel animate-rise-delay-2"><div className="flex items-start justify-between gap-4"><div className="flex items-center gap-3"><BrainCircuit size={19} className="text-emerald-300" /><div><p className="eyebrow">RAG investigation aid</p><h2 className="mt-1 font-display text-2xl font-semibold">AI reasoning</h2></div></div><button onClick={onRun} disabled={loading} className="action-button">{loading ? "Analyzing" : result ? "Refresh" : "Generate"}</button></div>{!result && !loading && <p className="mt-6 text-sm leading-6 text-stone-400">Generate a source-grounded assessment from the correlated alerts and security knowledge base.</p>}{result && <div className="mt-6 space-y-5"><p className="text-sm leading-6 text-stone-300">{result.assessment}</p><div><p className="eyebrow">Recommended validation</p><ul className="mt-3 space-y-2">{result.recommended_actions.map((action) => <li key={action} className="flex gap-2 text-sm text-stone-400"><Sparkles size={14} className="mt-1 shrink-0 text-emerald-300" />{action}</li>)}</ul></div><p className="border-t border-emerald-100/10 pt-4 text-xs text-stone-500">{result.disclaimer}</p></div>}</div>; }

function ContextPanel({ incident }: { incident: Incident }) { return <div className="panel"><p className="eyebrow">Investigation context</p><dl className="mt-5 space-y-4 text-sm"><div><dt className="text-stone-500">Correlation key</dt><dd className="mt-1 break-all font-mono text-xs text-emerald-100">{incident.correlation_key}</dd></div><div><dt className="text-stone-500">First observed</dt><dd className="mt-1 text-stone-200">{new Date(incident.first_event_at).toLocaleString()}</dd></div><div><dt className="text-stone-500">Assigned analyst</dt><dd className="mt-1 text-stone-200">{incident.assigned_to_user_id ?? "Unassigned"}</dd></div></dl></div>; }

function IntelligencePanel({ result, cveIds, setCveIds, loading, onRun }: { result: ThreatIntelligenceResult | null; cveIds: string; setCveIds: (value: string) => void; loading: boolean; onRun: () => void }) { return <div className="panel"><div className="flex items-center gap-3"><FileSearch size={19} className="text-amber-300" /><div><p className="eyebrow">External context</p><h2 className="mt-1 font-display text-2xl font-semibold">Threat intelligence</h2></div></div><label className="mt-6 block"><span className="font-mono text-[10px] uppercase tracking-widest text-stone-500">CVE IDs, optional</span><input value={cveIds} onChange={(event) => setCveIds(event.target.value)} placeholder="CVE-2025-1234, CVE-2024-5678" className="input-field mt-2" /></label><button onClick={onRun} disabled={loading} className="action-button mt-3 w-full">{loading ? "Querying sources" : "Enrich investigation"}</button>{result && <div className="mt-6 space-y-5"><div><p className="eyebrow">Observed MITRE techniques</p><div className="mt-3 flex flex-wrap gap-2">{result.mitre_techniques.map((technique) => <a key={technique.technique_id} href={technique.source_url} target="_blank" rel="noreferrer" className="technique-link">{technique.technique_id}<ExternalLink size={11} /></a>)}</div></div>{result.cves.map((cve) => <a key={cve.cve_id} href={cve.source_url} target="_blank" rel="noreferrer" className="block rounded-lg border border-emerald-100/10 p-3 transition hover:border-emerald-300/30"><div className="flex items-center justify-between gap-2"><span className="font-mono text-xs text-emerald-200">{cve.cve_id}</span><span className="text-xs text-amber-200">CVSS {cve.cvss_score ?? "N/A"}</span></div><p className="mt-2 line-clamp-3 text-xs leading-5 text-stone-400">{cve.description}</p></a>)}{result.unavailable_cve_ids.length > 0 && <p className="text-xs text-amber-200">Unavailable: {result.unavailable_cve_ids.join(", ")}</p>}<p className="text-xs text-stone-500">{result.disclaimer}</p></div>}</div>; }

function PageMessage({ message, error = false }: { message: string; error?: boolean }) { return <section className="mx-auto max-w-3xl px-6 py-20"><div className={`panel text-center ${error ? "border-red-300/25" : ""}`}><CircleAlert className="mx-auto text-emerald-300" /><p className="mt-4 text-sm text-stone-400">{message}</p></div></section>; }


