import {
  AuthResponse,
  LoginCredentials,
  User,
  UserSession,
  PasswordChangePayload,
  PasswordResetRequestPayload,
  PasswordResetConfirmPayload,
  EmailVerificationPayload,
  PhoneVerificationPayload,
} from '@edukit/types';
import { ApiClient } from '../client';

export class AuthEndpoints {
  constructor(private client: ApiClient) {}

  login(credentials: LoginCredentials): Promise<AuthResponse> {
    return this.client.post<AuthResponse>('/auth/login/', credentials);
  }

  logout(allSessions = false): Promise<void> {
    return this.client.post<void>('/auth/logout/', { all_sessions: allSessions });
  }

  getMe(): Promise<User> {
    return this.client.get<User>('/auth/me/');
  }

  updateMe(data: Partial<User>): Promise<User> {
    return this.client.patch<User>('/auth/me/', data);
  }

  refreshSession(): Promise<User> {
    return this.client.post<User>('/auth/session/refresh/');
  }

  changePassword(data: PasswordChangePayload): Promise<{ ok: boolean; message: string }> {
    return this.client.post<{ ok: boolean; message: string }>('/auth/password/change/', data);
  }

  requestPasswordReset(data: PasswordResetRequestPayload): Promise<{ sent: boolean }> {
    return this.client.post<{ sent: boolean }>('/auth/password/reset/request/', data);
  }

  confirmPasswordReset(data: PasswordResetConfirmPayload): Promise<{ ok: boolean; message: string }> {
    return this.client.post<{ ok: boolean; message: string }>('/auth/password/reset/confirm/', data);
  }

  requestEmailVerification(email?: string): Promise<{ sent: boolean }> {
    return this.client.post<{ sent: boolean }>('/auth/verify/email/request/', { email });
  }

  confirmEmailVerification(data: EmailVerificationPayload): Promise<User> {
    return this.client.post<User>('/auth/verify/email/confirm/', data);
  }

  requestPhoneVerification(phone?: string): Promise<{ sent: boolean }> {
    return this.client.post<{ sent: boolean }>('/auth/verify/phone/request/', { phone });
  }

  confirmPhoneVerification(data: PhoneVerificationPayload): Promise<User> {
    return this.client.post<User>('/auth/verify/phone/confirm/', data);
  }

  listSessions(): Promise<UserSession[]> {
    return this.client.get<UserSession[]>('/auth/sessions/');
  }

  revokeSession(uuid: string): Promise<void> {
    return this.client.delete<void>(`/auth/sessions/${uuid}/`);
  }

  revokeOtherSessions(): Promise<{ revoked: number }> {
    return this.client.post<{ revoked: number }>('/auth/sessions/revoke-others/');
  }
}
