import { Server, Play, Square, Eye } from 'lucide-react';
import { Card } from '@/components/Card';
import type { Pod } from '../types';

export default function PodStats({ pods }: { pods: Pod[] }) {
  const running = pods.filter((p) => p.status?.toLowerCase() === 'running').length;
  const stopped = pods.filter((p) => p.status?.toLowerCase() === 'stopped').length;
  const publicPods = pods.filter((p) => p.is_public).length;

  const stats = [
    { label: 'Total pods', value: pods.length, icon: Server, tone: 'text-accent' },
    { label: 'Running', value: running, icon: Play, tone: 'text-success' },
    { label: 'Stopped', value: stopped, icon: Square, tone: 'text-danger' },
    { label: 'Public', value: publicPods, icon: Eye, tone: 'text-info' },
  ];

  return (
    <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map(({ label, value, icon: Icon, tone }) => (
        <Card key={label} className="p-6 transition-colors hover:border-border-strong">
          <div className="flex items-center gap-4">
            <Icon className={`h-7 w-7 ${tone}`} />
            <div>
              <p className="text-sm text-text-muted">{label}</p>
              <p className="text-2xl font-semibold text-text">{value}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
