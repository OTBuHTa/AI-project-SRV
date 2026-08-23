import {
  useEffect,
  useState,
} from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../auth/useAuth'

export type RealtimeStatus =
  | 'disabled'
  | 'connecting'
  | 'connected'
  | 'disconnected'

export function useWorkspaceTelemetry(
  enabled = true,
) {
  const auth = useAuth()
  const queryClient = useQueryClient()

  const accessToken =
    auth.tokens?.access_token

  const workspaceId =
    auth.workspace?.id

  const [connectionStatus, setConnectionStatus] =
    useState<Exclude<RealtimeStatus, 'disabled'>>(
      'disconnected',
    )

  useEffect(() => {
    if (
      !enabled
      || !accessToken
      || !workspaceId
    ) {
      return
    }

    const token = accessToken
    const activeWorkspaceId = workspaceId

    let socket: WebSocket | null = null
    let reconnectTimer: number | null = null
    let stopped = false

    function connect() {
      if (stopped) {
        return
      }

      setConnectionStatus('connecting')

      const protocol =
        window.location.protocol === 'https:'
          ? 'wss:'
          : 'ws:'

      const url =
        `${protocol}//${window.location.host}`
        + `/api/v1/monitoring/ws/${activeWorkspaceId}`

      socket = new WebSocket(url)

      socket.onopen = () => {
        socket?.send(JSON.stringify({
          type: 'auth',
          token,
        }))
      }

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(
            event.data,
          ) as {
            type?: string
          }

          if (
            message.type === 'auth.ok'
          ) {
            setConnectionStatus('connected')
            return
          }

          if (
            message.type === 'resource.telemetry'
          ) {
            void queryClient.invalidateQueries({
              queryKey: ['agents'],
            })
          }
        } catch {
          // Ignore malformed realtime events.
        }
      }

      socket.onerror = () => {
        setConnectionStatus('disconnected')
      }

      socket.onclose = (event) => {
        setConnectionStatus('disconnected')

        if (
          stopped
          || event.code === 4401
          || event.code === 4403
        ) {
          return
        }

        reconnectTimer = window.setTimeout(
          connect,
          2000,
        )
      }
    }

    connect()

    return () => {
      stopped = true

      if (reconnectTimer !== null) {
        window.clearTimeout(
          reconnectTimer,
        )
      }

      socket?.close()
    }
  }, [
    accessToken,
    workspaceId,
    queryClient,
    enabled,
  ])

  if (
    !enabled
    || !accessToken
    || !workspaceId
  ) {
    return 'disabled'
  }

  return connectionStatus
}
