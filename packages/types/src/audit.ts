export interface AuditEvent {
  uuid: string;
  actor_uuid: string | null;
  actor_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  status: 'SUCCESS' | 'FAILURE' | 'DENIED';
  ip_address: string | null;
  user_agent: string;
  details: Record<string, any>;
  created_at: string;
}
