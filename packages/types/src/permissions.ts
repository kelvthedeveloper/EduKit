export type ScopeCode =
  | 'GLOBAL'
  | 'ASSIGNED_CLASSES'
  | 'ASSIGNED_SUBJECTS'
  | 'DEPARTMENT'
  | 'SELECTED_CLASSES'
  | 'OWN_CHILDREN'
  | 'SELF';

export type ActionType =
  | 'VIEW'
  | 'CREATE'
  | 'UPDATE'
  | 'DELETE'
  | 'ARCHIVE'
  | 'EXPORT'
  | 'APPROVE'
  | 'PUBLISH'
  | 'MANAGE';

export interface PermissionScope {
  uuid: string;
  code: ScopeCode;
  name: string;
  description: string;
  is_system: boolean;
}

export interface Permission {
  uuid: string;
  codename: string;
  name: string;
  resource: string;
  action: ActionType;
  description: string;
  is_system: boolean;
}

export interface RolePermissionDetail {
  uuid: string;
  permission_codename: string;
  permission_name: string;
  scope_code: ScopeCode;
  scope_name: string;
  scope_parameters: Record<string, any>;
}

export interface Role {
  uuid: string;
  code: string;
  name: string;
  description: string;
  is_system: boolean;
  is_active: boolean;
  role_permissions?: RolePermissionDetail[];
  assigned_count?: number;
  created_at: string;
  updated_at: string;
}

export interface RoleInputPayload {
  code?: string;
  name: string;
  description?: string;
  is_active?: boolean;
  permissions?: {
    permission_code: string;
    scope_code?: string;
    scope_parameters?: Record<string, any>;
  }[];
}

export interface RoleAssignment {
  uuid: string;
  user_uuid: string;
  user_email: string;
  user_name: string;
  role_uuid: string;
  role_code: string;
  role_name: string;
  assigned_at: string;
  expires_at: string | null;
  scope_override_code: ScopeCode | null;
  scope_context: Record<string, any>;
  is_active: boolean;
}

export interface AssignRolePayload {
  role_code?: string;
  role_uuid?: string;
  expires_at?: string | null;
  scope_override_code?: string | null;
  scope_context?: Record<string, any>;
}
