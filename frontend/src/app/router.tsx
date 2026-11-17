import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";

import { AppShell } from "./shell";
import { useAuth } from "../auth/auth-context";
import { AuthPage } from "../pages/auth-page";
import { AuditPage } from "../pages/audit-page";
import { EndpointsPage } from "../pages/endpoints-page";
import { IncidentDetailPage } from "../pages/incident-detail-page";
import { IncidentsPage } from "../pages/incidents-page";
import { OverviewPage } from "../pages/overview-page";

function ProtectedLayout() { const { user, ready } = useAuth(); const location = useLocation(); if (!ready) return <div className="grid min-h-screen place-items-center bg-[#07130f] font-mono text-xs uppercase tracking-widest text-emerald-200">Restoring analyst session...</div>; if (!user) return <Navigate replace to="/auth" state={{ from: location.pathname }} />; return <AppShell />; }
export function AppRouter() { return <Routes><Route path="/auth" element={<AuthPage />} /><Route element={<ProtectedLayout />}><Route path="/overview" element={<OverviewPage />} /><Route path="/incidents" element={<IncidentsPage />} /><Route path="/incidents/:incidentId" element={<IncidentDetailPage />} /><Route path="/endpoints" element={<EndpointsPage />} /><Route path="/audit" element={<AuditPage />} /></Route><Route path="*" element={<Navigate replace to="/overview" />} /></Routes>; }

