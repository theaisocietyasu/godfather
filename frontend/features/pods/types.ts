export interface Pod {
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
  ports?: Record<string, unknown>;
  machine?: Record<string, unknown>;
  is_public: boolean;
  allowed_users: string[];
  custom_config: {
    storageAmount?: number;
    containerDiskSize?: number;
  };
}

export interface DiscordMember {
  discord_id: string;
  username: string;
  global_name?: string;
  nickname?: string;
  avatar?: string;
  display_name: string;
}

export interface PodConfig {
  name: string;
  image_name: string;
  gpu_type_id: string;
  instance_ids?: string[];
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

export type PodAction = 'start' | 'stop' | 'restart' | 'terminate';
