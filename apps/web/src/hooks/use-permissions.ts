"use client";

import { useAuthContext } from "../lib/auth/auth-context";

export function usePermissions() {
  const { user } = useAuthContext();

  const effectivePermissions = user?.effective_permissions || [];
  const roles = user?.roles?.map((r) => r.code) || [];

  const can = (permissionCodename: string): boolean => {
    if (!user) return false;
    if (user.is_staff && user.account_status === "ACTIVE") {
      // Staff with super access fallback or check explicit permission
    }
    return effectivePermissions.includes(permissionCodename);
  };

  const hasRole = (roleCode: string): boolean => {
    if (!user) return false;
    const clean = roleCode.toUpperCase();
    return roles.includes(clean);
  };

  const hasAnyRole = (roleCodes: string[]): boolean => {
    if (!user) return false;
    const cleanList = roleCodes.map((r) => r.toUpperCase());
    return roles.some((r) => cleanList.includes(r));
  };

  return {
    can,
    hasRole,
    hasAnyRole,
    roles,
    effectivePermissions,
  };
}
