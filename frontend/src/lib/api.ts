export type Severity = "low" | "medium" | "high" | "critical";
export type IncidentStatus = "open" | "in_progress" | "resolved" | "closed";
export type AuthUser = { id: string; email: string; full_name: string; role: "admin" | "analyst" | "viewer"; is_active: boolean; created_at: string };
export type LoginRequest = { email: string; password: string };
export type RegisterRequest = LoginRequest & { full_name: string };
export type LoginResponse = { access_token: string; token_type: "bearer"; user: AuthUser };

export type Endpoint = { id: string; hostname: string; operating_system: string; agent_version: string; last_seen_at: string; created_at: string };
export type Incident = { id: string; title: string; summary: string; severity: Severity; status: IncidentStatus; endpoint_id: string; correlation_key: string; first_event_at: string; last_event_at: string; assigned_to_user_id: string | null; resolution_summary: string | null };
export type IncidentNote = { id: string; incident_id: string; author_user_id: string; body: string; created_at: string };
export type TimelineEntry = { entry_type: "alert" | "note"; occurred_at: string; title: string; detail: string; actor_user_id: string | null; related_id: string };
export type ReasoningResult = { incident_id: string; summary: string; assessment: string; recommended_actions: string[]; sources: { id: string; title: string; source_url: string }[]; model_used: string | null; disclaimer: string };
export type ThreatIntelligenceResult = { incident_id: string; mitre_techniques: { technique_id: string; source_url: string }[]; cves: { cve_id: string; description: string; cvss_score: number | null; cvss_severity: string | null; source_url: string }[]; unavailable_cve_ids: string[]; disclaimer: string };
export type AuditLog = { id: string; actor_user_id: string | null; action: string; resource_type: string; resource_id: string | null; details: Record<string, unknown>; created_at: string };

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const tokenKey = "sentinelai.access_token";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = sessionStorage.getItem(tokenKey);
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  if (!response.ok) throw new Error(`Request failed with status ${response.status}.`);
  return response.json() as Promise<T>;
}

export function login(payload: LoginRequest) { return request<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }); }
export function register(payload: RegisterRequest) { return request<AuthUser>("/auth/register", { method: "POST", body: JSON.stringify(payload) }); }
export function getCurrentUser() { return request<AuthUser>("/auth/me"); }
export function getEndpoints(signal?: AbortSignal) { return request<Endpoint[]>("/ingestion/endpoints", { signal }); }
export function getAuditLogs(signal?: AbortSignal) { return request<AuditLog[]>("/audit-logs", { signal }); }
export function getIncidents(signal?: AbortSignal) { return request<Incident[]>("/incidents", { signal }); }
export function getIncident(incidentId: string, signal?: AbortSignal) { return request<Incident>(`/incidents/${incidentId}`, { signal }); }
export function getTimeline(incidentId: string, signal?: AbortSignal) { return request<TimelineEntry[]>(`/incidents/${incidentId}/timeline`, { signal }); }
export function addNote(incidentId: string, authorUserId: string, body: string) { return request<IncidentNote>(`/incidents/${incidentId}/notes`, { method: "POST", body: JSON.stringify({ author_user_id: authorUserId, body }) }); }
export function getReasoning(incidentId: string) { return request<ReasoningResult>(`/incidents/${incidentId}/reasoning`, { method: "POST", body: JSON.stringify({}) }); }
export function getThreatIntelligence(incidentId: string, cveIds: string[]) { return request<ThreatIntelligenceResult>(`/incidents/${incidentId}/threat-intelligence`, { method: "POST", body: JSON.stringify({ cve_ids: cveIds }) }); }


