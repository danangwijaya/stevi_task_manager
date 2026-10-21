// Pure logic of the delta save (no Vue, no network): compare the features on screen with the baseline of what the
// server is known to hold, build the request, and fold the response back into the baseline.
//
// baseline: Map<id, { hash, version }>  hash = class + rounded geometry, version = row updated_at (null = unknown)

// Same precision as syncFeaturesFromMap, so data loaded from the server and data read back from the map hash alike.
export const roundCoords = (coords) => {
  if (!Array.isArray(coords)) return coords
  if (typeof coords[0] === 'number') return [Math.round(coords[0] * 1e6) / 1e6, Math.round(coords[1] * 1e6) / 1e6]
  return coords.map(roundCoords)
}

// 53-bit string hash (cyrb53): a collision would hide a real change, so 32 bits are not enough
const cyrb53 = (str, seed = 0) => {
  let h1 = 0xdeadbeef ^ seed
  let h2 = 0x41c6ce57 ^ seed
  for (let i = 0; i < str.length; i++) {
    const ch = str.charCodeAt(i)
    h1 = Math.imul(h1 ^ ch, 2654435761)
    h2 = Math.imul(h2 ^ ch, 1597334677)
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909)
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909)
  return 4294967296 * (2097151 & h2) + (h1 >>> 0)
}

export const featureHash = (f) =>
  `${f?.properties?.class_id ?? 0}:${cyrb53(JSON.stringify(roundCoords(f?.geometry?.coordinates)))}`

export const rawId = (f) => f?.id ?? f?.properties?.id

// database id as a number, or null when the feature has none yet
export const numericId = (f) => {
  const raw = rawId(f)
  if (typeof raw === 'number' && Number.isFinite(raw)) return raw
  if (typeof raw === 'string' && /^\d+$/.test(raw)) return Number(raw)
  return null
}

const clientUid = (f) => {
  const uid = f?._uiId || f?.properties?._uiId
  return uid ? String(uid) : null
}

export const buildBaseline = (features) => {
  const baseline = new Map()
  for (const f of features || []) {
    const id = numericId(f)
    if (id !== null) baseline.set(id, { hash: featureHash(f), version: f.properties?.version ?? null })
  }
  return baseline
}

// Returns { fallback: reason } when the delta cannot be computed safely (the caller then uses the full save),
// otherwise { upserts, deletes, sent, adopted } where `sent` remembers what was hashed at send time and `adopted`
// maps client_uid -> database id for polygons that lost their id on screen but are identical to a baseline polygon.
export const computeDelta = (features, baseline) => {
  if (!baseline) return { fallback: 'no-baseline' }
  if (!features.length && baseline.size) return { fallback: 'empty-features' }   // never turn "nothing on screen" into "delete all"
  const upserts = []
  const sent = []
  const seen = new Set()
  const fresh = []                    // polygons without a database id: inserted, unless they turn out to be an id-less copy
  for (const f of features) {
    const raw = rawId(f)
    const id = numericId(f)
    if (raw !== undefined && raw !== null && id === null) return { fallback: 'non-numeric-id' }   // legacy exploded multipart ids
    const hash = featureHash(f)
    if (id !== null) {
      seen.add(id)
      const b = baseline.get(id)
      if (b && b.hash === hash) continue
      upserts.push({ id, version: b ? b.version : null, geometry: f.geometry, properties: { class_id: f.properties?.class_id ?? 0 } })
      sent.push({ id, uid: null, hash, feature: f })
    } else {
      const uid = clientUid(f)
      if (!uid || uid.length > 64) return { fallback: 'no-client-uid' }
      fresh.push({ f, uid, hash })
    }
  }
  // A restored local draft (or any state rebuilt without ids) shows the same polygons again as "new" while the baseline
  // still holds them: delete + insert would only churn their ids. Hand each one its old id back instead.
  const unclaimed = new Map()         // hash -> baseline ids no longer on screen
  for (const [id, b] of baseline) {
    if (seen.has(id)) continue
    if (!unclaimed.has(b.hash)) unclaimed.set(b.hash, [])
    unclaimed.get(b.hash).push(id)
  }
  const adopted = {}
  for (const { f, uid, hash } of fresh) {
    const candidates = unclaimed.get(hash)
    if (candidates && candidates.length) {
      const id = candidates.shift()
      seen.add(id)
      adopted[uid] = id
      continue
    }
    upserts.push({ client_uid: uid, geometry: f.geometry, properties: { class_id: f.properties?.class_id ?? 0 } })
    sent.push({ id: null, uid, hash, feature: f })
  }
  const deletes = []
  for (const [id, b] of baseline) if (!seen.has(id)) deletes.push({ id, version: b.version })
  return { upserts, deletes, sent, adopted }
}

// Folds the server response into the baseline and the in-memory features. Returns what the view must apply.
export const applyResponse = (baseline, sent, data) => {
  const idMap = data.id_map || {}
  const versions = data.versions || {}
  const conflicts = data.conflicts || []
  const conflictIds = new Set(conflicts.map((c) => c.id))

  for (const s of sent) {
    if (s.uid && idMap[s.uid] !== undefined) {
      s.feature.id = idMap[s.uid]
      if (s.feature.properties) s.feature.properties.id = idMap[s.uid]
    }
    const id = s.id ?? idMap[s.uid]
    if (id === undefined || id === null || conflictIds.has(id)) continue        // rejected or in conflict
    baseline.set(id, { hash: s.hash, version: versions[String(id)] ?? null })
  }
  for (const id of data.deleted || []) baseline.delete(id)
  // server wins: the baseline becomes the server's version, the view replaces the local copy
  for (const c of conflicts) {
    baseline.set(c.id, { hash: featureHash(c.server_feature), version: c.server_feature?.properties?.version ?? null })
  }
  for (const ef of data.extra_features || []) {
    const id = numericId(ef)
    if (id !== null) baseline.set(id, { hash: featureHash(ef), version: ef.properties?.version ?? null })
  }
  return { idMap, conflicts, rejected: data.rejected || [], extraFeatures: data.extra_features || [] }
}

// Rows the server changed on our behalf (smart delete neighbours): same hash, unknown version (no false conflict later)
export const rebase = (baseline, features) => {
  for (const f of features || []) {
    const id = numericId(f)
    if (id !== null) baseline.set(id, { hash: featureHash(f), version: null })
  }
}
