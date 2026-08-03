'use client';

import { useSession } from 'next-auth/react';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import toast, { Toaster } from 'react-hot-toast';
import Navbar from '@/components/Navbar';
import { LoadingScreen } from '@/components/Skeleton';
import { verifyDiscordUser } from '@/features/auth/api';
import { fetchPods, runPodAction } from '../api';
import type { Pod, PodAction } from '../types';
import PodStats from './PodStats';
import PodTable from './PodTable';

export default function DashboardView() {
  const { data: session, status } = useSession();
  const [pods, setPods] = useState<Pod[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const router = useRouter();

  const loadPods = useCallback(async () => {
    if (!session?.user?.discordId) return;
    try {
      const data = await fetchPods(session.user.discordId);
      setPods(data);
    } catch (error: unknown) {
      console.error('Error fetching pods:', error);
      toast.error('Failed to fetch pods');
    } finally {
      setLoading(false);
    }
  }, [session]);

  const verifyAndLoadPods = useCallback(async () => {
    if (!session?.user?.discordId) {
      router.push('/');
      return;
    }

    try {
      const verifyData = await verifyDiscordUser(session.user.discordId);

      if (!verifyData.is_admin) {
        toast.error('Admin access required');
        router.push('/');
        return;
      }

      await loadPods();
    } catch (error: unknown) {
      console.error('Error during verification:', error);
      toast.error('Authentication failed');
      router.push('/');
    }
  }, [session, loadPods, router]);

  useEffect(() => {
    if (status === 'loading') return;

    if (!session) {
      router.push('/');
      return;
    }

    verifyAndLoadPods();
  }, [session, status, router, verifyAndLoadPods]);

  const handlePodAction = async (podId: string, action: PodAction) => {
    if (!session?.user?.discordId) return;
    setActionLoading(podId);
    try {
      await runPodAction(podId, action, session.user.discordId);
      toast.success(`Pod ${action} successful`);
      loadPods();
    } catch (error: unknown) {
      console.error(`Error running ${action} on pod:`, error);
      toast.error(`Failed to ${action} pod`);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return <LoadingScreen label="Loading dashboard" />;
  }

  return (
    <div className="min-h-screen bg-bg">
      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <PodStats pods={pods} />
        <PodTable pods={pods} actionLoading={actionLoading} onAction={handlePodAction} />
      </main>

      <Toaster />
    </div>
  );
}
