import { ApiError, type ApiResult } from '../types/common';
import { clearSession, getToken } from '../utils/storage';

/** 开发期由 Vite 代理到后端（vite.config.ts 的 /api -> http://127.0.0.1:8000） */
const BASE_URL = '/api';

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  query?: Record<string, string | number | undefined>;
  /** 是否需要携带 token，默认 true */
  auth?: boolean;
}

function buildQuery(query?: Record<string, string | number | undefined>): string {
  if (!query) return '';
  const pairs = Object.keys(query)
    .filter((key) => query[key] !== undefined && query[key] !== '')
    .map((key) => encodeURIComponent(key) + '=' + encodeURIComponent(String(query[key])));
  return pairs.length ? '?' + pairs.join('&') : '';
}

/**
 * 统一请求入口：
 * - 自动附加 JWT
 * - 解包后端 Result<T>，业务码非 200 抛 ApiError
 * - 401 自动清理登录态
 * - 网络层失败给出可操作的提示（后端未启动是最常见原因）
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (options.auth !== false) {
    const token = getToken();
    if (token) headers.Authorization = 'Bearer ' + token;
  }

  let response: Response;
  try {
    response = await fetch(BASE_URL + path + buildQuery(options.query), {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw new ApiError(0, '无法连接后端服务，请确认 uvicorn 已在 127.0.0.1:8000 启动');
  }

  const text = await response.text();
  let payload: ApiResult<T> | null = null;
  try {
    payload = text ? (JSON.parse(text) as ApiResult<T>) : null;
  } catch {
    payload = null;
  }
  if (!payload || typeof payload.code !== 'number') {
    throw new ApiError(response.status, '响应格式异常（HTTP ' + response.status + '）');
  }
  if (payload.code !== 200) {
    if (payload.code === 401) clearSession();
    throw new ApiError(payload.code, payload.message || '请求失败');
  }
  return payload.data as T;
}
