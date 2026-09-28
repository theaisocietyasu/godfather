import { apiJson } from '@/lib/api-client';
import type { DiscordMember, Pod, PodAction, PodConfig } from './types';

export async function fetchPods(): Promise<Pod[]> {
  const data = await apiJson<{ pods: Pod[] }>('/api/pods');
  return data.pods;
}

export async function fetchPod(podId: string): Promise<Pod> {
  const data = await apiJson<{ pod: Pod }>(`/api/pods/${podId}`);
  return data.pod;
}

export async function createPod(config: PodConfig): Promise<void> {
  await apiJson(`/api/pods`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
}

export async function runPodAction(podId: string, action: PodAction): Promise<void> {
  await apiJson(`/api/pods/${podId}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  });
}

export async function updatePod(
  podId: string,
  patch: { is_public?: boolean; allowed_users?: string[] }
): Promise<void> {
  await apiJson(`/api/pods/${podId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
}

export async function fetchDiscordMembers(): Promise<DiscordMember[]> {
  const data = await apiJson<{ members: DiscordMember[] }>('/api/discord/members');
  return data.members || [];
}
