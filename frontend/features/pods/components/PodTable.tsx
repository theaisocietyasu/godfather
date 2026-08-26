'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Play, Square, RotateCw, Trash2, Eye, Plus, Server } from 'lucide-react';
import moment from 'moment';
import { StatusPill, Badge } from '@/components/Badge';
import EmptyState from '@/components/EmptyState';
import Button from '@/components/Button';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import ConfirmDialog from '@/components/ConfirmDialog';
import type { Pod, PodAction } from '../types';

interface PodTableProps {
  pods: Pod[];
  actionLoading: string | null;
  onAction: (podId: string, action: PodAction) => void;
}

// The seed "godfather" pod backs this admin portal itself and must not be
// stopped/restarted/terminated from the UI.
const isProtected = (pod: Pod) => pod.name.toLowerCase() === 'godfather';

export default function PodTable({ pods, actionLoading, onAction }: PodTableProps) {
  const router = useRouter();
  const [terminateTarget, setTerminateTarget] = useState<Pod | null>(null);

  return (
    <>
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>RunPod instances</CardTitle>
      </CardHeader>

      {pods.length === 0 ? (
        <EmptyState
          icon={Server}
          title="No pods yet"
          description="Create a pod to spin up a GPU environment for your team."
          action={
            <Button onClick={() => router.push('/dashboard/create-pod')}>
              <Plus className="h-4 w-4" />
              Create pod
            </Button>
          }
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-bg-elevated">
              <tr>
                {['Name', 'Status', 'Type', 'Visibility', 'Created', ''].map((label) => (
                  <th
                    key={label}
                    className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted last:text-right"
                  >
                    {label || 'Actions'}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {pods.map((pod) => {
                const status = pod.status?.toLowerCase();
                const protectedPod = isProtected(pod);
                return (
                  <tr key={pod.id} className="transition-colors hover:bg-surface-hover">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm font-medium text-text">{pod.name}</div>
                      <div className="text-xs text-text-muted">{pod.id}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusPill status={pod.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-text-secondary">{pod.machine_type}</td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <Badge tone={pod.is_public ? 'info' : 'neutral'}>{pod.is_public ? 'Public' : 'Private'}</Badge>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-text-muted">
                      {moment(pod.created_at).fromNow()}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => router.push(`/dashboard/pods/${pod.id}`)}
                          className="rounded p-1.5 text-info transition-colors hover:bg-info-soft"
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>

                        {status === 'stopped' && (
                          <button
                            onClick={() => onAction(pod.id, 'start')}
                            disabled={actionLoading === pod.id}
                            className="rounded p-1.5 text-success transition-colors hover:bg-success-soft disabled:opacity-50"
                            title="Start pod"
                          >
                            <Play className="h-4 w-4" />
                          </button>
                        )}

                        {status === 'running' && (
                          <>
                            <button
                              onClick={() => onAction(pod.id, 'restart')}
                              disabled={actionLoading === pod.id || protectedPod}
                              className="rounded p-1.5 text-warning transition-colors hover:bg-warning-soft disabled:cursor-not-allowed disabled:opacity-50"
                              title={protectedPod ? 'Protected pod, cannot restart' : 'Restart pod'}
                            >
                              <RotateCw className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => onAction(pod.id, 'stop')}
                              disabled={actionLoading === pod.id || protectedPod}
                              className="rounded p-1.5 text-warning transition-colors hover:bg-warning-soft disabled:cursor-not-allowed disabled:opacity-50"
                              title={protectedPod ? 'Protected pod, cannot stop' : 'Stop pod'}
                            >
                              <Square className="h-4 w-4" />
                            </button>
                          </>
                        )}

                        <button
                          onClick={() => setTerminateTarget(pod)}
                          disabled={actionLoading === pod.id || protectedPod}
                          className="rounded p-1.5 text-danger transition-colors hover:bg-danger-soft disabled:cursor-not-allowed disabled:opacity-50"
                          title={protectedPod ? 'Protected pod, cannot terminate' : 'Terminate pod'}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>

    <ConfirmDialog
      open={terminateTarget !== null}
      onClose={() => setTerminateTarget(null)}
      onConfirm={() => {
        if (terminateTarget) onAction(terminateTarget.id, 'terminate');
        setTerminateTarget(null);
      }}
      title="Terminate pod"
      description={
        terminateTarget
          ? `This permanently destroys "${terminateTarget.name}" and its storage. This action cannot be undone.`
          : ''
      }
      confirmLabel="Terminate"
      loading={terminateTarget ? actionLoading === terminateTarget.id : false}
    />
    </>
  );
}
