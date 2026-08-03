'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import Image from 'next/image';
import toast, { Toaster } from 'react-hot-toast';
import { Rocket, Plus, X } from 'lucide-react';
import Navbar from '@/components/Navbar';
import { LoadingScreen } from '@/components/Skeleton';
import { Card, CardHeader, CardTitle, CardBody } from '@/components/Card';
import { Input, Select, Textarea, FieldLabel, FieldHint } from '@/components/Input';
import Button from '@/components/Button';
import { verifyDiscordUser } from '@/features/auth/api';
import { createPod, fetchDiscordMembers } from '../api';
import type { DiscordMember, PodConfig } from '../types';

const defaultConfig: PodConfig = {
  name: '',
  image_name: 'theaisocietyasu/godfather-base:latest',
  gpu_type_id: 'NVIDIA RTX A4000',
  instance_ids: ['cpu3c-2-4'],
  use_cpu_only: false,
  cloud_type: 'COMMUNITY',
  support_public_ip: false,
  start_jupyter: false,
  start_ssh: true,
  volume_in_gb: 1,
  container_disk_in_gb: 2,
  min_vcpu_count: 1,
  min_memory_in_gb: 2,
  docker_args: '',
  ports: '22/tcp',
  volume_mount_path: '/workspace',
  is_public: false,
  allowed_users: [],
  env: {},
};

