import { AuditEvent } from '@edukit/types';
import { ApiClient } from '../client';

export class AuditEndpoints {
  constructor(private client: ApiClient) {}

  listAuditEvents(params?: {
    action?: string;
    status?: string;
    resource_type?: string;
    search?: string;
  }): Promise<AuditEvent[]> {
    return this.client.get<AuditEvent[]>('/audit/', { params });
  }

  getAuditEvent(uuid: string): Promise<AuditEvent> {
    return this.client.get<AuditEvent>(`/audit/${uuid}/`);
  }
}
