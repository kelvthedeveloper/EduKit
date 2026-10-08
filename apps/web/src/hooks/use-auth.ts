"use client";

import { useAuthContext } from "../lib/auth/auth-context";

export function useAuth() {
  const { user, isLoading, isAuthenticated, login, logout, refresh } = useAuthContext();
  return {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refresh,
  };
}
