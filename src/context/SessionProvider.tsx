"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  fetchMe,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  setToken,
} from "@/lib/api";
import type { ApiUser, UserRole } from "@/lib/apiTypes";

interface SessionContextValue {
  user: ApiUser | null;
  /** False until the stored token has been checked against the API. */
  hydrated: boolean;
  signingIn: boolean;
  error: string | null;
  fieldErrors: Record<string, string[]>;
  signIn: (email: string, password: string) => Promise<ApiUser>;
  signUp: (input: {
    email: string;
    first_name: string;
    last_name?: string;
    password: string;
    confirm_password: string;
    phone?: string;
  }) => Promise<ApiUser>;
  signOut: () => Promise<void>;
  /** Replaces the in-memory user after a successful profile update. */
  updateUser: (user: ApiUser) => void;
  clearError: () => void;
  hasRole: (...roles: UserRole[]) => boolean;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ApiUser | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [signingIn, setSigningIn] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  // Re-check a stored token on mount so a revoked or expired one can't leave a
  // stale user in the UI.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const me = await fetchMe();
        if (!cancelled) setUser(me);
      } catch (err) {
        if (!cancelled) {
          if (err instanceof ApiError && err.isUnauthenticated) setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setHydrated(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const adopt = useCallback((nextUser: ApiUser) => {
    setUser(nextUser);
    setError(null);
    setFieldErrors({});
  }, []);

  const fail = useCallback((err: unknown) => {
    if (err instanceof ApiError) {
      setError(err.message);
      setFieldErrors(err.fieldErrors);
      return err.message;
    }
    setError("Something went wrong. Please try again in a moment.");
    return "Something went wrong. Please try again in a moment.";
  }, []);

  const signIn = useCallback(
    async (email: string, password: string) => {
      setSigningIn(true);
      setError(null);
      setFieldErrors({});
      try {
        const result = await loginRequest(email, password);
        setToken(result.token);
        adopt(result.user);
        return result.user;
      } catch (err) {
        return Promise.reject(new Error(fail(err))) as never;
      } finally {
        if (mounted.current) setSigningIn(false);
      }
    },
    [adopt, fail],
  );

  const signUp = useCallback(
    async (input: {
      email: string;
      first_name: string;
      last_name?: string;
      password: string;
      confirm_password: string;
      phone?: string;
    }) => {
      setSigningIn(true);
      setError(null);
      setFieldErrors({});
      try {
        const result = await registerRequest(input);
        setToken(result.token);
        adopt(result.user);
        return result.user;
      } catch (err) {
        return Promise.reject(new Error(fail(err))) as never;
      } finally {
        if (mounted.current) setSigningIn(false);
      }
    },
    [adopt, fail],
  );

  const signOut = useCallback(async () => {
    try {
      await logoutRequest();
    } catch {
      // The local session goes either way: the user asked to sign out.
    }
    setToken(null);
    setUser(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    setFieldErrors({});
  }, []);

  const hasRole = useCallback(
    (...roles: UserRole[]) => Boolean(user && roles.includes(user.role)),
    [user],
  );

  const value = useMemo<SessionContextValue>(
    () => ({
      user,
      hydrated,
      signingIn,
      error,
      fieldErrors,
      signIn,
      signUp,
      signOut,
      updateUser: adopt,
      clearError,
      hasRole,
    }),
    [user, hydrated, signingIn, error, fieldErrors, signIn, signUp, signOut, adopt, clearError, hasRole],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used inside <SessionProvider>");
  }
  return context;
}

/**
 * Sends a signed-out visitor to the login page, remembering where they were
 * going. Render only inside a client component.
 */
export function useRequireSession(roles?: UserRole[]) {
  const session = useSession();
  const router = useRouter();

  useEffect(() => {
    if (!session.hydrated || session.user) return;
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    router.replace(`/login?next=${next}`);
  }, [session.hydrated, session.user, router]);

  const allowed = roles ? session.hasRole(...roles) : true;
  const denied = session.hydrated && session.user !== null && !allowed;

  useEffect(() => {
    if (denied) router.replace("/");
  }, [denied, router]);

  return { ...session, allowed, denied, pending: !session.hydrated || denied };
}