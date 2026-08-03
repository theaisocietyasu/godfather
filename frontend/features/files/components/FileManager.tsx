'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
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
import Button from '@/components/Button';
import { Input } from '@/components/Input';
import EmptyState from '@/components/EmptyState';
import { Skeleton } from '@/components/Skeleton';
import {
  listFiles,
  uploadFile as apiUploadFile,
  downloadFile,
  deleteFile,
  bulkDeleteFiles,
  createFolder,
  readFile,
  writeFile,
  renameFileOrDir,
  copyFileOrDir,
  searchFiles,
} from '../api';
import type { FileItem } from '../types';

interface FileManagerProps {
  podId: string;
  initialPath?: string;
}

const TEXT_EXTENSIONS = [
  '.txt', '.md', '.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml',
  '.xml', '.html', '.css', '.sh', '.bash', '.env', '.gitignore', '.log',
];

function isTextFile(fileName: string) {
  return TEXT_EXTENSIONS.some((ext) => fileName.toLowerCase().endsWith(ext));
}

function formatSize(bytes?: number) {
  if (!bytes) return '-';
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

function formatDate(timestamp?: number) {
  if (!timestamp) return '-';
  return new Date(timestamp * 1000).toLocaleString();
}

export default function FileManager({ podId, initialPath = '/workspace' }: FileManagerProps) {
  const { data: session } = useSession();
  const discordId = session?.user?.discordId || '';

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

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listFiles(podId, currentPath, discordId);
      setFiles(data);
      setSelectedFiles(new Set());
    } catch (error: unknown) {
      console.error('Error fetching files:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to fetch files');
    } finally {
      setLoading(false);
    }
  }, [podId, currentPath, discordId]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

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

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    for (const file of Array.from(e.dataTransfer.files)) {
      await uploadFile(file);
    }
  };

  const uploadFile = async (file: File) => {
    setUploadingFile(true);
    try {
      await apiUploadFile(podId, currentPath, file, discordId);
      toast.success(`${file.name} uploaded`);
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error uploading file:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to upload file');
    } finally {
      setUploadingFile(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = event.target.files;
    if (!fileList) return;
    for (const file of Array.from(fileList)) {
      await uploadFile(file);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDownload = async (fileName: string) => {
    try {
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');
      const blob = await downloadFile(podId, filePath, discordId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success(`${fileName} downloaded`);
    } catch (error: unknown) {
      console.error('Error downloading file:', error);
      toast.error('Failed to download file');
    }
  };

  const handleDelete = async (fileName: string, fileType: 'file' | 'directory') => {
    const confirmMsg =
      fileType === 'directory' ? `Delete directory "${fileName}"?` : `Delete "${fileName}"?`;
    if (!confirm(confirmMsg)) return;

    try {
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');
      await deleteFile(podId, filePath, fileType, discordId);
      toast.success(`${fileType === 'directory' ? 'Directory' : 'File'} deleted`);
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
      const paths = Array.from(selectedFiles).map((name) => `${currentPath}/${name}`.replace(/\/+/g, '/'));
      const message = await bulkDeleteFiles(podId, paths, discordId);
      toast.success(message);
      setSelectedFiles(new Set());
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error deleting items:', error);
      toast.error('Failed to delete items');
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      toast.error('Enter a folder name');
      return;
    }
    try {
      const dirPath = `${currentPath}/${newFolderName}`.replace(/\/+/g, '/');
      await createFolder(podId, dirPath, discordId);
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
      const content = await readFile(podId, filePath, discordId);
      setPreviewFile({ path: filePath, content, name: fileName });
    } catch (error: unknown) {
      console.error('Error reading file:', error);
      toast.error('Failed to read file');
    }
  };

  const handleEdit = async (fileName: string) => {
    try {
      const filePath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');
      const content = await readFile(podId, filePath, discordId);
      setEditingFile({ path: filePath, content, name: fileName });
    } catch (error: unknown) {
      console.error('Error reading file:', error);
      toast.error('Failed to read file');
    }
  };

  const handleSaveEdit = async () => {
    if (!editingFile) return;
    try {
      await writeFile(podId, editingFile.path, editingFile.content, discordId);
      toast.success('File saved');
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
      await renameFileOrDir(podId, oldPath, newPath, discordId);
      toast.success('Item renamed');
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
    toast.success(`"${fileName}" copied. Navigate to a destination and paste.`);
  };

  const handlePaste = async () => {
    if (!copySource) return;
    try {
      const fileName = copySource.split('/').pop();
      const destPath = `${currentPath}/${fileName}`.replace(/\/+/g, '/');
      await copyFileOrDir(podId, copySource, destPath, discordId);
      toast.success('Item pasted');
      setCopySource(null);
      fetchFiles();
    } catch (error: unknown) {
      console.error('Error copying item:', error);
      toast.error('Failed to copy item');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Enter a search term');
      return;
    }
    setIsSearching(true);
    try {
      const results = await searchFiles(podId, searchQuery, currentPath, discordId);
      setSearchResults(results);
      toast.success(`Found ${results.length} result(s)`);
    } catch (error: unknown) {
      console.error('Error searching files:', error);
      toast.error('Failed to search files');
    } finally {
      setIsSearching(false);
    }
  };

  const toggleFileSelection = (fileName: string) => {
    const newSelection = new Set(selectedFiles);
    if (newSelection.has(fileName)) newSelection.delete(fileName);
    else newSelection.add(fileName);
    setSelectedFiles(newSelection);
  };

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-bg-elevated">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-surface px-4 py-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPath('/workspace')}
            className="rounded-md p-2 text-text-secondary hover:bg-surface-hover hover:text-text"
            title="Go to workspace root"
          >
            <HomeIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => navigateToDirectory('..')}
            disabled={currentPath === '/' || currentPath === '/workspace'}
            className="rounded-md p-2 text-text-secondary hover:bg-surface-hover hover:text-text disabled:cursor-not-allowed disabled:opacity-50"
            title="Go up one directory"
          >
            <ArrowLeftIcon className="h-4 w-4" />
          </button>
          <button
            onClick={fetchFiles}
            disabled={loading}
            className="rounded-md p-2 text-text-secondary hover:bg-surface-hover hover:text-text disabled:opacity-50"
            title="Refresh"
          >
            <RefreshIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <span className="font-mono text-sm text-text-muted">{currentPath}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="rounded-md p-2 text-text-secondary hover:bg-surface-hover hover:text-text"
            title="Search files"
          >
            <SearchIcon className="h-4 w-4" />
          </button>
          {copySource && (
            <Button size="sm" variant="secondary" onClick={handlePaste}>
              Paste
            </Button>
          )}
          {selectedFiles.size > 0 && (
            <Button size="sm" variant="danger" onClick={handleBulkDelete}>
              <TrashIcon className="h-4 w-4" />
              Delete ({selectedFiles.size})
            </Button>
          )}
          <Button size="sm" variant="secondary" onClick={() => setShowNewFolderInput(!showNewFolderInput)}>
            <FolderPlusIcon className="h-4 w-4" />
            New folder
          </Button>
          <label>
            <Button size="sm" loading={uploadingFile} type="button" onClick={() => fileInputRef.current?.click()}>
              {!uploadingFile && <UploadIcon className="h-4 w-4" />}
              {uploadingFile ? 'Uploading...' : 'Upload'}
            </Button>
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

      {/* Search bar */}
      {showSearch && (
        <div className="flex items-center gap-2 border-b border-border bg-info-soft px-4 py-3">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files by name"
            className="flex-1"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button size="sm" loading={isSearching} onClick={handleSearch}>
            Search
          </Button>
          <button
            onClick={() => {
              setShowSearch(false);
              setSearchResults([]);
              setSearchQuery('');
            }}
            className="rounded-md p-1.5 text-text-secondary hover:bg-surface-hover"
          >
            <XIcon className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Search results */}
      {searchResults.length > 0 && (
        <div className="border-b border-border bg-warning-soft px-4 py-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-text">Search results ({searchResults.length})</span>
            <button onClick={() => setSearchResults([])} className="text-sm text-accent hover:underline">
              Clear
            </button>
          </div>
          <div className="max-h-48 space-y-1 overflow-y-auto">
            {searchResults.map((result, idx) => (
              <div
                key={idx}
                className="cursor-pointer rounded p-2 text-sm text-text-secondary hover:bg-surface-hover"
                onClick={() => {
                  const dirPath = result.path!.substring(0, result.path!.lastIndexOf('/'));
                  setCurrentPath(dirPath || '/workspace');
                  setSearchResults([]);
                }}
              >
                <span className="inline-flex items-center gap-2">
                  {result.type === 'directory' ? (
                    <FolderIcon className="h-3.5 w-3.5 text-accent" />
                  ) : (
                    <FileIcon className="h-3.5 w-3.5 text-text-muted" />
                  )}
                  {result.path}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* New folder input */}
      {showNewFolderInput && (
        <div className="flex items-center gap-2 border-b border-border bg-info-soft px-4 py-3">
          <Input
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="Folder name"
            className="flex-1"
            onKeyDown={(e) => e.key === 'Enter' && handleCreateFolder()}
          />
          <Button size="sm" onClick={handleCreateFolder}>
            Create
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              setShowNewFolderInput(false);
              setNewFolderName('');
            }}
          >
            Cancel
          </Button>
        </div>
      )}

      {/* Rename input */}
      {renameFile && (
        <div className="flex items-center gap-2 border-b border-border bg-accent-soft px-4 py-3">
          <span className="text-sm text-text-secondary">Rename:</span>
          <Input
            value={renameFile.newName}
            onChange={(e) => setRenameFile({ ...renameFile, newName: e.target.value })}
            placeholder="New name"
            className="flex-1"
            onKeyDown={(e) => e.key === 'Enter' && handleRename()}
          />
          <button onClick={handleRename} className="rounded-md bg-accent p-2 text-white hover:bg-accent-hover">
            <CheckIcon className="h-4 w-4" />
          </button>
          <button
            onClick={() => setRenameFile(null)}
            className="rounded-md bg-surface-hover p-2 text-text-secondary hover:bg-border"
          >
            <XIcon className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* File list */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`max-h-96 divide-y divide-border overflow-y-auto ${
          isDragging ? 'border-2 border-dashed border-accent bg-accent-soft' : ''
        }`}
      >
        {isDragging && (
          <div className="py-12 text-center">
            <UploadIcon className="mx-auto h-12 w-12 text-accent" />
            <p className="mt-2 font-medium text-accent">Drop files to upload</p>
          </div>
        )}

        {!isDragging && loading && (
          <div className="space-y-2 p-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}

        {!isDragging && !loading && files.length === 0 && (
          <EmptyState icon={FolderIcon} title="This directory is empty" />
        )}

        {!isDragging &&
          !loading &&
          files.length > 0 &&
          files.map((file, index) => (
            <div
              key={index}
              className={`group flex items-center justify-between p-3 hover:bg-surface-hover ${
                selectedFiles.has(file.name) ? 'bg-accent-soft' : ''
              }`}
            >
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <input
                  type="checkbox"
                  checked={selectedFiles.has(file.name)}
                  onChange={() => toggleFileSelection(file.name)}
                  className="rounded border-border-strong bg-bg-elevated text-accent focus:ring-accent"
                />
                {file.type === 'directory' ? (
                  <button
                    onClick={() => navigateToDirectory(file.name)}
                    className="flex min-w-0 flex-1 items-center gap-3 text-left"
                  >
                    <FolderIcon className="h-5 w-5 flex-shrink-0 text-accent" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-text">{file.name}</p>
                      <p className="text-xs text-text-muted">Folder</p>
                    </div>
                  </button>
                ) : (
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <FileIcon className="h-5 w-5 flex-shrink-0 text-text-muted" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-text">{file.name}</p>
                      <p className="text-xs text-text-muted">{formatSize(file.size)}</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="ml-4 flex items-center gap-4">
                <span className="hidden text-xs text-text-muted md:block">{formatDate(file.modified)}</span>
                <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  {file.type === 'file' && isTextFile(file.name) && (
                    <>
                      <button
                        onClick={() => handlePreview(file.name)}
                        className="rounded p-1.5 text-text-secondary hover:bg-success-soft hover:text-success"
                        title="Preview"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(file.name)}
                        className="rounded p-1.5 text-text-secondary hover:bg-accent-soft hover:text-accent"
                        title="Edit"
                      >
                        <EditIcon className="h-4 w-4" />
                      </button>
                    </>
                  )}
                  {file.type === 'file' && (
                    <button
                      onClick={() => handleDownload(file.name)}
                      className="rounded p-1.5 text-text-secondary hover:bg-info-soft hover:text-info"
                      title="Download"
                    >
                      <DownloadIcon className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={() => handleCopy(file.name)}
                    className="rounded p-1.5 text-text-secondary hover:bg-accent-soft hover:text-accent"
                    title="Copy"
                  >
                    <CopyIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setRenameFile({ oldName: file.name, newName: file.name })}
                    className="rounded p-1.5 text-text-secondary hover:bg-warning-soft hover:text-warning"
                    title="Rename"
                  >
                    <EditIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(file.name, file.type)}
                    className="rounded p-1.5 text-text-secondary hover:bg-danger-soft hover:text-danger"
                    title="Delete"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
      </div>

      {/* Preview modal */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="flex max-h-[80vh] w-full max-w-4xl flex-col rounded-lg border border-border bg-surface">
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="text-lg font-medium text-text">Preview: {previewFile.name}</h3>
              <button onClick={() => setPreviewFile(null)} className="rounded p-1 hover:bg-surface-hover">
                <XIcon className="h-5 w-5 text-text-secondary" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <pre className="whitespace-pre-wrap rounded bg-bg-elevated p-4 font-mono text-sm text-text">
                {previewFile.content}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Edit modal */}
      {editingFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="flex max-h-[80vh] w-full max-w-4xl flex-col rounded-lg border border-border bg-surface">
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="text-lg font-medium text-text">Edit: {editingFile.name}</h3>
              <div className="flex gap-2">
                <Button size="sm" onClick={handleSaveEdit}>
                  <SaveIcon className="h-4 w-4" />
                  Save
                </Button>
                <button onClick={() => setEditingFile(null)} className="rounded p-1 hover:bg-surface-hover">
                  <XIcon className="h-5 w-5 text-text-secondary" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <textarea
                value={editingFile.content}
                onChange={(e) => setEditingFile({ ...editingFile, content: e.target.value })}
                className="h-full w-full rounded border border-border bg-bg-elevated p-4 font-mono text-sm text-text focus:outline-none focus:ring-2 focus:ring-accent"
                style={{ minHeight: '400px' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
