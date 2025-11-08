'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import Image from 'next/image';
import toast, { Toaster } from 'react-hot-toast';
import Navbar from '@/components/Navbar';

interface DiscordMember {
  discord_id: string;
  username: string;
  global_name?: string;
  nickname?: string;
  avatar?: string;
  display_name: string;
}

interface PodConfig {
  name: string;
  image_name: string;
  gpu_type_id: string;
  instance_id?: string;
  use_cpu_only: boolean;
  cloud_type: string;
  support_public_ip: boolean;
  start_jupyter: boolean;
  start_ssh: boolean;
  volume_in_gb: number;
  container_disk_in_gb: number;
  min_vcpu_count: number;
  min_memory_in_gb: number;
  docker_args: string;
  ports: string;
  volume_mount_path: string;
  is_public: boolean;
  allowed_users: string[];
  env: Record<string, string>;
}

const defaultConfig: PodConfig = {
  name: '',
  image_name: 'theaisocietyasu/godfather-base:latest',  // Default to Godfather custom image
  gpu_type_id: 'NVIDIA RTX A4000',
  instance_id: 'cpu3c-2-4',  // Default CPU instance
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
  env: {}
};

export default function CreatePod() {
  const { data: session, status } = useSession();
  const [config, setConfig] = useState<PodConfig>(defaultConfig);
  const [loading, setLoading] = useState(false);
  const [envKey, setEnvKey] = useState('');
  const [envValue, setEnvValue] = useState('');
  const [discordMembers, setDiscordMembers] = useState<DiscordMember[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(true);
  const [verifyingAuth, setVerifyingAuth] = useState(true);
  const router = useRouter();

  // Verify admin access on mount
  useEffect(() => {
    const verifyAdmin = async () => {
      if (status === 'loading') return;
      
      if (!session?.user?.discordId) {
        router.push('/');
        return;
      }

      try {
        const response = await fetch('/api/auth/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ discord_user_id: session.user.discordId })
        });

        if (!response.ok) {
          throw new Error('Authentication failed');
        }

        const data = await response.json();
        
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
    };

    verifyAdmin();
  }, [session, status, router]);

  // Fetch Discord members on component mount
  useEffect(() => {
    if (verifyingAuth) return;

    const fetchDiscordMembers = async () => {
      try {
        const response = await fetch('/api/discord/members', {
          headers: {
            'X-Discord-User-ID': session?.user?.discordId || '',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setDiscordMembers(data.members || []);
        } else {
          console.error('Failed to fetch Discord members');
          toast.error('Could not load Discord members');
        }
      } catch (error) {
        console.error('Error fetching Discord members:', error);
        toast.error('Error loading Discord members');
      } finally {
        setLoadingMembers(false);
      }
    };

    fetchDiscordMembers();
  }, [session, verifyingAuth]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config.name.trim()) {
      toast.error('Pod name is required');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/pods', {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create pod');
      }
      
      toast.success('Pod created successfully!');
      router.push('/dashboard');
    } catch (error: unknown) {
      console.error('Error creating pod:', error);
      toast.error('Failed to create pod');
    } finally {
      setLoading(false);
    }
  };

  const addEnvVar = () => {
    if (envKey && envValue) {
      setConfig({
        ...config,
        env: { ...config.env, [envKey]: envValue }
      });
      setEnvKey('');
      setEnvValue('');
    }
  };

  const removeEnvVar = (key: string) => {
    const newEnv = { ...config.env };
    delete newEnv[key];
    setConfig({ ...config, env: newEnv });
  };

  if (verifyingAuth || loadingMembers) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-purple-500/30"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin"></div>
          </div>
          <p className="text-gray-300">
            {verifyingAuth ? 'Verifying access...' : 'Loading...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />

      {/* Form */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="bg-gray-800 shadow rounded-lg p-6 border border-gray-700">
            <h2 className="text-lg font-medium text-white mb-6">Basic Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Pod Name *
                </label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="my-awesome-pod"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Docker Image
                </label>
                <select
                  value={config.image_name}
                  onChange={(e) => setConfig({ ...config, image_name: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="theaisocietyasu/godfather-base:latest">Godfather Base (Recommended) ⭐</option>
                  <option value="runpod/base:0.4.0-cuda11.8.0">Base CUDA 11.8 (Cheapest)</option>
                  <option value="nvidia/cuda:11.8-devel-ubuntu20.04">NVIDIA CUDA 11.8</option>
                  <option value="runpod/pytorch:3.10-2.0.0-117">PyTorch 2.0.0 (Python 3.10)</option>
                  <option value="runpod/tensorflow:2.11.0-py3.10-cuda11.8.0-devel-ubuntu22.04">TensorFlow 2.11.0</option>
                </select>
                <p className="mt-1 text-sm text-gray-400">
                  ⚠️ Use &quot;Godfather Base&quot; for automatic SSH setup and user isolation
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Compute Type
                </label>
                <select
                  value={config.use_cpu_only ? 'cpu' : 'gpu'}
                  onChange={(e) => setConfig({ ...config, use_cpu_only: e.target.value === 'cpu' })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="cpu">CPU Only (Cheapest) 💰</option>
                  <option value="gpu">GPU</option>
                </select>
              </div>

              {config.use_cpu_only ? (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    CPU Instance Type
                  </label>
                  <select
                    value={config.instance_id}
                    onChange={(e) => setConfig({ ...config, instance_id: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="cpu3c-2-4">3 vCPU, 2 GB RAM (Minimal) 💰</option>
                    <option value="cpu4c-4-8">4 vCPU, 4 GB RAM</option>
                    <option value="cpu8c-8-16">8 vCPU, 8 GB RAM</option>
                    <option value="cpu16c-16-32">16 vCPU, 16 GB RAM</option>
                  </select>
                  <p className="mt-2 text-xs text-blue-400">
                    💡 CPU-only pods are much cheaper. Great for development and testing!
                  </p>
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    GPU Type
                  </label>
                  <select
                    value={config.gpu_type_id}
                    onChange={(e) => setConfig({ ...config, gpu_type_id: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="NVIDIA RTX A4000">NVIDIA RTX A4000 (Minimal) 💰</option>
                    <option value="NVIDIA RTX A5000">NVIDIA RTX A5000 (Normal)</option>
                  </select>
                  <p className="mt-2 text-xs text-blue-400">
                    💡 Starting with minimal GPU option. Upgrade if you need more power.
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Cloud Type
                </label>
                <select
                  value={config.cloud_type}
                  onChange={(e) => setConfig({ ...config, cloud_type: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="COMMUNITY">Community Cloud (Cheapest) 💰</option>
                  <option value="ALL">All Regions</option>
                  <option value="SECURE">Secure Cloud (More Expensive)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Resource Configuration */}
          <div className="bg-gray-800 shadow rounded-lg p-6 border border-gray-700">
            <h2 className="text-lg font-medium text-white mb-4">Resource Configuration</h2>
            <div className="mb-4 p-3 bg-blue-900/30 border border-blue-700 rounded-md">
              <p className="text-sm text-blue-300">
                💡 <strong>Tip:</strong> Start with minimal resources to save costs. You can always upgrade later if needed.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Volume Size (GB)
                </label>
                <input
                  type="number"
                  value={config.volume_in_gb}
                  onChange={(e) => setConfig({ ...config, volume_in_gb: parseInt(e.target.value) || 1 })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  min="1"
                  max="1000"
                />
                <p className="mt-1 text-xs text-gray-400">Persistent storage (min: 1 GB)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Container Disk (GB)
                </label>
                <input
                  type="number"
                  value={config.container_disk_in_gb}
                  onChange={(e) => setConfig({ ...config, container_disk_in_gb: parseInt(e.target.value) || 2 })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  min="2"
                  max="1000"
                />
                <p className="mt-1 text-xs text-gray-400">Temporary disk space (min: 2 GB)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Min vCPU Count
                </label>
                <input
                  type="number"
                  value={config.min_vcpu_count}
                  onChange={(e) => setConfig({ ...config, min_vcpu_count: parseInt(e.target.value) || 1 })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  min="1"
                  max="64"
                />
                <p className="mt-1 text-xs text-gray-400">CPU cores (min: 1)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Min Memory (GB)
                </label>
                <input
                  type="number"
                  value={config.min_memory_in_gb}
                  onChange={(e) => setConfig({ ...config, min_memory_in_gb: parseInt(e.target.value) || 2 })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  min="2"
                  max="512"
                />
                <p className="mt-1 text-xs text-gray-400">RAM (min: 2 GB)</p>
              </div>
            </div>
          </div>

          {/* Network & Services */}
          <div className="bg-gray-800 shadow rounded-lg p-6 border border-gray-700">
            <h2 className="text-lg font-medium text-white mb-6">Network & Services</h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center space-x-2 p-3 border border-gray-700 rounded-md hover:bg-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.support_public_ip}
                    onChange={(e) => setConfig({ ...config, support_public_ip: e.target.checked })}
                    className="rounded border-gray-600 text-purple-500 focus:ring-purple-500 bg-gray-700"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-200">Public IP</span>
                    <p className="text-xs text-gray-400">Adds cost</p>
                  </div>
                </label>
                
                <label className="flex items-center space-x-2 p-3 border border-gray-700 rounded-md hover:bg-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.start_jupyter}
                    onChange={(e) => setConfig({ ...config, start_jupyter: e.target.checked })}
                    className="rounded border-gray-600 text-purple-500 focus:ring-purple-500 bg-gray-700"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-200">Jupyter Notebook</span>
                    <p className="text-xs text-gray-400">Web-based IDE</p>
                  </div>
                </label>
                
                <label className="flex items-center space-x-2 p-3 border border-gray-700 rounded-md hover:bg-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.start_ssh}
                    onChange={(e) => setConfig({ ...config, start_ssh: e.target.checked })}
                    className="rounded border-gray-600 text-purple-500 focus:ring-purple-500 bg-gray-700"
                  />
                  <div>
                    <span className="text-sm font-medium text-gray-200">SSH Access</span>
                    <p className="text-xs text-gray-400">Recommended ✓</p>
                  </div>
                </label>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Ports
                  </label>
                  <input
                    type="text"
                    value={config.ports}
                    onChange={(e) => setConfig({ ...config, ports: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="8888/http,22/tcp"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Volume Mount Path
                  </label>
                  <input
                    type="text"
                    value={config.volume_mount_path}
                    onChange={(e) => setConfig({ ...config, volume_mount_path: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="/workspace"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Docker Arguments
                </label>
                <textarea
                  value={config.docker_args}
                  onChange={(e) => setConfig({ ...config, docker_args: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  rows={3}
                  placeholder="Additional docker arguments..."
                />
              </div>
            </div>
          </div>

          {/* Access Control */}
          <div className="bg-gray-800 shadow rounded-lg p-6 border border-gray-700">
            <h2 className="text-lg font-medium text-white mb-6">Access Control</h2>
            
            <div className="space-y-4">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.is_public}
                  onChange={(e) => setConfig({ ...config, is_public: e.target.checked })}
                  className="rounded border-gray-600 text-purple-500 focus:ring-purple-500 bg-gray-700"
                />
                <span className="ml-2 text-sm text-gray-300">
                  Make this pod public (accessible to all Discord members)
                </span>
              </label>
              
              {config.is_public && (
                <div className="ml-6 text-sm text-gray-300 bg-blue-900/30 border border-blue-700 p-3 rounded-md">
                  When public, any Discord member with valid authentication can connect to this pod via CLI.
                  Each user will get their own isolated workspace folder.
                </div>
              )}

              {!config.is_public && (
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Allowed Discord Users
                  </label>
                  {loadingMembers ? (
                    <div className="text-sm text-gray-400">Loading Discord members...</div>
                  ) : (
                    <div className="border border-gray-700 rounded-md max-h-64 overflow-y-auto bg-gray-750">
                      {discordMembers.length === 0 ? (
                        <div className="p-4 text-sm text-gray-400">No Discord members found</div>
                      ) : (
                        <div className="divide-y divide-gray-700">
                          {discordMembers.map((member) => (
                            <label key={member.discord_id} className="flex items-center p-3 hover:bg-gray-700 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={config.allowed_users.includes(member.discord_id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setConfig({
                                      ...config,
                                      allowed_users: [...config.allowed_users, member.discord_id]
                                    });
                                  } else {
                                    setConfig({
                                      ...config,
                                      allowed_users: config.allowed_users.filter(id => id !== member.discord_id)
                                    });
                                  }
                                }}
                                className="rounded border-gray-600 text-purple-500 focus:ring-purple-500 bg-gray-700"
                              />
                              <div className="ml-3 flex items-center">
                                {member.avatar && (
                                  <Image
                                    src={`https://cdn.discordapp.com/avatars/${member.discord_id}/${member.avatar}.png?size=32`}
                                    alt={member.display_name}
                                    width={32}
                                    height={32}
                                    className="rounded-full mr-2"
                                  />
                                )}
                                <div>
                                  <div className="text-sm font-medium text-gray-200">
                                    {member.display_name}
                                  </div>
                                  <div className="text-xs text-gray-400">
                                    @{member.username}
                                  </div>
                                </div>
                              </div>
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {config.allowed_users.length > 0 && (
                    <div className="mt-2 text-sm text-gray-400">
                      {config.allowed_users.length} user{config.allowed_users.length !== 1 ? 's' : ''} selected
                    </div>
                  )}
                  <div className="mt-2 text-sm text-gray-300 bg-blue-900/30 border border-blue-700 p-3 rounded-md">
                    Only selected Discord users will be able to see and connect to this pod via CLI.
                    Each user will get their own isolated workspace folder.
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Environment Variables */}
          <div className="bg-gray-800 shadow rounded-lg p-6 border border-gray-700">
            <h2 className="text-lg font-medium text-white mb-6">Environment Variables</h2>
            
            <div className="space-y-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={envKey}
                  onChange={(e) => setEnvKey(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Variable name"
                />
                <input
                  type="text"
                  value={envValue}
                  onChange={(e) => setEnvValue(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Variable value"
                />
                <button
                  type="button"
                  onClick={addEnvVar}
                  className="px-4 py-2 bg-gray-700 text-gray-200 rounded-md hover:bg-gray-600 border border-gray-600"
                >
                  Add
                </button>
              </div>

              {Object.entries(config.env).length > 0 && (
                <div className="space-y-2">
                  {Object.entries(config.env).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between bg-gray-700 p-3 rounded-md border border-gray-600">
                      <span className="text-sm text-gray-200">
                        <strong>{key}</strong> = {value}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeEnvVar(key)}
                        className="text-red-400 hover:text-red-300 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Submit */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 border border-gray-600 text-gray-300 rounded-md hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-md hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Creating...</span>
                </>
              ) : (
                <span>Create Pod</span>
              )}
            </button>
          </div>
        </form>
      </main>

      <Toaster />
    </div>
  );
}