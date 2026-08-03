'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import toast, { Toaster } from 'react-hot-toast';
import {
  Server as ServerIcon,
  Play as PlayIcon,
  Square as StopIcon,
  RotateCw as RestartIcon,
  Trash2 as TrashIcon,
  Folder as FolderIcon,
  Pencil as EditIcon,
  X as XIcon,
  Save as SaveIcon,
} from 'lucide-react';
import moment from 'moment';
import Image from 'next/image';
import Navbar from '@/components/Navbar';
import { LoadingScreen } from '@/components/Skeleton';
import { Card, CardHeader, CardTitle, CardBody } from '@/components/Card';
import { StatusPill, Badge } from '@/components/Badge';
import Button from '@/components/Button';
import EmptyState from '@/components/EmptyState';
import FileManager from '@/features/files/components/FileManager';
import { verifyDiscordUser } from '@/features/auth/api';
import { fetchPod, runPodAction, updatePod, fetchDiscordMembers } from '../api';
import type { DiscordMember, Pod, PodAction } from '../types';

export default function PodDetail() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const params = useParams();
  const podId = params.id as string;

  const [pod, setPod] = useState<Pod | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showFileManager, setShowFileManager] = useState(false);
  const [verifyingAuth, setVerifyingAuth] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [discordMembers, setDiscordMembers] = useState<DiscordMember[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(true);

  const [editForm, setEditForm] = useState({
    is_public: false,
    allowed_users: [] as string[],
  });

  const verifyAdmin = useCallback(async () => {
    if (status === 'loading') return;

    if (!session?.user?.discordId) {
      router.push('/');
      return;
    }

    try {
      const data = await verifyDiscordUser(session.user.discordId);
      if (!data.is_admin) {
        toast.error('Admin access required');
        router.push('/');
        return;
      }
      setVerifyingAuth(false);
    } catch (error) {
      console.error('Auth verification error:', error);
      toast.error('Authentication failed');
      router.push('/');
    }
  }, [session, status, router]);

  useEffect(() => {
    verifyAdmin();
  }, [verifyAdmin]);

  const loadPod = useCallback(async () => {
    if (!session?.user?.discordId) return;
    try {
      const data = await fetchPod(podId, session.user.discordId);
      setPod(data);
    } catch (error: unknown) {
      console.error('Error fetching pod details:', error);
      toast.error('Failed to fetch pod details');
      router.push('/dashboard');
    } finally {
      setLoading(false);
    }
  }, [podId, session, router]);

  useEffect(() => {
    if (verifyingAuth) return;
    loadPod();
  }, [verifyingAuth, loadPod]);

  useEffect(() => {
    if (verifyingAuth || !session?.user?.discordId) return;

    const loadMembers = async () => {
      try {
        const members = await fetchDiscordMembers(session.user.discordId);
        setDiscordMembers(members);
      } catch (error) {
        console.error('Error fetching Discord members:', error);
      } finally {
        setLoadingMembers(false);
      }
    };

    loadMembers();
  }, [session, verifyingAuth]);

  useEffect(() => {
    if (pod) {
      setEditForm({ is_public: pod.is_public, allowed_users: pod.allowed_users || [] });
    }
  }, [pod]);

  const handlePodAction = async (action: PodAction) => {
    if (!session?.user?.discordId) return;
    setActionLoading(true);
    try {
      await runPodAction(podId, action, session.user.discordId);
      toast.success(`Pod ${action} successful`);
      loadPod();
    } catch (error: unknown) {
      console.error(`Error running ${action} on pod:`, error);
      toast.error(`Failed to ${action} pod`);
    } finally {
      setActionLoading(false);
    }
  };

  const togglePublicAccess = async () => {
    if (!pod || !session?.user?.discordId) return;
    try {
      await updatePod(podId, { is_public: !pod.is_public }, session.user.discordId);
      setPod({ ...pod, is_public: !pod.is_public });
      toast.success(`Pod is now ${!pod.is_public ? 'public' : 'private'}`);
    } catch (error: unknown) {
      console.error('Error updating pod access:', error);
      toast.error('Failed to update pod access');
    }
  };

  const handleSaveEdit = async () => {
    if (!pod || !session?.user?.discordId) return;
    setEditLoading(true);
    try {
      await updatePod(podId, editForm, session.user.discordId);
      setPod({ ...pod, ...editForm });
      toast.success('Pod updated');
      setShowEditModal(false);
      loadPod();
    } catch (error: unknown) {
      console.error('Error updating pod:', error);
      toast.error('Failed to update pod');
    } finally {
      setEditLoading(false);
    }
  };

  const toggleUserSelection = (userId: string) => {
    setEditForm((prev) => ({
      ...prev,
      allowed_users: prev.allowed_users.includes(userId)
        ? prev.allowed_users.filter((id) => id !== userId)
        : [...prev.allowed_users, userId],
    }));
  };

  if (verifyingAuth || loading) {
    return <LoadingScreen label={verifyingAuth ? 'Verifying access' : 'Loading pod details'} />;
  }

  if (!pod) {
    return (
      <div className="min-h-screen bg-bg">
        <Navbar />
        <div className="mx-auto max-w-3xl px-4 py-16">
          <EmptyState
            icon={ServerIcon}
            title="Pod not found"
            description="The requested pod could not be found."
            action={<Button onClick={() => router.push('/dashboard')}>Back to dashboard</Button>}
          />
        </div>
      </div>
    );
  }

  const podStatus = pod.status?.toLowerCase();

  return (
    <div className="min-h-screen bg-bg">
      <Navbar />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-text">{pod.name}</h1>
            <p className="text-sm text-text-muted">{pod.id}</p>
          </div>
          <StatusPill status={pod.status} />
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Pod information</CardTitle>
              </CardHeader>
              <CardBody className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-text-muted">Machine type</dt>
                  <dd className="mt-1 text-sm text-text-secondary">{pod.machine_type}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-muted">Created</dt>
                  <dd className="mt-1 text-sm text-text-secondary">
                    {moment(pod.created_at).format('MMMM Do YYYY, h:mm a')}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-muted">Runtime</dt>
                  <dd className="mt-1 text-sm text-text-secondary">
                    {pod.runtime ? moment(pod.created_at).fromNow() : 'Not started'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-text-muted">Access</dt>
                  <dd className="mt-1">
                    <Badge tone={pod.is_public ? 'info' : 'neutral'}>{pod.is_public ? 'Public' : 'Private'}</Badge>
                  </dd>
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Machine details</CardTitle>
              </CardHeader>
              <CardBody>
                {pod.machine ? (
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {(pod.machine as Record<string, unknown>).gpuDisplayName === 'unknown' ||
                    (pod.machine as Record<string, unknown>).cpuFlavor ? (
                      <>
                        <div>
                          <dt className="text-sm font-medium text-text-muted">Compute type</dt>
                          <dd className="mt-1 text-sm text-text-secondary">CPU-only instance</dd>
                        </div>
                        {(pod.machine as Record<string, unknown>).vcpuTotal !== undefined && (
                          <div>
                            <dt className="text-sm font-medium text-text-muted">vCPU cores</dt>
                            <dd className="mt-1 text-sm text-text-secondary">
                              {String((pod.machine as Record<string, unknown>).vcpuTotal)}
                            </dd>
                          </div>
                        )}
                        {(pod.machine as Record<string, unknown>).memoryTotal !== undefined && (
                          <div>
                            <dt className="text-sm font-medium text-text-muted">Memory</dt>
                            <dd className="mt-1 text-sm text-text-secondary">
                              {String((pod.machine as Record<string, unknown>).memoryTotal)} GB
                            </dd>
                          </div>
                        )}
                        {(pod.machine as Record<string, unknown>).location !== undefined && (
                          <div>
                            <dt className="text-sm font-medium text-text-muted">Location</dt>
                            <dd className="mt-1 text-sm text-text-secondary">
                              {String((pod.machine as Record<string, unknown>).location)}
                            </dd>
                          </div>
                        )}
                      </>
                    ) : (
                      Object.entries(pod.machine).map(([key, value]) => (
                        <div key={key}>
                          <dt className="text-sm font-medium capitalize text-text-muted">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </dt>
                          <dd className="mt-1 text-sm text-text-secondary">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </dd>
                        </div>
                      ))
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-text-muted">No machine details available</p>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader className="flex items-center justify-between">
                <CardTitle>File manager</CardTitle>
                <Button size="sm" variant="secondary" onClick={() => setShowFileManager(!showFileManager)}>
                  {showFileManager ? 'Hide' : 'Show'} files
                </Button>
              </CardHeader>
              {showFileManager && (
                <CardBody>
                  {podStatus === 'running' ? (
                    <FileManager podId={podId} />
                  ) : (
                    <EmptyState
                      icon={FolderIcon}
                      title="Pod is not running"
                      description="The file manager is only available while the pod is running."
                    />
                  )}
                </CardBody>
              )}
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Quick actions</CardTitle>
              </CardHeader>
              <CardBody className="space-y-3">
                {podStatus === 'stopped' && (
                  <Button className="w-full" onClick={() => handlePodAction('start')} loading={actionLoading}>
                    {!actionLoading && <PlayIcon className="h-4 w-4" />}
                    Start pod
                  </Button>
                )}

                {podStatus === 'running' && (
                  <>
                    <Button
                      className="w-full"
                      variant="secondary"
                      onClick={() => handlePodAction('restart')}
                      disabled={actionLoading}
                    >
                      <RestartIcon className="h-4 w-4" />
                      Restart pod
                    </Button>
                    <Button
                      className="w-full"
                      variant="secondary"
                      onClick={() => handlePodAction('stop')}
                      disabled={actionLoading}
                    >
                      <StopIcon className="h-4 w-4" />
                      Stop pod
                    </Button>
                  </>
                )}

                <Button className="w-full" variant="secondary" onClick={() => setShowEditModal(true)}>
                  <EditIcon className="h-4 w-4" />
                  Edit pod settings
                </Button>

                <Button
                  className="w-full"
                  variant="danger"
                  onClick={() => handlePodAction('terminate')}
                  disabled={actionLoading}
                >
                  <TrashIcon className="h-4 w-4" />
                  Terminate pod
                </Button>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Access control</CardTitle>
              </CardHeader>
              <CardBody className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-text-secondary">Public access</span>
                  <button
                    onClick={togglePublicAccess}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                      pod.is_public ? 'bg-accent' : 'bg-surface-hover'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        pod.is_public ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                <p className="text-xs text-text-muted">
                  {pod.is_public
                    ? 'Any authenticated Discord member can connect to this pod via CLI.'
                    : 'Only administrators can access this pod.'}
                </p>

                {pod.is_public && (
                  <div className="rounded-lg border border-info/30 bg-info-soft p-3">
                    <p className="text-sm text-text-secondary">
                      Users connect with the godfather CLI. Each user gets an isolated workspace folder.
                    </p>
                  </div>
                )}
              </CardBody>
            </Card>
          </div>
        </div>
      </main>

      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-border bg-surface">
            <div className="sticky top-0 flex items-center justify-between border-b border-border bg-surface px-6 py-4">
              <h2 className="text-xl font-semibold text-text">Edit pod settings</h2>
              <button onClick={() => setShowEditModal(false)} className="text-text-secondary hover:text-text">
                <XIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-6 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-text-secondary">Public access</label>
                  <p className="text-xs text-text-muted">Allow all members to view and connect via CLI</p>
                </div>
                <button
                  onClick={() => setEditForm({ ...editForm, is_public: !editForm.is_public })}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    editForm.is_public ? 'bg-accent' : 'bg-surface-hover'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      editForm.is_public ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {!editForm.is_public && (
                <div>
                  <label className="mb-3 block text-sm font-medium text-text-secondary">Allowed users</label>
                  <p className="mb-3 text-xs text-text-muted">Select which members can access this pod via CLI</p>

                  {loadingMembers ? (
                    <div className="py-4 text-center">
                      <div className="mx-auto h-8 w-8 animate-spin rounded-full border-b-2 border-accent" />
                    </div>
                  ) : (
                    <div className="max-h-64 overflow-y-auto rounded-lg border border-border">
                      {discordMembers.map((member) => (
                        <div
                          key={member.discord_id}
                          className="flex items-center justify-between border-b border-border p-3 last:border-b-0 hover:bg-surface-hover"
                        >
                          <div className="flex items-center gap-3">
                            {member.avatar ? (
                              <Image
                                src={`https://cdn.discordapp.com/avatars/${member.discord_id}/${member.avatar}.png`}
                                alt={member.display_name}
                                width={32}
                                height={32}
                                className="rounded-full"
                              />
                            ) : (
                              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-hover text-sm font-bold text-text">
                                {member.display_name.charAt(0).toUpperCase()}
                              </div>
                            )}
                            <div>
                              <p className="text-sm font-medium text-text">{member.display_name}</p>
                              <p className="text-xs text-text-muted">@{member.username}</p>
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            checked={editForm.allowed_users.includes(member.discord_id)}
                            onChange={() => toggleUserSelection(member.discord_id)}
                            className="h-4 w-4 rounded border-border-strong bg-bg-elevated text-accent focus:ring-accent"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="secondary" onClick={() => setShowEditModal(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveEdit} loading={editLoading}>
                  {!editLoading && <SaveIcon className="h-4 w-4" />}
                  Save changes
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      <Toaster />
    </div>
  );
}
