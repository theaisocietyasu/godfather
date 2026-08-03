import { HTMLAttributes } from 'react';
import clsx from 'clsx';

type Tone = 'neutral' | 'accent' | 'success' | 'danger' | 'warning' | 'info';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

const toneClasses: Record<Tone, string> = {
  neutral: 'bg-surface-hover text-text-secondary border-border',
  accent: 'bg-accent-soft text-accent border-accent-border',
  success: 'bg-success-soft text-success border-success/30',
  danger: 'bg-danger-soft text-danger border-danger/30',
  warning: 'bg-warning-soft text-warning border-warning/30',
  info: 'bg-info-soft text-info border-info/30',
};

export function Badge({ tone = 'neutral', className, ...props }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}

const STATUS_TONE: Record<string, Tone> = {
  running: 'success',
  stopped: 'danger',
  starting: 'warning',
  stopping: 'warning',
  error: 'danger',
  exited: 'neutral',
};

export function StatusPill({ status }: { status?: string }) {
  const key = (status || '').toLowerCase();
  const tone = STATUS_TONE[key] ?? 'neutral';
  return (
    <Badge tone={tone}>
      <span
        className={clsx('h-1.5 w-1.5 rounded-full', {
          'bg-success': tone === 'success',
          'bg-danger': tone === 'danger',
          'bg-warning': tone === 'warning',
          'bg-info': tone === 'info',
          'bg-text-muted': tone === 'neutral',
        })}
      />
      {status || 'unknown'}
    </Badge>
  );
}
