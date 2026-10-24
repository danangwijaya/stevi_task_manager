// Tells an open tab that a newer build of the app has been deployed. Hashed assets are cached for a year and the page itself is
// only reloaded by the user, so a tab left open for days keeps running old code (old save logic included). The build writes
// /version.json (never cached by nginx); the tab compares it with the id baked into its own bundle.

export const versionState = { newVersion: false }          // read by the router guard

const POLL_MS = 60000

// `fetchFn` is injectable for tests. Returns true only when the server reports a build different from `current`.
export const checkOnce = async (current, fetchFn = fetch) => {
  try {
    const res = await fetchFn(`/version.json?t=${Date.now()}`, { cache: 'no-store' })
    if (!res.ok) return false
    const data = await res.json()
    return typeof data?.build === 'string' && data.build.length > 0 && data.build !== current
  } catch (_) {
    return false                                           // offline, dev server without the file, ...: say nothing
  }
}

export const startVersionCheck = (current, onNewVersion) => {
  let stopped = false
  const run = async () => {
    if (stopped || versionState.newVersion) return
    if (await checkOnce(current)) {
      versionState.newVersion = true
      onNewVersion()
    }
  }
  const timer = setInterval(run, POLL_MS)
  const onVisible = () => { if (document.visibilityState === 'visible') run() }
  document.addEventListener('visibilitychange', onVisible)
  run()
  return () => { stopped = true; clearInterval(timer); document.removeEventListener('visibilitychange', onVisible) }
}
