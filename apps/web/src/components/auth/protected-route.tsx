"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "../hooks/use-auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredRole?: string;
  fallbackPath?: string;
}

/**
 * ProtectedRoute: Client-side route guard component.
 *
 * Note: This component provides UX-level protection only.
 * All data access is ultimately controlled by the Django backend.
 * Never rely on this alone for security.
 */
export function ProtectedRoute({
  children,
  fallbackPath = "/login",
}: ProtectedRouteProps) {
  const { isLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const loginPath = `${fallbackPath}?next=${encodeURIComponent(pathname)}`;
      router.replace(loginPath);
    }
  }, [isLoading, isAuthenticated, router, pathname, fallbackPath]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}

/**
 * PermissionGate: Conditionally renders children based on client-side permission check.
 * IMPORTANT: Backend authorization is the definitive security layer.
 */
export function PermissionGate({
  children,
  permission,
  roles,
  fallback = null,
}: {
  children: React.ReactNode;
  permission?: string;
  roles?: string[];
  fallback?: React.ReactNode;
}) {
  const { user } = useAuth();

  if (!user) return <>{fallback}</>;

  // Permission check using effective_permissions from /auth/me/
  if (permission) {
    const perms = user.effective_permissions || [];
    if (!perms.includes(permission)) return <>{fallback}</>;
  }

  // Role check
  if (roles && roles.length > 0) {
    const userRoleCodes = (user.roles || []).map((r) => r.code.toUpperCase());
    const requiredRoles = roles.map((r) => r.toUpperCase());
    const hasRole = requiredRoles.some((r) => userRoleCodes.includes(r));
    if (!hasRole) return <>{fallback}</>;
  }

  return <>{children}</>;
}
