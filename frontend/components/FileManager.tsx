'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/nextjs';
import toast from 'react-hot-toast';
import {
  Folder as FolderIcon,
  File as FileIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Plus as PlusIcon,
  Trash2 as TrashIcon,
  ArrowLeft as ArrowLeftIcon,
  RefreshCw as RefreshIcon,
  FolderPlus as FolderPlusIcon,
  Home as HomeIcon,
} from 'lucide-react';

interface FileItem {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: number;
  permissions?: string;
}

interface FileManagerProps {
  podId: string;
  initialPath?: string;
}

export default function FileManager({ podId, initialPath = '/workspace' }: FileManagerProps) {
  const { getToken } = useAuth();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [showNewFolderInput, setShowNewFolderInput] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');

  useEffect(() => {
    fetchFiles();
  }, [currentPath]);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch(`/api/pods/${podId}/files?path=${encodeURIComponent(currentPath)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch files');
      }

      const data = await response.json();
      setFiles(data.files);
    } catch (error: any) {
      console.error('Error fetching files:', error);
      toast.error(error.message || 'Failed to fetch files');
    } finally {
      setLoading(false);
    }
  };

  const navigateToDirectory = (dirName: string) => {
    if (dirName === '..') {
      // Go up one directory
      const parts = currentPath.split('/').filter(Boolean);
      parts.pop();
      setCurrentPath('/' + parts.join('/'));
    } else {
      setCurrentPath(`${currentPath}/${dirName}`.replace(/\/+/g, '/'));
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingFile(true);
    try {
      const token = await getToken();
      const formData = new FormData();
      formData.append('file', file);
      formData.append('path', currentPath);

      const response = await fetch(`/api/pods/${podId}/files/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload file');
      }

      toast.success(`File ${file.name} uploaded successfully`);
      fetchFiles(); // Refresh file list
    } catch (error: any) {
      console.error('Error uploading file:', error);
      toast.error(error.message || 'Failed to upload file');
    } finally {
      setUploadingFile(false);
      event.target.value = ''; // Reset input
    }
  };

  const handleDownload = async (fileName: string) => {
    try {
      const token = await getToken();
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/download`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath }),
      });

      if (!response.ok) {
        throw new Error('Failed to download file');
      }

      // Create a blob from the response
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`File ${fileName} downloaded`);
    } catch (error: any) {
      console.error('Error downloading file:', error);
      toast.error(error.message || 'Failed to download file');
    }
  };

  const handleDelete = async (fileName: string, fileType: 'file' | 'directory') => {
    const confirmMsg = fileType === 'directory' 
      ? `Are you sure you want to delete directory "${fileName}"? It must be empty.`
      : `Are you sure you want to delete "${fileName}"?`;
    
    if (!confirm(confirmMsg)) return;

    try {
      const token = await getToken();
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/delete`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath, type: fileType }),
      });

      if (!response.ok) {
        throw new Error('Failed to delete item');
      }

      toast.success(`${fileType === 'directory' ? 'Directory' : 'File'} deleted successfully`);
      fetchFiles(); // Refresh file list
    } catch (error: any) {
      console.error('Error deleting item:', error);
      toast.error(error.message || 'Failed to delete item');
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      toast.error('Please enter a folder name');
      return;
    }

    try {
      const token = await getToken();
      const dirPath = `${currentPath}/${newFolderName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/mkdir`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: dirPath }),
      });

      if (!response.ok) {
        throw new Error('Failed to create directory');
      }

      toast.success(`Directory ${newFolderName} created`);
      setNewFolderName('');
      setShowNewFolderInput(false);
      fetchFiles(); // Refresh file list
    } catch (error: any) {
      console.error('Error creating directory:', error);
      toast.error(error.message || 'Failed to create directory');
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return '-';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDate = (timestamp?: number) => {
    if (!timestamp) return '-';
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentPath('/workspace')}
            className="p-2 hover:bg-gray-200 rounded-md"
            title="Go to workspace root"
          >
            <HomeIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => navigateToDirectory('..')}
            disabled={currentPath === '/' || currentPath === '/workspace'}
            className="p-2 hover:bg-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            title="Go up one directory"
          >
            <ArrowLeftIcon className="w-4 h-4" />
          </button>
          <button
            onClick={fetchFiles}
            disabled={loading}
            className="p-2 hover:bg-gray-200 rounded-md disabled:opacity-50"
            title="Refresh"
          >
            <RefreshIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <span className="text-sm text-gray-600 ml-2">{currentPath}</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowNewFolderInput(!showNewFolderInput)}
            className="flex items-center px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200"
          >
            <FolderPlusIcon className="w-4 h-4 mr-1" />
            New Folder
          </button>
          <label className="flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 cursor-pointer">
            <UploadIcon className="w-4 h-4 mr-1" />
            {uploadingFile ? 'Uploading...' : 'Upload File'}
            <input
              type="file"
              onChange={handleFileUpload}
              disabled={uploadingFile}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* New Folder Input */}
      {showNewFolderInput && (
        <div className="bg-blue-50 px-4 py-3 border-b flex items-center space-x-2">
          <input
            type="text"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="Enter folder name"
            className="flex-1 px-3 py-1.5 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && handleCreateFolder()}
          />
          <button
            onClick={handleCreateFolder}
            className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
          >
            Create
          </button>
          <button
            onClick={() => {
              setShowNewFolderInput(false);
              setNewFolderName('');
            }}
            className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      )}

      {/* File List */}
      <div className="divide-y max-h-96 overflow-y-auto">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-sm text-gray-500 mt-2">Loading files...</p>
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-12">
            <FolderIcon className="mx-auto h-12 w-12 text-gray-300" />
            <p className="text-sm text-gray-500 mt-2">This directory is empty</p>
          </div>
        ) : (
          files.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 hover:bg-gray-50 group"
            >
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                {file.type === 'directory' ? (
                  <button
                    onClick={() => navigateToDirectory(file.name)}
                    className="flex items-center space-x-3 flex-1 min-w-0 text-left"
                  >
                    <FolderIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                      <p className="text-xs text-gray-500">Folder</p>
                    </div>
                  </button>
                ) : (
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <FileIcon className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                      <p className="text-xs text-gray-500">{formatSize(file.size)}</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-4 ml-4">
                <span className="text-xs text-gray-500 hidden md:block">
                  {formatDate(file.modified)}
                </span>
                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {file.type === 'file' && (
                    <button
                      onClick={() => handleDownload(file.name)}
                      className="p-1.5 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="Download"
                    >
                      <DownloadIcon className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(file.name, file.type)}
                    className="p-1.5 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                    title="Delete"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
