/** localStorage 封装：集中管理登录态与最近一次诊断会话 */
const KEY_TOKEN = 'iip.token';
const KEY_USER = 'iip.username';
const KEY_THREAD = 'iip.lastThread';

export function getToken(): string | null {
  return localStorage.getItem(KEY_TOKEN);
}

export function setSession(token: string, username: string): void {
  localStorage.setItem(KEY_TOKEN, token);
  localStorage.setItem(KEY_USER, username);
}

export function clearSession(): void {
  localStorage.removeItem(KEY_TOKEN);
  localStorage.removeItem(KEY_USER);
  localStorage.removeItem(KEY_THREAD);
}

export function getUsername(): string {
  return localStorage.getItem(KEY_USER) ?? '';
}

/** 记住最近一次会话 thread_id：刷新页面后仍可继续澄清/审核（checkpoint 在服务端） */
export function setLastThread(threadId: string): void {
  localStorage.setItem(KEY_THREAD, threadId);
}

export function getLastThread(): string | null {
  return localStorage.getItem(KEY_THREAD);
}

export function clearLastThread(): void {
  localStorage.removeItem(KEY_THREAD);
}
