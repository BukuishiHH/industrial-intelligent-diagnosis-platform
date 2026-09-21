import { useCallback, useState } from 'react';
import { authService } from '../services/auth.service';

/** 登录态：页面只依赖这个 hook，不直接访问 storage / api */
export function useAuth() {
  const [authenticated, setAuthenticated] = useState<boolean>(() => authService.isAuthenticated());
  const [username, setUsername] = useState<string>(() => authService.currentUsername());

  const login = useCallback(async (name: string, password: string) => {
    await authService.login(name, password);
    setUsername(name);
    setAuthenticated(true);
  }, []);

  const register = useCallback(async (name: string, password: string, pwdConfirm: string) => {
    await authService.register(name, password, pwdConfirm);
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setAuthenticated(false);
    setUsername('');
  }, []);

  return { authenticated, username, login, register, logout };
}
