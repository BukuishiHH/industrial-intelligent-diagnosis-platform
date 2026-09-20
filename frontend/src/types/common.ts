/** 与后端 packages/core/Result/Result.py 对齐的统一响应结构 */
export interface ApiResult<T> {
  code: number;
  message: string;
  trace_id?: string | null;
  data: T | null;
}

/** 业务错误：code 为后端业务码（401/404/501...），code=0 表示网络层失败 */
export class ApiError extends Error {
  readonly code: number;

  constructor(code: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
  }
}
