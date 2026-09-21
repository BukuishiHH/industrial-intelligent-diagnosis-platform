import type { LoginPayload, RegisterPayload, TokenResponse, UserOut } from '../types/auth';
import { request } from './client';

export function login(payload: LoginPayload): Promise<TokenResponse> {
  return request<TokenResponse>('/user/login', { method: 'POST', body: payload, auth: false });
}

export function register(payload: RegisterPayload): Promise<UserOut> {
  return request<UserOut>('/user/register', { method: 'POST', body: payload, auth: false });
}
