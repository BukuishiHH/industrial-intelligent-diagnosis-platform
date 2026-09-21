import * as authApi from '../api/auth';
import type { UserOut } from '../types/auth';
import { clearSession, getToken, getUsername, setSession } from '../utils/storage';

/**
 * 登录态服务：token 的读写只在这里发生，页面与 hooks 不直接碰 localStorage，
 * 便于以后换成后端 session / 刷新 token。
 */
export const authService = {
  async login(username: string, password: string): Promise<void> {
    const token = await authApi.login({ username, password });
    setSession(token.access_token, username);
  },

  async register(username: string, password: string, pwdConfirm: string): Promise<UserOut> {
    return authApi.register({ username, password, pwd_confirm: pwdConfirm });
  },

  logout(): void {
    clearSession();
  },

  isAuthenticated(): boolean {
    return Boolean(getToken());
  },

  currentUsername(): string {
    return getUsername();
  },
};
