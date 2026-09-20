/** 与后端 packages/user/schemas.py 对齐 */
export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  pwd_confirm: string;
}

export interface UserOut {
  id: number;
  username: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
