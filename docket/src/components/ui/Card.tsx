import type { HTMLAttributes } from 'react';
import clsx from 'clsx';

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx('bg-surface border border-line rounded-2xl', className)}
      {...rest}
    />
  );
}
