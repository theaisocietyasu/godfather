'use client';

import { useSession } from 'next-auth/react';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import toast, { Toaster } from 'react-hot-toast';
import Navbar from '@/components/Navbar';
import { 
  Server as ServerIcon, 
  Play as PlayIcon, 
  Square as StopIcon, 
  RotateCw as RestartIcon,
  Trash2 as TrashIcon,
  Eye as EyeIcon,
  Plus as PlusIcon
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

      const verifyData = await verifyResponse.json();
      
      // Check if user is admin
      if (!verifyData.is_admin) {
        toast.error('Admin access required. Redirecting...');
        router.push('/');
        return;
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
    <div className="min-h-screen bg-gray-900">
      {/* Navbar */}
      <Navbar />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-6 hover:border-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ServerIcon className="h-8 w-8 text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total Pods</p>
                <p className="text-2xl font-semibold text-white">{pods.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-6 hover:border-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <PlayIcon className="h-8 w-8 text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Running</p>
                <p className="text-2xl font-semibold text-white">
                  {pods.filter(p => p.status?.toLowerCase() === 'running').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-6 hover:border-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <StopIcon className="h-8 w-8 text-red-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Stopped</p>
                <p className="text-2xl font-semibold text-white">
                  {pods.filter(p => p.status?.toLowerCase() === 'stopped').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-6 hover:border-gray-600 transition-colors">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <EyeIcon className="h-8 w-8 text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Public</p>
                <p className="text-2xl font-semibold text-white">
                  {pods.filter(p => p.is_public).length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Pods Table */}
        <div className="bg-gray-800 border border-gray-700 shadow-lg rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h2 className="text-lg font-medium text-white">RunPod Instances</h2>
          </div>
          
          {pods.length === 0 ? (
            <div className="text-center py-12">
              <ServerIcon className="mx-auto h-12 w-12 text-gray-500" />
              <h3 className="mt-2 text-sm font-medium text-gray-300">No pods</h3>
              <p className="mt-1 text-sm text-gray-400">Get started by creating a new pod.</p>
              <div className="mt-6">
                <button
                  onClick={() => router.push('/dashboard/create-pod')}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                >
                  <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
                  Create Pod
                </button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Visibility
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {pods.map((pod) => (
                    <tr key={pod.id} className="hover:bg-gray-700 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">{pod.name}</div>
                        <div className="text-sm text-gray-400">{pod.id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(pod.status)}`}>
                          {pod.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {pod.machine_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          pod.is_public ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {pod.is_public ? 'Public' : 'Private'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        {moment(pod.created_at).fromNow()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => router.push(`/dashboard/pods/${pod.id}`)}
                            className="text-blue-400 hover:text-blue-300 p-1 rounded transition-colors"
                            title="View Details"
                          >
                            <EyeIcon className="w-4 h-4" />
                          </button>
                          
                          {pod.status?.toLowerCase() === 'stopped' && (
                            <button
                              onClick={() => handlePodAction(pod.id, 'start')}
                              disabled={actionLoading === pod.id}
                              className="text-green-400 hover:text-green-300 p-1 rounded disabled:opacity-50 transition-colors"
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
                                className="text-yellow-400 hover:text-yellow-300 p-1 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                title={pod.name.toLowerCase() === 'godfather' ? 'Protected pod - cannot restart' : 'Restart Pod'}
                              >
                                <RestartIcon className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handlePodAction(pod.id, 'stop')}
                                disabled={actionLoading === pod.id || pod.name.toLowerCase() === 'godfather'}
                                className="text-orange-400 hover:text-orange-300 p-1 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                title={pod.name.toLowerCase() === 'godfather' ? 'Protected pod - cannot stop' : 'Stop Pod'}
                              >
                                <StopIcon className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          
                          <button
                            onClick={() => handlePodAction(pod.id, 'terminate')}
                            disabled={actionLoading === pod.id || pod.name.toLowerCase() === 'godfather'}
                            className="text-red-400 hover:text-red-300 p-1 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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