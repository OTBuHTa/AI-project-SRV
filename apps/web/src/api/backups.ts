import {
  apiJson,
  workspaceHeaders,
} from './http'

export type BackupJob = {
  id: string
  workspace_id: string
  backup_type: string
  status: string
  started_at: string | null
  completed_at: string | null
  error: string | null
  created_at: string
}

export type BackupStatus = {
  status: string
  reason: string
  last_verified_at: string | null
  verified_age_seconds: number | null
  failed_jobs: number
  last_failure_at: string | null
  scheduler_lag_seconds: number
}

export type BackupHealth = {
  status: string
  reason: string
  last_verified_at: string | null
  verified_count: number
}

export type BackupStorageHealth = {
  backend: string
  root: string
  writable: boolean
  readable: boolean
  healthy: boolean
  error: string | null
}

export type BackupSchedule = {
  id: string
  workspace_id: string
  enabled: boolean
  interval_minutes: number
  retention_keep_last: number
  retention_max_age_days: number
  last_run_at: string | null
  last_success_at: string | null
  next_run_at: string | null
}

export function getBackupJobs(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<BackupJob[]>(
    '/api/v1/backups',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getBackupStatus(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<BackupStatus>(
    '/api/v1/backups/status',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getBackupHealth(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<BackupHealth>(
    '/api/v1/backups/health',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getBackupStorageHealth(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<BackupStorageHealth>(
    '/api/v1/backups/storage-health',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getBackupSchedule(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<BackupSchedule | null>(
    '/api/v1/backups/schedule',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function createBackup(
  accessToken: string,
  workspaceId: string,
  backupType = 'full',
) {
  return apiJson<BackupJob>(
    '/api/v1/backups',
    {
      method: 'POST',
      headers: {
        ...workspaceHeaders(
          accessToken,
          workspaceId,
        ),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        backup_type: backupType,
      }),
    },
  )
}
