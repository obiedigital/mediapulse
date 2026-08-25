import { createContext, useContext, useState, type ReactNode } from 'react';
import { demoUsers } from '../data/mockData';
import type { DemoUser } from '../types';

interface AuthContextValue {
  user: DemoUser | null;
  login: (userId: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const STORAGE_KEY = 'docket.demo.userId';

function restoreUser(): DemoUser | null {
  try {
    const savedId = localStorage.getItem(STORAGE_KEY);
    return demoUsers.find((u) => u.id === savedId) ?? null;
  } catch {
    // localStorage can throw in locked-down/private browsing contexts.
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  // Lazy-initialize from localStorage synchronously so a hard refresh on an
  // /app/* route doesn't render one authless frame and bounce to /login
  // before the session has a chance to restore.
  const [user, setUser] = useState<DemoUser | null>(restoreUser);

  const login = (userId: string) => {
    const found = demoUsers.find((u) => u.id === userId);
    if (found) {
      setUser(found);
      localStorage.setItem(STORAGE_KEY, found.id);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
