import { HTMLAttributes } from 'react';
import clsx from 'clsx';

export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx('animate-pulse rounded-md bg-surface-hover', className)}
      {...props}
    />
  );
}

export function LoadingScreen({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg">
      <div className="text-center">
        <div className="relative mx-auto mb-4 h-12 w-12">
          <div className="absolute inset-0 rounded-full border-2 border-accent-soft" />
          <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-accent" />
        </div>
        <p className="text-sm text-text-secondary">{label}</p>
      </div>
    </div>
  );
}
