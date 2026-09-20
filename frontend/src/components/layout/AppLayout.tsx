import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { authService } from '../../services/auth.service';

/** 应用外壳：顶栏 + 内容区；页面本身只关心自己的内容 */
export function AppLayout({ username, onLogout }: { username: string; onLogout: () => void }) {
  const navigate = useNavigate();
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__brand">
          工业智能诊断平台<small>设备检修诊断 BG-01</small>
        </div>
        <nav className="topbar__nav">
          <NavLink to="/diagnosis" className={({ isActive }) => (isActive ? 'is-active' : '')}>
            智能诊断
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => (isActive ? 'is-active' : '')}>
            诊断历史
          </NavLink>
        </nav>
        <div className="topbar__right">
          <span className="topbar__user">{username || '未登录'}</span>
          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={() => {
              authService.logout();
              onLogout();
              navigate('/login', { replace: true });
            }}
          >
            退出
          </button>
        </div>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
}
