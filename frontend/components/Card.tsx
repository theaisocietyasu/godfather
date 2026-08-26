import { HTMLAttributes } from 'react';
import clsx from 'clsx';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** 'glass' (default) applies the frosted glass treatment; 'solid' opts out for surfaces stacked on top of other glass panels. */
  variant?: 'glass' | 'solid';
}

export function Card({ className, variant = 'glass', ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-xl',
        variant === 'glass' ? 'glass' : 'border border-border bg-surface',
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('px-6 py-4 border-b border-border', className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={clsx('text-base font-semibold text-text', className)} {...props} />;
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('p-6', className)} {...props} />;
}
