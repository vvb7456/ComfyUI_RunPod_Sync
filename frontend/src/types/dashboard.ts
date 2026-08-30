export type DashboardState =
  | 'loading'
  | 'ready'
  | 'busy'
  | 'starting'
  | 'stopped'
  | 'fault'
  | 'unavailable'

export interface SyncLogEntry {
  ts?: string
  key?: string
  params?: Record<string, unknown>
  level?: string
}

export interface DownloadTask {
  download_id?: string
  filename: string
  model_name?: string
  progress: number
  speed?: string | number
  completed_bytes?: number
  total_bytes?: number
  status?: string
}

export interface ServiceEntry {
  name: string
  pm_id?: number
  status?: string
  uptime?: number | string
  cpu?: number | string
  memory?: number | string
  restarts?: number
  pid?: number
}

export interface OverviewData {
  comfyui: {
    online: boolean
    version: string
    pm2_status: string
    pm2_uptime: number
    pm2_restarts?: number
    queue_running: number
    queue_pending: number
    pytorch_version: string
    python_version: string
    port: number
    executing?: boolean
    exec_start_time?: number
    progress?: { value: number; max: number; percent?: number } | null
  }
  jupyter: {
    online: boolean
    pm2_status: string
    port: number
  }
  sync: {
    worker_running: boolean
    rules_count: number
    watch_rules: number
    last_log_lines: Array<string | SyncLogEntry>
  }
  tunnel: {
    effective_status: string
    urls: Record<string, string>
    public?: { urls: Record<string, string> }
  }
  downloads: {
    active_count: number
    active: DownloadTask[]
    queue_count: number
  }
  services: ServiceEntry[] | {
    services?: ServiceEntry[]
    error?: string
  }
  version: { version: string }
}

/** Fast-changing activity data from GET /api/activity (5s poll) */
export interface ActivityData {
  comfyui: {
    online: boolean
    queue_running: number
    queue_pending: number
    executing?: boolean
    exec_start_time?: number
    progress?: { value: number; max: number; percent?: number } | null
  }
  downloads: {
    active_count: number
    active: DownloadTask[]
    queue_count: number
  }
  sync: {
    worker_running: boolean
    last_log_lines: Array<string | SyncLogEntry>
  }
}
