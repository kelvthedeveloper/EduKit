import {
  Role,
  RoleInputPayload,
  Permission,
  PermissionScope,
  RoleAssignment,
  AssignRolePayload,
} from '@edukit/types';
import { ApiClient } from '../client';

export class PermissionEndpoints {
  constructor(private client: ApiClient) {}

  listRoles(params?: { is_active?: boolean; search?: string }): Promise<Role[]> {
    return this.client.get<Role[]>('/permissions/roles/', { params });
  }

  getRole(uuid: string): Promise<Role> {
    return this.client.get<Role>(`/permissions/roles/${uuid}/`);
  }

  createRole(data: RoleInputPayload): Promise<Role> {
    return this.client.post<Role>('/permissions/roles/', data);
  }

  updateRole(uuid: string, data: Partial<RoleInputPayload>): Promise<Role> {
    return this.client.patch<Role>(`/permissions/roles/${uuid}/`, data);
  }

  deleteRole(uuid: string): Promise<void> {
    return this.client.delete<void>(`/permissions/roles/${uuid}/`);
  }

  listPermissions(params?: { resource?: string; action?: string }): Promise<Permission[]> {
    return this.client.get<Permission[]>('/permissions/', { params });
  }

  listScopes(): Promise<PermissionScope[]> {
    return this.client.get<PermissionScope[]>('/permissions/scopes/');
  }

  getUserRoles(userUuid: string): Promise<RoleAssignment[]> {
    return this.client.get<RoleAssignment[]>(`/permissions/users/${userUuid}/roles/`);
  }

  assignUserRole(userUuid: string, data: AssignRolePayload): Promise<RoleAssignment> {
    return this.client.post<RoleAssignment>(`/permissions/users/${userUuid}/roles/`, data);
  }

  removeUserRole(userUuid: string, roleCode: string): Promise<void> {
    return this.client.delete<void>(`/permissions/users/${userUuid}/roles/${roleCode}/`);
  }
}
