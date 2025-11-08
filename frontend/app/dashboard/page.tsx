'use client';

import { useSession } from 'next-auth/react';
import { signOut } from '@/lib/auth-client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import toast, { Toaster } from 'react-hot-toast';
import { 
  Server as ServerIcon, 
  Plus as PlusIcon, 
  Play as PlayIcon, 
  Square as StopIcon, 
  RotateCw as RestartIcon,
  Trash2 as TrashIcon,
  Eye as EyeIcon,
  Terminal as TerminalIcon,
  LogOut as LogOutIcon
} from 'lucide-react';
import moment from 'moment';

interface Pod {
  id: string;
  name: string;
  status: string;
  machine_type: string;
  created_at: string;
  runtime?: {
    uptimeInSeconds?: number;
    ports?: string;
    gpus?: string;
  };
  is_public: boolean;
  allowed_users: string[];
  custom_config: {
    storageAmount?: number;
    containerDiskSize?: number;
  };
}

export default function Dashboard() {
  const { data: session, status } = useSession();
  const [pods, setPods] = useState<Pod[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const router = useRouter();

  const fetchPods = useCallback(async () => {
    try {
      const response = await fetch('/api/pods', {
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch pods');
      }
      
      const data = await response.json();
      setPods(data.pods);
    } catch (error: unknown) {
      console.error('Error fetching pods:', error);
      toast.error('Failed to fetch pods');
    } finally {
      setLoading(false);
    }
  }, [session]);

  const verifyAndFetchPods = useCallback(async () => {
    if (!session?.user?.discordId) {
      router.push('/');
      return;
    }

    try {
      // First verify authentication
      const verifyResponse = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          discord_user_id: session.user.discordId 
        }),
      });

      if (!verifyResponse.ok) {
        throw new Error('Authentication failed');
      }

      // Then fetch pods
      await fetchPods();
    } catch (error: unknown) {
      console.error('Error during verification:', error);
      toast.error('Authentication failed. Redirecting to home...');
      router.push('/');
    }
  }, [session, fetchPods, router]);

  useEffect(() => {
    if (status === 'loading') return;
    
    if (!session) {
      router.push('/');
      return;
    }
    
    // Verify auth first, then fetch pods
    verifyAndFetchPods();
  }, [session, status, router, verifyAndFetchPods]);

  const handlePodAction = async (podId: string, action: string) => {
    setActionLoading(podId);
    try {
      const response = await fetch(`/api/pods/${podId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Discord-User-ID': session?.user?.discordId || '',
        },
        body: JSON.stringify({ action }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to ${action} pod`);
      }
      
      toast.success(`Pod ${action} successful`);
      fetchPods(); // Refresh the list
    } catch (error: unknown) {
      console.error(`Error ${action} pod:`, error);
      toast.error(`Failed to ${action} pod`);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'running': return 'bg-green-100 text-green-800';
      case 'stopped': return 'bg-red-100 text-red-800';
      case 'starting': return 'bg-yellow-100 text-yellow-800';
      case 'stopping': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">AI Society Admin Portal</h1>
              <span className="text-sm text-gray-500">RunPod Management</span>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/cli-auth')}
                className="text-gray-600 hover:text-gray-900 px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
              >
                <TerminalIcon className="w-4 h-4" />
                <span>CLI Token</span>
              </button>
              <button
                onClick={() => router.push('/dashboard/create-pod')}
                className="bg-black text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-800 transition-colors flex items-center space-x-2"
              >
                <PlusIcon className="w-4 h-4" />
                <span>Create Pod</span>
              </button>
              <button
                onClick={() => signOut({ callbackUrl: '/' })}
                className="text-gray-600 hover:text-gray-900 px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
              >
                <LogOutIcon className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ServerIcon className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Pods</p>
                <p className="text-2xl font-semibold text-gray-900">{pods.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <PlayIcon className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Running</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {pods.filter(p => p.status?.toLowerCase() === 'running').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <StopIcon className="h-8 w-8 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Stopped</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {pods.filter(p => p.status?.toLowerCase() === 'stopped').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <EyeIcon className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Public</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {pods.filter(p => p.is_public).length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Pods Table */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">RunPod Instances</h2>
          </div>
          
          {pods.length === 0 ? (
            <div className="text-center py-12">
              <ServerIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No pods</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating a new pod.</p>
              <div className="mt-6">
                <button
                  onClick={() => router.push('/dashboard/create-pod')}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-black hover:bg-gray-800"
                >
                  <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
                  Create Pod
                </button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Visibility
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {pods.map((pod) => (
                    <tr key={pod.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{pod.name}</div>
                        <div className="text-sm text-gray-500">{pod.id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(pod.status)}`}>
                          {pod.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {pod.machine_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          pod.is_public ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {pod.is_public ? 'Public' : 'Private'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {moment(pod.created_at).fromNow()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => router.push(`/dashboard/pods/${pod.id}`)}
                            className="text-blue-600 hover:text-blue-900 p-1 rounded"
                            title="View Details"
                          >
                            <EyeIcon className="w-4 h-4" />
                          </button>
                          
                          {pod.status?.toLowerCase() === 'stopped' && (
                            <button
                              onClick={() => handlePodAction(pod.id, 'start')}
                              disabled={actionLoading === pod.id}
                              className="text-green-600 hover:text-green-900 p-1 rounded disabled:opacity-50"
                              title="Start Pod"
                            >
                              <PlayIcon className="w-4 h-4" />
                            </button>
                          )}
                          
                          {pod.status?.toLowerCase() === 'running' && (
                            <>
                              <button
                                onClick={() => handlePodAction(pod.id, 'restart')}
                                disabled={actionLoading === pod.id || pod.name.toLowerCase() === 'godfather'}
                                className="text-yellow-600 hover:text-yellow-900 p-1 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                title={pod.name.toLowerCase() === 'godfather' ? 'Protected pod - cannot restart' : 'Restart Pod'}
                              >
                                <RestartIcon className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handlePodAction(pod.id, 'stop')}
                                disabled={actionLoading === pod.id || pod.name.toLowerCase() === 'godfather'}
                                className="text-orange-600 hover:text-orange-900 p-1 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                title={pod.name.toLowerCase() === 'godfather' ? 'Protected pod - cannot stop' : 'Stop Pod'}
                              >
                                <StopIcon className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          
                          <button
                            onClick={() => handlePodAction(pod.id, 'terminate')}
                            disabled={actionLoading === pod.id || pod.name.toLowerCase() === 'godfather'}
                            className="text-red-600 hover:text-red-900 p-1 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                            title={pod.name.toLowerCase() === 'godfather' ? 'Protected pod - cannot terminate' : 'Terminate Pod'}
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
      
      <Toaster />
    </div>
  );
}