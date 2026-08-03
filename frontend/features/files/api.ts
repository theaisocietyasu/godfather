import { apiFetch } from '@/lib/api-client';
import type { FileItem } from './types';

async function errorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json();
    return data.error || fallback;
  } catch {
    return fallback;
  }
}

export async function listFiles(podId: string, path: string, discordId: string): Promise<FileItem[]> {
  const response = await apiFetch(`/api/pods/${podId}/files?path=${encodeURIComponent(path)}`, { discordId });
  if (!response.ok) throw new Error(await errorMessage(response, 'Failed to fetch files'));
  const data = await response.json();
  return data.files;
}

export async function uploadFile(podId: string, path: string, file: File, discordId: string): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('path', path);
  const response = await apiFetch(`/api/pods/${podId}/files/upload`, {
    method: 'POST',
    discordId,
    body: formData,
  });
  if (!response.ok) throw new Error(await errorMessage(response, 'Failed to upload file'));
}

export async function downloadFile(podId: string, path: string, discordId: string): Promise<Blob> {
  const response = await apiFetch(`/api/pods/${podId}/files/download`, {
    method: 'POST',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!response.ok) throw new Error('Failed to download file');
  return response.blob();
}

export async function deleteFile(podId: string, path: string, type: 'file' | 'directory', discordId: string): Promise<void> {
  const response = await apiFetch(`/api/pods/${podId}/files/delete`, {
    method: 'DELETE',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, type }),
  });
  if (!response.ok) throw new Error('Failed to delete item');
}

export async function bulkDeleteFiles(podId: string, paths: string[], discordId: string): Promise<string> {
  const response = await apiFetch(`/api/pods/${podId}/files/bulk-delete`, {
    method: 'DELETE',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paths }),
  });
  if (!response.ok) throw new Error('Failed to delete items');
  const data = await response.json();
  return data.message;
}

export async function createFolder(podId: string, path: string, discordId: string): Promise<void> {
  const response = await apiFetch(`/api/pods/${podId}/files/mkdir`, {
    method: 'POST',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!response.ok) throw new Error('Failed to create directory');
}

export async function readFile(podId: string, path: string, discordId: string): Promise<string> {
  const response = await apiFetch(`/api/pods/${podId}/files/read`, {
    method: 'POST',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!response.ok) throw new Error('Failed to read file');
  const data = await response.json();
  return data.content;
}

export async function writeFile(podId: string, path: string, content: string, discordId: string): Promise<void> {
  const response = await apiFetch(`/api/pods/${podId}/files/write`, {
    method: 'POST',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, content }),
  });
  if (!response.ok) throw new Error('Failed to save file');
}

export async function renameFileOrDir(podId: string, oldPath: string, newPath: string, discordId: string): Promise<void> {
  const response = await apiFetch(`/api/pods/${podId}/files/rename`, {
    method: 'POST',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ old_path: oldPath, new_path: newPath }),
  });
  if (!response.ok) throw new Error('Failed to rename item');
}

export async function copyFileOrDir(podId: string, sourcePath: string, destPath: string, discordId: string): Promise<void> {
  const response = await apiFetch(`/api/pods/${podId}/files/copy`, {
    method: 'POST',
    discordId,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_path: sourcePath, dest_path: destPath }),
  });
  if (!response.ok) throw new Error('Failed to copy item');
}

export async function searchFiles(podId: string, query: string, path: string, discordId: string): Promise<FileItem[]> {
  const response = await apiFetch(
    `/api/pods/${podId}/files/search?query=${encodeURIComponent(query)}&path=${encodeURIComponent(path)}`,
    { discordId }
  );
  if (!response.ok) throw new Error('Failed to search files');
  const data = await response.json();
  return data.results;
}
