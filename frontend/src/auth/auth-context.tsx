import { createContext, type ReactNode, useContext, useEffect, useState } from "react";

import { getCurrentUser, login, type AuthUser, type LoginRequest, register, type RegisterRequest } from "../lib/api";

type AuthContextValue = {
  user: AuthUser | null;
  ready: boolean;
  signIn: (payload: LoginRequest) => Promise<void>;
  signUp: (payload: RegisterRequest) => Promise<void>;
  signOut: () => void;
};

const tokenKey = "sentinelai.access_token";
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = sessionStorage.getItem(tokenKey);
    if (!token) { setReady(true); return; }
    getCurrentUser().then(setUser).catch(() => sessionStorage.removeItem(tokenKey)).finally(() => setReady(true));
  }, []);

  async function signIn(payload: LoginRequest) {
    const response = await login(payload);
    sessionStorage.setItem(tokenKey, response.access_token);
    setUser(response.user);
  }

  async function signUp(payload: RegisterRequest) {
    await register(payload);
    await signIn({ email: payload.email, password: payload.password });
  }

  function signOut() { sessionStorage.removeItem(tokenKey); setUser(null); }

  return <AuthContext.Provider value={{ user, ready, signIn, signUp, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider.");
  return context;
}

export function getAccessToken() { return sessionStorage.getItem(tokenKey); }
