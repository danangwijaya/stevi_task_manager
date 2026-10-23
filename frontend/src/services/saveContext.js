// Breadcrumbs of what the mapper did since the page loaded. Every save sends them (`ctx`) and the server stores them in
// the audit trail, so that when a polygon shows up twice the operations that led to it can be read back. Pure
// bookkeeping: it never throws and never changes what is saved.

const MAX_OPS = 12
const tab = Math.random().toString(36).slice(2, 8)       // tells two tabs of one mapper apart
const pageLoadedAt = Date.now()
let ops = []
let gridLoadedAt = pageLoadedAt
let gridId = null

// `op` is a short name ('undo', 'split_poly', ...); `info` holds a few small numbers or strings (counts, class ids)
export const noteOp = (op, info) => {
  try {
    const name = String(op).slice(0, 30)
    const last = ops[ops.length - 1]
    if (last && last.op === name) {                    // a run of the same operation (vertex edits) is one entry with a count
      last.n = (last.n || 1) + 1
      last.at = Date.now()
      return
    }
    ops.push({ op: name, at: Date.now(), ...(info && typeof info === 'object' ? info : {}) })
    if (ops.length > MAX_OPS) ops.shift()
  } catch (_) { /* breadcrumbs must never break an edit */ }
}

// A grid was (re)loaded from the server or restored from a local draft
export const markGridLoaded = (taskGridId, source = 'server') => {
  gridId = taskGridId
  gridLoadedAt = Date.now()
  ops = []
  noteOp(`load_${source}`)
}

// `extra`: facts known only at save time (feature count, how many have no database id, ...)
export const buildContext = (extra) => {
  try {
    const now = Date.now()
    return {
      tab,
      grid: gridId,
      loaded_s: Math.round((now - gridLoadedAt) / 1000),
      page_s: Math.round((now - pageLoadedAt) / 1000),
      ...(extra && typeof extra === 'object' ? extra : {}),
      ops: ops.map(({ at, ...rest }) => ({ ...rest, ago: Math.round((now - at) / 1000) })),
    }
  } catch (_) {
    return undefined
  }
}
