import type { ReactNode } from 'react';

export function Spinner({ dark = false }: { dark?: boolean }) {
  return <span className={dark ? 'spinner spinner--dark' : 'spinner'} />;
}

export function LoadingBlock({ text, hint }: { text: string; hint?: ReactNode }) {
  return (
    <div className="loading-block">
      <Spinner dark />
      <div>{text}</div>
      {hint ? <div className="loading-steps">{hint}</div> : null}
    </div>
  );
}

export function EmptyState({ text, icon = '📭' }: { text: string; icon?: string }) {
  return (
    <div className="empty">
      <div className="empty__icon">{icon}</div>
      <div className="empty__text">{text}</div>
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return <div className="alert alert--danger">{message}</div>;
}

export function WarnBanner({ children }: { children: ReactNode }) {
  return <div className="alert alert--warn">{children}</div>;
}

export function InfoBanner({ children }: { children: ReactNode }) {
  return <div className="alert alert--info">{children}</div>;
}
