'use client';

import { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import toast from 'react-hot-toast';
import {
  Folder as FolderIcon,
  File as FileIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Trash2 as TrashIcon,
  ArrowLeft as ArrowLeftIcon,
  RefreshCw as RefreshIcon,
  FolderPlus as FolderPlusIcon,
  Home as HomeIcon,
  Edit2 as EditIcon,
  Eye as EyeIcon,
  Copy as CopyIcon,
  Search as SearchIcon,
  X as XIcon,
  Check as CheckIcon,
  Save as SaveIcon,
} from 'lucide-react';

interface FileItem {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: number;
  permissions?: string;
  path?: string;
}

interface FileManagerProps {
  podId: string;
  initialPath?: string;
}

// Helper function to extract error message from response
async function getErrorMessage(response: Response, defaultMessage: string): Promise<string> {
  try {
    const errorData = await response.json();
    return errorData.error || defaultMessage;
  } catch {
    return defaultMessage;
  }
}

export default function FileManager({ podId, initialPath = '/workspace' }: FileManagerProps) {
  const { data: session } = useSession();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [showNewFolderInput, setShowNewFolderInput] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FileItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [previewFile, setPreviewFile] = useState<{ path: string; content: string; name: string } | null>(null);
  const [editingFile, setEditingFile] = useState<{ path: string; content: string; name: string } | null>(null);
  const [renameFile, setRenameFile] = useState<{ oldName: string; newName: string } | null>(null);
  const [copySource, setCopySource] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPath]);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/pods/${podId}/files?path=${encodeURIComponent(currentPath)}`, {
        headers: { 
          'X-Discord-User-ID': session?.user?.discordId || '',
        },
      });

      if (!response.ok) {
        const errorMessage = await getErrorMessage(response, 'Failed to fetch files');
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setFiles(data.files);
      setSelectedFiles(new Set());
    } catch (error: unknown) {
      console.error('Error fetching files:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch files';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const navigateToDirectory = (dirName: string) => {
    if (dirName === '..') {
      const parts = currentPath.split('/').filter(Boolean);
      parts.pop();
      setCurrentPath('/' + parts.join('/'));
    } else {
      setCurrentPath(`${currentPath}/${dirName}`.replace(/\/+/g, '/'));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    for (const file of droppedFiles) {
      await uploadFile(file);
    }
  };

  const uploadFile = async (file: File) => {
    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('path', currentPath);

      const response = await fetch(`/api/pods/${podId}/files/upload`, {
        method: 'POST',
        headers: { 
          'X-Discord-User-ID': session?.user?.discordId || '',
        },
        body: formData,
      });

      if (!response.ok) {
        const errorMessage = await getErrorMessage(response, 'Failed to upload file');
        throw new Error(errorMessage);
      }

      toast.success(`File ${file.name} uploaded successfully`);
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error uploading file:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload file';
      toast.error(errorMessage);
    } finally {
      setUploadingFile(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = event.target.files;
    if (!fileList) return;

    const files = Array.from(fileList);
    for (const file of files) {
      await uploadFile(file);
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDownload = async (fileName: string) => {
    try {
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/download`, {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath }),
      });

      if (!response.ok) {
        throw new Error('Failed to download file');
      }

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
    } catch (error: unknown) {
      console.error('Error downloading file:', error);
      toast.error('Failed to download file');
    }
  };

  const handleDelete = async (fileName: string, fileType: 'file' | 'directory') => {
    const confirmMsg = fileType === 'directory' 
      ? `Are you sure you want to delete directory "${fileName}"?`
      : `Are you sure you want to delete "${fileName}"?`;
    
    if (!confirm(confirmMsg)) return;

    try {
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/delete`, {
        method: 'DELETE',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath, type: fileType }),
      });

      if (!response.ok) {
        throw new Error('Failed to delete item');
      }

      toast.success(`${fileType === 'directory' ? 'Directory' : 'File'} deleted successfully`);
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error deleting item:', error);
      toast.error('Failed to delete item');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedFiles.size === 0) {
      toast.error('No files selected');
      return;
    }

    if (!confirm(`Delete ${selectedFiles.size} selected item(s)?`)) return;

    try {
      const paths = Array.from(selectedFiles).map(name => `${currentPath}/${name}`.replace(/\/+/g, '/'));

      const response = await fetch(`/api/pods/${podId}/files/bulk-delete`, {
        method: 'DELETE',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ paths }),
      });

      if (!response.ok) {
        throw new Error('Failed to delete items');
      }

      const data = await response.json();
      toast.success(data.message);
      setSelectedFiles(new Set());
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error deleting items:', error);
      toast.error('Failed to delete items');
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      toast.error('Please enter a folder name');
      return;
    }

    try {
      const dirPath = `${currentPath}/${newFolderName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/mkdir`, {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
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
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error creating directory:', error);
      toast.error('Failed to create directory');
    }
  };

  const handlePreview = async (fileName: string) => {
    try {
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/read`, {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath }),
      });

      if (!response.ok) {
        throw new Error('Failed to read file');
      }

      const data = await response.json();
      setPreviewFile({ path: filePath, content: data.content, name: fileName });
    } catch (error: unknown) {
      console.error('Error reading file:', error);
      toast.error('Failed to read file');
    }
  };

  const handleEdit = async (fileName: string) => {
    try {
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/read`, {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: filePath }),
      });

      if (!response.ok) {
        throw new Error('Failed to read file');
      }

      const data = await response.json();
      setEditingFile({ path: filePath, content: data.content, name: fileName });
    } catch (error: unknown) {
      console.error('Error reading file:', error);
      toast.error('Failed to read file');
    }
  };

  const handleSaveEdit = async () => {
    if (!editingFile) return;

    try {
      const response = await fetch(`/api/pods/${podId}/files/write`, {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: editingFile.path, content: editingFile.content }),
      });

      if (!response.ok) {
        throw new Error('Failed to save file');
      }

      toast.success('File saved successfully');
      setEditingFile(null);
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error saving file:', error);
      toast.error('Failed to save file');
    }
  };

  const handleRename = async () => {
    if (!renameFile || !renameFile.newName.trim()) return;

    try {
      const oldPath = `${currentPath}/${renameFile.oldName}`.replace(/\/+/g, '/');
      const newPath = `${currentPath}/${renameFile.newName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/rename`, {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ old_path: oldPath, new_path: newPath }),
      });

      if (!response.ok) {
        throw new Error('Failed to rename item');
      }

      toast.success('Item renamed successfully');
      setRenameFile(null);
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error renaming item:', error);
      toast.error('Failed to rename item');
    }
  };

  const handleCopy = (fileName: string) => {
    const sourcePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');
    setCopySource(sourcePath);
    toast.success(`"${fileName}" copied. Navigate to destination and paste.`);
  };

  const handlePaste = async () => {
    if (!copySource) return;

    try {
      const fileName = copySource.split('/').pop();
      const destPath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');

      const response = await fetch(`/api/pods/${podId}/files/copy`, {
        method: 'POST',
        headers: {
          'X-Discord-User-ID': session?.user?.discordId || '',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source_path: copySource, dest_path: destPath }),
      });

      if (!response.ok) {
        throw new Error('Failed to copy item');
      }

      toast.success('Item pasted successfully');
      setCopySource(null);
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error copying item:', error);
      toast.error('Failed to copy item');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Please enter a search term');
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(
        `/api/pods/${podId}/files/search?query=${encodeURIComponent(searchQuery)}&path=${encodeURIComponent(currentPath)}`,
        {
          headers: { 
            'X-Discord-User-ID': session?.user?.discordId || '',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to search files');
      }

      const data = await response.json();
      setSearchResults(data.results);
      toast.success(`Found ${data.results.length} result(s)`);
    } catch (error: unknown) {
      console.error('Error searching files:', error);
      toast.error('Failed to search files');
    } finally {
      setIsSearching(false);
    }
  };

  const toggleFileSelection = (fileName: string) => {
    const newSelection = new Set(selectedFiles);
    if (newSelection.has(fileName)) {
      newSelection.delete(fileName);
    } else {
      newSelection.add(fileName);
    }
    setSelectedFiles(newSelection);
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

  const isTextFile = (fileName: string) => {
    const textExtensions = ['.txt', '.md', '.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.sh', '.bash', '.env', '.gitignore', '.log'];
    return textExtensions.some(ext => fileName.toLowerCase().endsWith(ext));
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between flex-wrap gap-2">
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
          <span className="text-sm text-gray-600">{currentPath}</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="p-2 hover:bg-gray-200 rounded-md"
            title="Search files"
          >
            <SearchIcon className="w-4 h-4" />
          </button>
          {copySource && (
            <button
              onClick={handlePaste}
              className="flex items-center px-3 py-1.5 bg-purple-100 text-purple-700 rounded-md text-sm hover:bg-purple-200"
            >
              Paste
            </button>
          )}
          {selectedFiles.size > 0 && (
            <button
              onClick={handleBulkDelete}
              className="flex items-center px-3 py-1.5 bg-red-100 text-red-700 rounded-md text-sm hover:bg-red-200"
            >
              <TrashIcon className="w-4 h-4 mr-1" />
              Delete ({selectedFiles.size})
            </button>
          )}
          <button
            onClick={() => setShowNewFolderInput(!showNewFolderInput)}
            className="flex items-center px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200"
          >
            <FolderPlusIcon className="w-4 h-4 mr-1" />
            New Folder
          </button>
          <label className="flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 cursor-pointer">
            <UploadIcon className="w-4 h-4 mr-1" />
            {uploadingFile ? 'Uploading...' : 'Upload'}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileUpload}
              disabled={uploadingFile}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Search Bar */}
      {showSearch && (
        <div className="bg-blue-50 px-4 py-3 border-b flex items-center space-x-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files by name..."
            className="flex-1 px-3 py-1.5 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
          <button
            onClick={() => {
              setShowSearch(false);
              setSearchResults([]);
              setSearchQuery('');
            }}
            className="p-1.5 hover:bg-gray-200 rounded-md"
          >
            <XIcon className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-yellow-50 px-4 py-3 border-b">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Search Results ({searchResults.length})</span>
            <button
              onClick={() => setSearchResults([])}
              className="text-sm text-blue-600 hover:underline"
            >
              Clear Results
            </button>
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {searchResults.map((result, idx) => (
              <div key={idx} className="text-sm text-gray-700 hover:bg-yellow-100 p-2 rounded cursor-pointer"
                onClick={() => {
                  const dirPath = result.path!.substring(0, result.path!.lastIndexOf('/'));
                  setCurrentPath(dirPath || '/workspace');
                  setSearchResults([]);
                }}
              >
                {result.type === 'directory' ? '📁' : '📄'} {result.path}
              </div>
            ))}
          </div>
        </div>
      )}

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

      {/* Rename Input */}
      {renameFile && (
        <div className="bg-purple-50 px-4 py-3 border-b flex items-center space-x-2">
          <span className="text-sm">Rename:</span>
          <input
            type="text"
            value={renameFile.newName}
            onChange={(e) => setRenameFile({ ...renameFile, newName: e.target.value })}
            placeholder="Enter new name"
            className="flex-1 px-3 py-1.5 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            onKeyPress={(e) => e.key === 'Enter' && handleRename()}
          />
          <button
            onClick={handleRename}
            className="px-3 py-1.5 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700"
          >
            <CheckIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => setRenameFile(null)}
            className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300"
          >
            <XIcon className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`divide-y max-h-96 overflow-y-auto ${isDragging ? 'bg-blue-50 border-2 border-dashed border-blue-400' : ''}`}
      >
        {isDragging && (
          <div className="text-center py-12">
            <UploadIcon className="mx-auto h-12 w-12 text-blue-500" />
            <p className="text-blue-600 font-medium mt-2">Drop files to upload</p>
          </div>
        )}
        
        {!isDragging && loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-sm text-gray-500 mt-2">Loading files...</p>
          </div>
        )}
        
        {!isDragging && !loading && files.length === 0 && (
          <div className="text-center py-12">
            <FolderIcon className="mx-auto h-12 w-12 text-gray-300" />
            <p className="text-sm text-gray-500 mt-2">This directory is empty</p>
          </div>
        )}
        
        {!isDragging && !loading && files.length > 0 && (
          files.map((file, index) => (
            <div
              key={index}
              className={`flex items-center justify-between p-3 hover:bg-gray-50 group ${selectedFiles.has(file.name) ? 'bg-blue-50' : ''}`}
            >
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                <input
                  type="checkbox"
                  checked={selectedFiles.has(file.name)}
                  onChange={() => toggleFileSelection(file.name)}
                  className="rounded border-gray-300"
                />
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
                  {file.type === 'file' && isTextFile(file.name) && (
                    <>
                      <button
                        onClick={() => handlePreview(file.name)}
                        className="p-1.5 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded"
                        title="Preview"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(file.name)}
                        className="p-1.5 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded"
                        title="Edit"
                      >
                        <EditIcon className="w-4 h-4" />
                      </button>
                    </>
                  )}
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
                    onClick={() => handleCopy(file.name)}
                    className="p-1.5 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                    title="Copy"
                  >
                    <CopyIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setRenameFile({ oldName: file.name, newName: file.name })}
                    className="p-1.5 text-gray-600 hover:text-orange-600 hover:bg-orange-50 rounded"
                    title="Rename"
                  >
                    <EditIcon className="w-4 h-4" />
                  </button>
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

      {/* Preview Modal */}
      {previewFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] flex flex-col">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-medium">Preview: {previewFile.name}</h3>
              <button onClick={() => setPreviewFile(null)} className="p-1 hover:bg-gray-100 rounded">
                <XIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-auto flex-1">
              <pre className="text-sm whitespace-pre-wrap font-mono bg-gray-50 p-4 rounded">{previewFile.content}</pre>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] flex flex-col">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-medium">Edit: {editingFile.name}</h3>
              <div className="flex space-x-2">
                <button
                  onClick={handleSaveEdit}
                  className="flex items-center px-3 py-1.5 bg-green-600 text-white rounded-md text-sm hover:bg-green-700"
                >
                  <SaveIcon className="w-4 h-4 mr-1" />
                  Save
                </button>
                <button onClick={() => setEditingFile(null)} className="p-1 hover:bg-gray-100 rounded">
                  <XIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="p-4 overflow-auto flex-1">
              <textarea
                value={editingFile.content}
                onChange={(e) => setEditingFile({ ...editingFile, content: e.target.value })}
                className="w-full h-full font-mono text-sm p-4 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={{ minHeight: '400px' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
