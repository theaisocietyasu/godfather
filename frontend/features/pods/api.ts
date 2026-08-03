import { apiJson } from '@/lib/api-client';
import type { DiscordMember, Pod, PodAction, PodConfig } from './types';

export async function fetchPods(discordId: string): Promise<Pod[]> {
  const data = await apiJson<{ pods: Pod[] }>('/api/pods', { discordId });
  return data.pods;
}

export async function fetchPod(podId: string, discordId: string): Promise<Pod> {
  const data = await apiJson<{ pod: Pod }>(`/api/pods/${podId}`, { discordId });
  return data.pod;
}

export async function createPod(config: PodConfig, discordId: string): Promise<void> {
  await apiJson(`/api/pods`, {
    method: 'POST',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
}

export async function runPodAction(podId: string, action: PodAction, discordId: string): Promise<void> {
  await apiJson(`/api/pods/${podId}/action`, {
    method: 'POST',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  });
}

export async function updatePod(
  podId: string,
  patch: { is_public?: boolean; allowed_users?: string[] },
  discordId: string
): Promise<void> {
  await apiJson(`/api/pods/${podId}`, {
    method: 'PUT',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
}

export async function fetchDiscordMembers(discordId: string): Promise<DiscordMember[]> {
  const data = await apiJson<{ members: DiscordMember[] }>('/api/discord/members', { discordId });
  return data.members || [];
}
