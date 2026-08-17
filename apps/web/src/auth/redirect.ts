export function safeNext(
  value: string | null | undefined,
) {
  if (
    !value
    || !value.startsWith('/')
    || value.startsWith('//')
    || value === '/login'
    || value.startsWith('/login?')
    || value === '/select-workspace'
    || value.startsWith('/select-workspace?')
  ) {
    return '/'
  }

  return value
}

export function loginPath(
  next: string,
) {
  return `/login?next=${encodeURIComponent(next)}`
}

export function workspaceSelectPath(
  next: string,
) {
  return (
    '/select-workspace?next='
    + encodeURIComponent(next)
  )
}