export default function CreatePodForm() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [config, setConfig] = useState<PodConfig>(defaultConfig);
  const [submitting, setSubmitting] = useState(false);
  const [envKey, setEnvKey] = useState('');
  const [envValue, setEnvValue] = useState('');
  const [discordMembers, setDiscordMembers] = useState<DiscordMember[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(true);
  const [verifyingAuth, setVerifyingAuth] = useState(true);

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

  useEffect(() => {
    if (verifyingAuth || !session?.user?.discordId) return;

    const loadMembers = async () => {
      try {
        const members = await fetchDiscordMembers(session.user.discordId);
        setDiscordMembers(members);
      } catch (error) {
        console.error('Error fetching Discord members:', error);
        toast.error('Could not load Discord members');
      } finally {
        setLoadingMembers(false);
      }
    };

    loadMembers();
  }, [session, verifyingAuth]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config.name.trim()) {
      toast.error('Pod name is required');
      return;
    }
    if (!session?.user?.discordId) return;

    setSubmitting(true);
    try {
      await createPod(config, session.user.discordId);
      toast.success('Pod created');
      router.push('/dashboard');
    } catch (error) {
      console.error('Error creating pod:', error);
      toast.error('Failed to create pod');
    } finally {
      setSubmitting(false);
    }
  };

  const addEnvVar = () => {
    if (envKey && envValue) {
      setConfig({ ...config, env: { ...config.env, [envKey]: envValue } });
      setEnvKey('');
      setEnvValue('');
    }
  };

  const removeEnvVar = (key: string) => {
    const newEnv = { ...config.env };
    delete newEnv[key];
    setConfig({ ...config, env: newEnv });
  };

  const toggleAllowedUser = (userId: string, checked: boolean) => {
    setConfig({
      ...config,
      allowed_users: checked
        ? [...config.allowed_users, userId]
        : config.allowed_users.filter((id) => id !== userId),
    });
  };

  if (verifyingAuth || loadingMembers) {
    return <LoadingScreen label={verifyingAuth ? 'Verifying access' : 'Loading'} />;
  }

  return (
    <div className="min-h-screen bg-bg">
      <Navbar />

      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-text">Launch a pod</h1>
          <p className="mt-1 text-sm text-text-muted">Configure and provision a new RunPod GPU environment.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic configuration</CardTitle>
            </CardHeader>
            <CardBody className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <FieldLabel htmlFor="name">Pod name *</FieldLabel>
                <Input
                  id="name"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                  placeholder="my-pod"
                  required
                />
              </div>

              <div>
                <FieldLabel htmlFor="image">Docker image</FieldLabel>
                <Select
                  id="image"
                  value={config.image_name}
                  onChange={(e) => setConfig({ ...config, image_name: e.target.value })}
                >
                  <option value="theaisocietyasu/godfather-base:latest">Godfather Base (recommended)</option>
                  <option value="runpod/base:0.4.0-cuda11.8.0">Base CUDA 11.8 (cheapest)</option>
                  <option value="nvidia/cuda:11.8-devel-ubuntu20.04">NVIDIA CUDA 11.8</option>
                  <option value="runpod/pytorch:3.10-2.0.0-117">PyTorch 2.0.0 (Python 3.10)</option>
                  <option value="runpod/tensorflow:2.11.0-py3.10-cuda11.8.0-devel-ubuntu22.04">TensorFlow 2.11.0</option>
                </Select>
                <FieldHint>Godfather Base sets up SSH and per-user isolation automatically.</FieldHint>
              </div>

              <div>
                <FieldLabel htmlFor="compute">Compute type</FieldLabel>
                <Select
                  id="compute"
                  value={config.use_cpu_only ? 'cpu' : 'gpu'}
                  onChange={(e) => setConfig({ ...config, use_cpu_only: e.target.value === 'cpu' })}
                >
                  <option value="cpu">CPU only (cheapest)</option>
                  <option value="gpu">GPU</option>
                </Select>
              </div>

              {config.use_cpu_only ? (
                <div>
                  <FieldLabel htmlFor="cpu-instance">CPU instance type</FieldLabel>
                  <Select
                    id="cpu-instance"
                    value={config.instance_ids?.[0] || 'cpu3c-2-4'}
                    onChange={(e) => setConfig({ ...config, instance_ids: [e.target.value] })}
                  >
                    <option value="cpu3c-2-4">3 vCPU, 2 GB RAM (minimal)</option>
                    <option value="cpu4c-4-8">4 vCPU, 4 GB RAM</option>
                    <option value="cpu8c-8-16">8 vCPU, 8 GB RAM</option>
                    <option value="cpu16c-16-32">16 vCPU, 16 GB RAM</option>
                  </Select>
                  <FieldHint>CPU-only pods cost less and work well for development.</FieldHint>
                </div>
              ) : (
                <div>
                  <FieldLabel htmlFor="gpu-type">GPU type</FieldLabel>
                  <Select
                    id="gpu-type"
                    value={config.gpu_type_id}
                    onChange={(e) => setConfig({ ...config, gpu_type_id: e.target.value })}
                  >
                    <option value="NVIDIA RTX A4000">NVIDIA RTX A4000 (minimal)</option>
                    <option value="NVIDIA RTX A5000">NVIDIA RTX A5000</option>
                  </Select>
                  <FieldHint>Start with the minimal option and upgrade later if you need more power.</FieldHint>
                </div>
              )}

              <div>
                <FieldLabel htmlFor="cloud-type">Cloud type</FieldLabel>
                <Select
                  id="cloud-type"
                  value={config.cloud_type}
                  onChange={(e) => setConfig({ ...config, cloud_type: e.target.value })}
                >
                  <option value="COMMUNITY">Community cloud (cheapest)</option>
                  <option value="ALL">All regions</option>
                  <option value="SECURE">Secure cloud (more expensive)</option>
                </Select>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resources</CardTitle>
            </CardHeader>
            <CardBody className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <FieldLabel htmlFor="volume">Volume size (GB)</FieldLabel>
                <Input
                  id="volume"
                  type="number"
                  min={1}
                  max={1000}
                  value={config.volume_in_gb}
                  onChange={(e) => setConfig({ ...config, volume_in_gb: parseInt(e.target.value) || 1 })}
                />
                <FieldHint>Persistent storage (min 1 GB).</FieldHint>
              </div>

              <div>
                <FieldLabel htmlFor="container-disk">Container disk (GB)</FieldLabel>
                <Input
                  id="container-disk"
                  type="number"
                  min={2}
                  max={1000}
                  value={config.container_disk_in_gb}
                  onChange={(e) => setConfig({ ...config, container_disk_in_gb: parseInt(e.target.value) || 2 })}
                />
                <FieldHint>Temporary disk space (min 2 GB).</FieldHint>
              </div>

              <div>
                <FieldLabel htmlFor="vcpu">Min vCPU count</FieldLabel>
                <Input
                  id="vcpu"
                  type="number"
                  min={1}
                  max={64}
                  value={config.min_vcpu_count}
                  onChange={(e) => setConfig({ ...config, min_vcpu_count: parseInt(e.target.value) || 1 })}
                />
              </div>

              <div>
                <FieldLabel htmlFor="memory">Min memory (GB)</FieldLabel>
                <Input
                  id="memory"
                  type="number"
                  min={2}
                  max={512}
                  value={config.min_memory_in_gb}
                  onChange={(e) => setConfig({ ...config, min_memory_in_gb: parseInt(e.target.value) || 2 })}
                />
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Network & services</CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {[
                  { key: 'support_public_ip' as const, label: 'Public IP', hint: 'Adds cost' },
                  { key: 'start_jupyter' as const, label: 'Jupyter notebook', hint: 'Web-based IDE' },
                  { key: 'start_ssh' as const, label: 'SSH access', hint: 'Recommended' },
                ].map(({ key, label, hint }) => (
                  <label
                    key={key}
                    className="flex items-center gap-2 rounded-lg border border-border p-3 hover:bg-surface-hover cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={config[key]}
                      onChange={(e) => setConfig({ ...config, [key]: e.target.checked })}
                      className="rounded border-border-strong bg-bg-elevated text-accent focus:ring-accent"
                    />
                    <div>
                      <span className="block text-sm font-medium text-text">{label}</span>
                      <span className="text-xs text-text-muted">{hint}</span>
                    </div>
                  </label>
                ))}
              </div>

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <FieldLabel htmlFor="ports">Ports</FieldLabel>
                  <Input
                    id="ports"
                    value={config.ports}
                    onChange={(e) => setConfig({ ...config, ports: e.target.value })}
                    placeholder="8888/http,22/tcp"
                  />
                </div>

                <div>
                  <FieldLabel htmlFor="mount-path">Volume mount path</FieldLabel>
                  <Input
                    id="mount-path"
                    value={config.volume_mount_path}
                    onChange={(e) => setConfig({ ...config, volume_mount_path: e.target.value })}
                    placeholder="/workspace"
                  />
                </div>
              </div>

              <div>
                <FieldLabel htmlFor="docker-args">Docker arguments</FieldLabel>
                <Textarea
                  id="docker-args"
                  rows={3}
                  value={config.docker_args}
                  onChange={(e) => setConfig({ ...config, docker_args: e.target.value })}
                  placeholder="Additional docker arguments"
                />
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Access control</CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.is_public}
                  onChange={(e) => setConfig({ ...config, is_public: e.target.checked })}
                  className="rounded border-border-strong bg-bg-elevated text-accent focus:ring-accent"
                />
                <span className="text-sm text-text-secondary">
                  Make this pod public (accessible to all Discord members)
                </span>
              </label>

              {config.is_public ? (
                <div className="rounded-lg border border-info/30 bg-info-soft p-3 text-sm text-text-secondary">
                  Any authenticated Discord member can connect to this pod via CLI. Each user gets an isolated
                  workspace folder.
                </div>
              ) : (
                <div>
                  <FieldLabel>Allowed Discord users</FieldLabel>
                  <div className="max-h-64 overflow-y-auto rounded-lg border border-border bg-bg-elevated">
                    {discordMembers.length === 0 ? (
                      <div className="p-4 text-sm text-text-muted">No Discord members found</div>
                    ) : (
                      <div className="divide-y divide-border">
                        {discordMembers.map((member) => (
                          <label
                            key={member.discord_id}
                            className="flex items-center p-3 hover:bg-surface-hover cursor-pointer"
                          >
                            <input
                              type="checkbox"
                              checked={config.allowed_users.includes(member.discord_id)}
                              onChange={(e) => toggleAllowedUser(member.discord_id, e.target.checked)}
                              className="rounded border-border-strong bg-surface text-accent focus:ring-accent"
                            />
                            <div className="ml-3 flex items-center">
                              {member.avatar && (
                                <Image
                                  src={`https://cdn.discordapp.com/avatars/${member.discord_id}/${member.avatar}.png?size=32`}
                                  alt={member.display_name}
                                  width={32}
                                  height={32}
                                  className="mr-2 rounded-full"
                                />
                              )}
                              <div>
                                <div className="text-sm font-medium text-text">{member.display_name}</div>
                                <div className="text-xs text-text-muted">@{member.username}</div>
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                  {config.allowed_users.length > 0 && (
                    <p className="mt-2 text-sm text-text-muted">
                      {config.allowed_users.length} user{config.allowed_users.length !== 1 ? 's' : ''} selected
                    </p>
                  )}
                  <div className="mt-2 rounded-lg border border-info/30 bg-info-soft p-3 text-sm text-text-secondary">
                    Only selected users can see and connect to this pod via CLI, each with an isolated workspace
                    folder.
                  </div>
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Environment variables</CardTitle>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={envKey}
                  onChange={(e) => setEnvKey(e.target.value)}
                  placeholder="Variable name"
                  className="flex-1"
                />
                <Input
                  value={envValue}
                  onChange={(e) => setEnvValue(e.target.value)}
                  placeholder="Variable value"
                  className="flex-1"
                />
                <Button type="button" variant="secondary" onClick={addEnvVar}>
                  <Plus className="h-4 w-4" />
                  Add
                </Button>
              </div>

              {Object.entries(config.env).length > 0 && (
                <div className="space-y-2">
                  {Object.entries(config.env).map(([key, value]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between rounded-lg border border-border bg-bg-elevated p-3"
                    >
                      <span className="text-sm text-text">
                        <strong>{key}</strong> = {value}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeEnvVar(key)}
                        className="rounded p-1 text-danger hover:bg-danger-soft"
                        title="Remove"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => router.back()}>
              Cancel
            </Button>
            <Button type="submit" loading={submitting}>
              {!submitting && <Rocket className="h-4 w-4" />}
              {submitting ? 'Provisioning...' : 'Create pod'}
            </Button>
          </div>
        </form>
      </main>

      <Toaster />
    </div>
  );
}
