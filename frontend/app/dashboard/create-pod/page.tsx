'use client';

import { useAuth, UserButton } from '@clerk/nextjs';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import { ArrowLeftIcon } from 'lucide-react';

interface PodConfig {
  name: string;
  image_name: string;
  gpu_type_id: string;
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
  image_name: 'runpod/pytorch:3.10-2.0.0-117',
  gpu_type_id: 'NVIDIA RTX A4000',
  cloud_type: 'ALL',
  support_public_ip: true,
  start_jupyter: true,
  start_ssh: true,
  volume_in_gb: 20,
  container_disk_in_gb: 20,
  min_vcpu_count: 2,
  min_memory_in_gb: 8,
  docker_args: '',
  ports: '8888/http,22/tcp',
  volume_mount_path: '/workspace',
  is_public: false,
  allowed_users: [],
  env: {}
};

export default function CreatePod() {
  const { getToken } = useAuth();
  const [config, setConfig] = useState<PodConfig>(defaultConfig);
  const [loading, setLoading] = useState(false);
  const [envKey, setEnvKey] = useState('');
  const [envValue, setEnvValue] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!config.name.trim()) {
      toast.error('Pod name is required');
      return;
    }

    setLoading(true);
    try {
      const token = await getToken();
      await axios.post('/api/pods', config, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Pod created successfully!');
      router.push('/dashboard');
    } catch (error: unknown) {
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.back()}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeftIcon className="w-5 h-5" />
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Create New Pod</h1>
            </div>
            <UserButton />
          </div>
        </div>
      </header>

      {/* Form */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-6">Basic Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Pod Name *
                </label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  placeholder="my-awesome-pod"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Docker Image
                </label>
                <select
                  value={config.image_name}
                  onChange={(e) => setConfig({ ...config, image_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                >
                  <option value="runpod/pytorch:3.10-2.0.0-117">PyTorch 2.0.0 (Python 3.10)</option>
                  <option value="runpod/tensorflow:2.11.0-py3.10-cuda11.8.0-devel-ubuntu22.04">TensorFlow 2.11.0</option>
                  <option value="runpod/base:0.4.0-cuda11.8.0">Base CUDA 11.8</option>
                  <option value="nvidia/cuda:11.8-devel-ubuntu20.04">NVIDIA CUDA 11.8</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  GPU Type
                </label>
                <select
                  value={config.gpu_type_id}
                  onChange={(e) => setConfig({ ...config, gpu_type_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                >
                  <option value="NVIDIA RTX A4000">NVIDIA RTX A4000</option>
                  <option value="NVIDIA RTX A5000">NVIDIA RTX A5000</option>
                  <option value="NVIDIA RTX A6000">NVIDIA RTX A6000</option>
                  <option value="NVIDIA A100 PCIe">NVIDIA A100 PCIe</option>
                  <option value="NVIDIA A100 SXM4">NVIDIA A100 SXM4</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cloud Type
                </label>
                <select
                  value={config.cloud_type}
                  onChange={(e) => setConfig({ ...config, cloud_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                >
                  <option value="ALL">All Regions</option>
                  <option value="SECURE">Secure Cloud</option>
                  <option value="COMMUNITY">Community Cloud</option>
                </select>
              </div>
            </div>
          </div>

          {/* Resource Configuration */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-6">Resource Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Volume Size (GB)
                </label>
                <input
                  type="number"
                  value={config.volume_in_gb}
                  onChange={(e) => setConfig({ ...config, volume_in_gb: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Container Disk (GB)
                </label>
                <input
                  type="number"
                  value={config.container_disk_in_gb}
                  onChange={(e) => setConfig({ ...config, container_disk_in_gb: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min vCPU Count
                </label>
                <input
                  type="number"
                  value={config.min_vcpu_count}
                  onChange={(e) => setConfig({ ...config, min_vcpu_count: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min Memory (GB)
                </label>
                <input
                  type="number"
                  value={config.min_memory_in_gb}
                  onChange={(e) => setConfig({ ...config, min_memory_in_gb: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  min="1"
                />
              </div>
            </div>
          </div>

          {/* Network & Services */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-6">Network & Services</h2>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.support_public_ip}
                    onChange={(e) => setConfig({ ...config, support_public_ip: e.target.checked })}
                    className="rounded border-gray-300 text-black focus:ring-black"
                  />
                  <span className="ml-2 text-sm text-gray-700">Support Public IP</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.start_jupyter}
                    onChange={(e) => setConfig({ ...config, start_jupyter: e.target.checked })}
                    className="rounded border-gray-300 text-black focus:ring-black"
                  />
                  <span className="ml-2 text-sm text-gray-700">Start Jupyter</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.start_ssh}
                    onChange={(e) => setConfig({ ...config, start_ssh: e.target.checked })}
                    className="rounded border-gray-300 text-black focus:ring-black"
                  />
                  <span className="ml-2 text-sm text-gray-700">Start SSH</span>
                </label>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ports
                  </label>
                  <input
                    type="text"
                    value={config.ports}
                    onChange={(e) => setConfig({ ...config, ports: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                    placeholder="8888/http,22/tcp"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Volume Mount Path
                  </label>
                  <input
                    type="text"
                    value={config.volume_mount_path}
                    onChange={(e) => setConfig({ ...config, volume_mount_path: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                    placeholder="/workspace"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Docker Arguments
                </label>
                <textarea
                  value={config.docker_args}
                  onChange={(e) => setConfig({ ...config, docker_args: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  rows={3}
                  placeholder="Additional docker arguments..."
                />
              </div>
            </div>
          </div>

          {/* Access Control */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-6">Access Control</h2>
            
            <div className="space-y-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.is_public}
                  onChange={(e) => setConfig({ ...config, is_public: e.target.checked })}
                  className="rounded border-gray-300 text-black focus:ring-black"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Make this pod public (accessible via CLI)
                </span>
              </label>
              
              {config.is_public && (
                <div className="ml-6 text-sm text-gray-600 bg-blue-50 p-3 rounded-md">
                  When public, users with valid Discord authentication can connect to this pod via CLI.
                  Each user will get their own isolated folder.
                </div>
              )}
            </div>
          </div>

          {/* Environment Variables */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-6">Environment Variables</h2>
            
            <div className="space-y-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={envKey}
                  onChange={(e) => setEnvKey(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  placeholder="Variable name"
                />
                <input
                  type="text"
                  value={envValue}
                  onChange={(e) => setEnvValue(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  placeholder="Variable value"
                />
                <button
                  type="button"
                  onClick={addEnvVar}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Add
                </button>
              </div>

              {Object.entries(config.env).length > 0 && (
                <div className="space-y-2">
                  {Object.entries(config.env).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                      <span className="text-sm">
                        <strong>{key}</strong> = {value}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeEnvVar(key)}
                        className="text-red-600 hover:text-red-800 text-sm"
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
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-black text-white rounded-md hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
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