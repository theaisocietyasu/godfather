export interface FileItem {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: number;
  permissions?: string;
  path?: string;
}
