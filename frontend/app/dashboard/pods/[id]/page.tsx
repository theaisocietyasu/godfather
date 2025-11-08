'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import toast, { Toaster } from 'react-hot-toast';
import { 
  ServerIcon,
  Play as PlayIcon,
  Square as StopIcon,
  RotateCw as RestartIcon,
  Trash2 as TrashIcon,
  Folder as FolderIcon,
  Edit as EditIcon,
  X as XIcon,
  Save as SaveIcon,
} from 'lucide-react';
import moment from 'moment';
import FileManager from '@/components/FileManager';
import Navbar from '@/components/Navbar';
import Image from 'next/image';

interface DiscordMember {
  discord_id: string;
  username: string;
  global_name?: string;
  nickname?: string;
  avatar?: string;
  display_name: string;
}

interface Pod {
  id: string;
  name: string;
  status: string;
  machine_type: string;
  created_at: string;
  runtime?: Record<string, unknown>;
  ports?: Record<string, unknown>;
  machine?: Record<string, unknown>;
  is_public: boolean;
  allowed_users: string[];
  custom_config: Record<string, unknown>;
}

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
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    is_public: false,
    allowed_users: [] as string[]
  });

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

  const fetchPodDetails = async () => {
    try {
      const response = await fetch(`/api/pods/${podId}`, {
        headers: { 
          'X-Discord-User-ID': session?.user?.discordId || '',
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch pod details');
      }
      
      const data = await response.json();
      setPod(data.pod);
    } catch (error: unknown) {
      console.error('Error fetching pod details:', error);
      toast.error('Failed to fetch pod details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (verifyingAuth) return;
    
    fetchPodDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [podId, verifyingAuth]);

  // Fetch Discord members
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
        }
      } catch (error) {
        console.error('Error fetching Discord members:', error);
      } finally {
        setLoadingMembers(false);
      }
    };

    fetchDiscordMembers();
  }, [session, verifyingAuth]);

  // Initialize edit form when pod data changes
  useEffect(() => {
    if (pod) {
      setEditForm({
        is_public: pod.is_public,
        allowed_users: pod.allowed_users || []
      });
    }
  }, [pod]);

  const handlePodAction = async (action: string) => {
    setActionLoading(true);
    try {
      const response = await fetch(`/api/pods/${podId}/action`, {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to ${action} pod`);
      }
      
      toast.success(`Pod ${action} successful`);
      fetchPodDetails(); // Refresh details
    } catch (error: unknown) {
      console.error(`Error ${action} pod:`, error);
      toast.error(`Failed to ${action} pod`);
    } finally {
      setActionLoading(false);
    }
  };

  const togglePublicAccess = async () => {
    if (!pod) return;
    
    try {
      const response = await fetch(`/api/pods/${podId}`, {
        method: 'PUT',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_public: !pod.is_public }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update pod access');
      }
      
      setPod({ ...pod, is_public: !pod.is_public });
      toast.success(`Pod is now ${!pod.is_public ? 'public' : 'private'}`);
    } catch (error: unknown) {
      console.error('Error updating pod access:', error);
      toast.error('Failed to update pod access');
    }
  };

  const handleOpenEditModal = () => {
    if (pod) {
      setEditForm({
        is_public: pod.is_public,
        allowed_users: pod.allowed_users || []
      });
      setShowEditModal(true);
    }
  };

  const handleSaveEdit = async () => {
    if (!pod) return;

    setEditLoading(true);
    try {
      const response = await fetch(`/api/pods/${podId}`, {
        method: 'PUT',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editForm),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update pod');
      }
      
      setPod({ ...pod, ...editForm });
      toast.success('Pod updated successfully');
      setShowEditModal(false);
      fetchPodDetails(); // Refresh to get latest data
    } catch (error: unknown) {
      console.error('Error updating pod:', error);
      toast.error('Failed to update pod');
    } finally {
      setEditLoading(false);
    }
  };

  const toggleUserSelection = (userId: string) => {
    setEditForm(prev => ({
      ...prev,
      allowed_users: prev.allowed_users.includes(userId)
        ? prev.allowed_users.filter(id => id !== userId)
        : [...prev.allowed_users, userId]
    }));
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

  if (verifyingAuth || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-purple-500/30"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin"></div>
          </div>
          <p className="text-gray-300">
            {verifyingAuth ? 'Verifying access...' : 'Loading pod details...'}
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-purple-500/30"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin"></div>
          </div>
          <p className="text-gray-300">Loading pod details...</p>
        </div>
      </div>
    );
  }

  if (!pod) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <ServerIcon className="mx-auto h-12 w-12 text-gray-500 mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">Pod not found</h3>
          <p className="text-gray-400 mb-4">The requested pod could not be found.</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-pink-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Pod Name Header */}
        <div className="mb-6">
          <div className="flex items-center space-x-4">
            <div>
              <h1 className="text-3xl font-bold text-white">{pod.name}</h1>
              <p className="text-sm text-gray-400">{pod.id}</p>
            </div>
            <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(pod.status)}`}>
              {pod.status}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Pod Information */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <div className="bg-gray-800 shadow rounded-lg p-6 border border-gray-700">
              <h2 className="text-lg font-medium text-white mb-4">Pod Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-400">Machine Type</dt>
                  <dd className="mt-1 text-sm text-gray-200">{pod.machine_type}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-400">Created</dt>
                  <dd className="mt-1 text-sm text-gray-200">{moment(pod.created_at).format('MMMM Do YYYY, h:mm a')}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-400">Runtime</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {pod.runtime ? moment(pod.created_at).fromNow() : 'Not started'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Access</dt>
                  <dd className="mt-1">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      pod.is_public ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {pod.is_public ? 'Public' : 'Private'}
                    </span>
                  </dd>
                </div>
              </div>
            </div>

            {/* Machine Details */}
            {pod.machine && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Machine Details</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(pod.machine).map(([key, value]) => (
                    <div key={key}>
                      <dt className="text-sm font-medium text-gray-500 capitalize">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </dd>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* File Manager */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium text-gray-900">File Manager</h2>
                <button
                  onClick={() => setShowFileManager(!showFileManager)}
                  className="bg-gray-100 text-gray-700 px-3 py-1 rounded-md text-sm hover:bg-gray-200"
                >
                  {showFileManager ? 'Hide' : 'Show'} Files
                </button>
              </div>

              {showFileManager && pod.status?.toLowerCase() === 'running' && (
                <FileManager podId={podId} />
              )}

              {showFileManager && pod.status?.toLowerCase() !== 'running' && (
                <div className="text-center py-8 text-gray-500 border rounded-lg">
                  <FolderIcon className="mx-auto h-12 w-12 text-gray-300 mb-2" />
                  <p>File manager is only available when the pod is running</p>
                </div>
              )}
            </div>
          </div>

          {/* Actions Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
              <div className="space-y-3">
                {pod.status?.toLowerCase() === 'stopped' && (
                  <button
                    onClick={() => handlePodAction('start')}
                    disabled={actionLoading}
                    className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    <PlayIcon className="w-4 h-4 mr-2" />
                    Start Pod
                  </button>
                )}
                
                {pod.status?.toLowerCase() === 'running' && (
                  <>
                    <button
                      onClick={() => handlePodAction('restart')}
                      disabled={actionLoading}
                      className="w-full flex items-center justify-center px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50"
                    >
                      <RestartIcon className="w-4 h-4 mr-2" />
                      Restart Pod
                    </button>
                    <button
                      onClick={() => handlePodAction('stop')}
                      disabled={actionLoading}
                      className="w-full flex items-center justify-center px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50"
                    >
                      <StopIcon className="w-4 h-4 mr-2" />
                      Stop Pod
                    </button>
                  </>
                )}
                
                <button
                  onClick={handleOpenEditModal}
                  className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <EditIcon className="w-4 h-4 mr-2" />
                  Edit Pod Settings
                </button>

                <button
                  onClick={() => handlePodAction('terminate')}
                  disabled={actionLoading}
                  className="w-full flex items-center justify-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  <TrashIcon className="w-4 h-4 mr-2" />
                  Terminate Pod
                </button>
              </div>
            </div>

            {/* Access Control */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Access Control</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Public Access</span>
                  <button
                    onClick={togglePublicAccess}
                    className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 ${
                      pod.is_public ? 'bg-black' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        pod.is_public ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
                
                <div className="text-xs text-gray-500">
                  {pod.is_public 
                    ? 'Users can connect to this pod via CLI' 
                    : 'Only administrators can access this pod'
                  }
                </div>

                {pod.is_public && (
                  <div className="bg-blue-50 p-3 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>CLI Connection:</strong> Users can run the godfather CLI and connect to this pod.
                      Each user will get their own isolated workspace folder.
                    </p>
                  </div>
                )}
              </div>
            </div>


          </div>
        </div>
      </main>

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-700">
            <div className="sticky top-0 bg-gray-800 border-b border-gray-700 px-6 py-4 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">Edit Pod Settings</h2>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <XIcon className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Public Access Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-300">Public Access</label>
                  <p className="text-xs text-gray-500">Allow all members to view and connect via CLI</p>
                </div>
                <button
                  onClick={() => setEditForm({ ...editForm, is_public: !editForm.is_public })}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    editForm.is_public ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      editForm.is_public ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {/* Allowed Users - Only show if private */}
              {!editForm.is_public && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Allowed Users
                  </label>
                  <p className="text-xs text-gray-500 mb-3">
                    Select which members can access this pod via CLI
                  </p>
                  
                  {loadingMembers ? (
                    <div className="text-center py-4">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                    </div>
                  ) : (
                    <div className="max-h-64 overflow-y-auto border border-gray-600 rounded-lg">
                      {discordMembers.map((member) => (
                        <div
                          key={member.discord_id}
                          className="flex items-center justify-between p-3 hover:bg-gray-700 border-b border-gray-600 last:border-b-0"
                        >
                          <div className="flex items-center space-x-3">
                            {member.avatar ? (
                              <Image
                                src={`https://cdn.discordapp.com/avatars/${member.discord_id}/${member.avatar}.png`}
                                alt={member.display_name}
                                width={32}
                                height={32}
                                className="rounded-full"
                              />
                            ) : (
                              <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white text-sm font-bold">
                                {member.display_name.charAt(0).toUpperCase()}
                              </div>
                            )}
                            <div>
                              <p className="text-sm font-medium text-white">{member.display_name}</p>
                              <p className="text-xs text-gray-400">@{member.username}</p>
                            </div>
                          </div>
                          <input
                            type="checkbox"
                            checked={editForm.allowed_users.includes(member.discord_id)}
                            onChange={() => toggleUserSelection(member.discord_id)}
                            className="w-4 h-4 text-blue-600 border-gray-600 rounded focus:ring-blue-500 focus:ring-2 bg-gray-700"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Save Button */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border border-gray-600 text-gray-300 rounded-md hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  disabled={editLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
                >
                  {editLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <SaveIcon className="w-4 h-4 mr-2" />
                      Save Changes
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <Toaster />
    </div>
  );
}