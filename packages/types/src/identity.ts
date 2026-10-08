export type AccountStatus =
  | 'ACTIVE'
  | 'INACTIVE'
  | 'SUSPENDED'
  | 'PENDING_VERIFICATION';

export interface RoleSummary {
  uuid: string;
  code: string;
  name: string;
}

export interface User {
  uuid: string;
  email: string | null;
  phone: string | null;
  username: string | null;
  first_name: string;
  last_name: string;
  display_name: string;
  name: string;
  full_name?: string;
  account_status: AccountStatus;
  email_verified: boolean;
  phone_verified: boolean;
  is_staff: boolean;
  last_login: string | null;
  last_active: string | null;
  created_at: string;
  updated_at: string;
  roles?: RoleSummary[];
  effective_permissions?: string[];
}

export interface UserSession {
  uuid: string;
  user_uuid: string;
  session_key?: string | null;
  device_id: string;
  device_name: string;
  ip_address: string | null;
  auth_source: string;
  last_activity: string;
  expires_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface LoginCredentials {
  identifier: string;
  password: string;
  remember?: boolean;
  device_id?: string;
  device_name?: string;
}

export interface AuthResponse {
  user_uuid: string;
  name: string;
  email: string | null;
  phone: string | null;
  display_name: string;
  account_status: AccountStatus;
  email_verified: boolean;
  phone_verified: boolean;
  roles: RoleSummary[];
  session_uuid?: string | null;
  access_token?: string;
  refresh_token?: string;
}

export interface PasswordChangePayload {
  old_password: string;
  new_password: string;
}

export interface PasswordResetRequestPayload {
  identifier: string;
}

export interface PasswordResetConfirmPayload {
  token: string;
  new_password: string;
}

export interface EmailVerificationPayload {
  token: string;
}

export interface PhoneVerificationPayload {
  phone: string;
  code: string;
}
