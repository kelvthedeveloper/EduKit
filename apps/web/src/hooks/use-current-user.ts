"use client";

import { useAuthContext } from "../lib/auth/auth-context";

export function useCurrentUser() {
  const { user, isLoading } = useAuthContext();

  const isVerified = Boolean(user && (user.email_verified || user.phone_verified));
  const isActive = Boolean(user && user.account_status === "ACTIVE");
  const isStaff = Boolean(user && user.is_staff);

  return {
    user,
    isLoading,
    isVerified,
    isActive,
    isStaff,
  };
}
