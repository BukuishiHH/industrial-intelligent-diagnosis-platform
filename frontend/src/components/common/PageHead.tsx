import type { ReactNode } from 'react';

export function PageHead({
  title,
  description,
  extra,
}: {
  title: string;
  description?: string;
  extra?: ReactNode;
}) {
  return (
    <div className="page-head">
      <div>
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {extra ? <div className="btn-row">{extra}</div> : null}
    </div>
  );
}
