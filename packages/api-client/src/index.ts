import { client, ApiClient } from './client';
import { AuthEndpoints } from './endpoints/auth';
import { PermissionEndpoints } from './endpoints/permissions';
import { AuditEndpoints } from './endpoints/audit';

export * from './client';
export * from './endpoints';

export const authApi = new AuthEndpoints(client);
export const permissionsApi = new PermissionEndpoints(client);
export const auditApi = new AuditEndpoints(client);

export function createApiClient(baseUrl?: string) {
  const customClient = new ApiClient(baseUrl);
  return {
    client: customClient,
    auth: new AuthEndpoints(customClient),
    permissions: new PermissionEndpoints(customClient),
    audit: new AuditEndpoints(customClient),
  };
}
