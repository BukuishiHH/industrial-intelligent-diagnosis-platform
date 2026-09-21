import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { RequireAuth } from './components/layout/RequireAuth';
import { useAuth } from './hooks/useAuth';
import { DiagnosisPage } from './pages/DiagnosisPage';
import { HistoryPage } from './pages/HistoryPage';
import { LoginPage } from './pages/LoginPage';
import { ReportPage } from './pages/ReportPage';

export default function App() {
  const { authenticated, username, login, register, logout } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage authenticated={authenticated} onLogin={login} onRegister={register} />}
      />
      <Route
        element={
          <RequireAuth>
            <AppLayout username={username} onLogout={logout} />
          </RequireAuth>
        }
      >
        <Route path="/diagnosis" element={<DiagnosisPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/report/:reportId" element={<ReportPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/diagnosis" replace />} />
    </Routes>
  );
}
