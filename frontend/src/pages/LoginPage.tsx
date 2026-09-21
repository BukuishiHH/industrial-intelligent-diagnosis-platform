import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { ErrorBanner } from '../components/common/Feedback';
import { ApiError } from '../types/common';

type Mode = 'login' | 'register';

export function LoginPage({
  authenticated,
  onLogin,
  onRegister,
}: {
  authenticated: boolean;
  onLogin: (username: string, password: string) => Promise<void>;
  onRegister: (username: string, password: string, pwdConfirm: string) => Promise<void>;
}) {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [pwdConfirm, setPwdConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  if (authenticated) return <Navigate to="/diagnosis" replace />;

  const submit = async () => {
    setError(null);
    setNotice(null);
    if (!username.trim() || !password) {
      setError('请填写用户名与密码');
      return;
    }
    if (mode === 'register' && password !== pwdConfirm) {
      setError('两次输入的密码不一致');
      return;
    }
    setBusy(true);
    try {
      if (mode === 'login') {
        await onLogin(username.trim(), password);
        navigate('/diagnosis', { replace: true });
      } else {
        await onRegister(username.trim(), password, pwdConfirm);
        setNotice('注册成功，请使用新账号登录');
        setMode('login');
        setPassword('');
        setPwdConfirm('');
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '操作失败，请重试');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <div className="login-card">
        <h1>工业智能诊断平台</h1>
        <div className="muted">设备检修诊断 · 知识 + 数据双证据推理</div>

        {error ? <ErrorBanner message={error} /> : null}
        {notice ? <div className="alert alert--info">{notice}</div> : null}

        <div className="field">
          <label htmlFor="username">用户名</label>
          <input
            id="username"
            className="input"
            value={username}
            autoComplete="username"
            onChange={(event) => setUsername(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="password">密码</label>
          <input
            id="password"
            className="input"
            type="password"
            value={password}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            onChange={(event) => setPassword(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && mode === 'login') void submit();
            }}
          />
        </div>
        {mode === 'register' ? (
          <div className="field">
            <label htmlFor="pwdConfirm">确认密码</label>
            <input
              id="pwdConfirm"
              className="input"
              type="password"
              value={pwdConfirm}
              autoComplete="new-password"
              onChange={(event) => setPwdConfirm(event.target.value)}
            />
          </div>
        ) : null}

        <button type="button" className="btn btn--primary" style={{ width: '100%' }} disabled={busy} onClick={submit}>
          {busy ? '处理中…' : mode === 'login' ? '登录' : '注册'}
        </button>

        <div className="login-switch">
          {mode === 'login' ? (
            <>
              还没有账号？
              <button type="button" onClick={() => { setMode('register'); setError(null); }}>立即注册</button>
            </>
          ) : (
            <>
              已有账号？
              <button type="button" onClick={() => { setMode('login'); setError(null); }}>返回登录</button>
            </>
          )}
        </div>

        <div className="login-hint">
          用户名 2~12 位、密码 6~16 位。首次使用请先注册；诊断记录与审核人将关联到当前账号。
        </div>
      </div>
    </div>
  );
}
