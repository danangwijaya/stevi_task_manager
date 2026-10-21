import test from 'node:test'
import assert from 'node:assert/strict'
import { buildBaseline, computeDelta, applyResponse, featureHash, rebase, roundCoords } from '../src/services/deltaSave.js'

const sq = (x, size = 0.002) => ({ type: 'Polygon', coordinates: [[[x, 0], [x + size, 0], [x + size, size], [x, size], [x, 0]]] })
const served = (id, x, cls = 1, version = 'v' + id) => ({ type: 'Feature', id, geometry: sq(x), properties: { id, class_id: cls, version } })
const clone = (o) => JSON.parse(JSON.stringify(o))

test('a freshly loaded grid produces no changes (even after the map rounds the coordinates)', () => {
  const loaded = [served(1, 0.1234567891), served(2, 0.2)]               // server value has more than 6 decimals
  const baseline = buildBaseline(loaded)
  const onMap = clone(loaded).map((f) => ({ ...f, geometry: { ...f.geometry, coordinates: roundCoords(f.geometry.coordinates) } }))
  const d = computeDelta(onMap, baseline)
  assert.deepEqual([d.upserts.length, d.deletes.length], [0, 0])
})

test('only the edited polygon is sent, with the version the client knew', () => {
  const loaded = [served(1, 0.1), served(2, 0.2), served(3, 0.3)]
  const baseline = buildBaseline(loaded)
  const now = clone(loaded)
  now[1].properties.class_id = 5
  const d = computeDelta(now, baseline)
  assert.equal(d.upserts.length, 1)
  assert.deepEqual([d.upserts[0].id, d.upserts[0].version, d.upserts[0].properties.class_id], [2, 'v2', 5])
  assert.equal(d.deletes.length, 0)
})

test('a polygon removed from the screen becomes a named delete with its version', () => {
  const loaded = [served(1, 0.1), served(2, 0.2)]
  const d = computeDelta([clone(loaded[0])], buildBaseline(loaded))
  assert.deepEqual(d.deletes, [{ id: 2, version: 'v2' }])
})

test('a new polygon is keyed by its _uiId; the response gives it an id and the baseline follows', () => {
  const baseline = buildBaseline([served(1, 0.1)])
  const fresh = { type: 'Feature', _uiId: 'f_tmp_1_1', geometry: sq(0.5), properties: { class_id: 2 } }
  const d = computeDelta([served(1, 0.1), fresh], baseline)
  assert.equal(d.upserts.length, 1)
  assert.equal(d.upserts[0].client_uid, 'f_tmp_1_1')
  const out = applyResponse(baseline, d.sent, { id_map: { f_tmp_1_1: 77 }, versions: { 77: 'v77' }, deleted: [], conflicts: [] })
  assert.equal(fresh.id, 77)
  assert.deepEqual(baseline.get(77), { hash: featureHash(fresh), version: 'v77' })
  assert.deepEqual(computeDelta([served(1, 0.1), fresh], baseline).upserts, [])      // nothing left to send
  assert.equal(out.conflicts.length, 0)
})

test('re-sending after a lost response keeps the same client_uid (the server makes it idempotent)', () => {
  const baseline = buildBaseline([])
  const fresh = { type: 'Feature', _uiId: 'f_tmp_9_9', geometry: sq(0.5), properties: { class_id: 2 } }
  const first = computeDelta([fresh], baseline)
  const second = computeDelta([fresh], baseline)                                      // response never arrived: id still unknown
  assert.equal(first.upserts[0].client_uid, second.upserts[0].client_uid)
})

test('a conflict makes the server version the baseline and is returned for the view to apply', () => {
  const baseline = buildBaseline([served(1, 0.1)])
  const now = [served(1, 0.1, 9)]
  const d = computeDelta(now, baseline)
  const server = served(1, 0.1, 3, 'v-new')
  const out = applyResponse(baseline, d.sent, { id_map: {}, versions: {}, deleted: [], conflicts: [{ id: 1, reason: 'changed', server_feature: server }] })
  assert.equal(out.conflicts.length, 1)
  assert.deepEqual(baseline.get(1), { hash: featureHash(server), version: 'v-new' })
})

test('empty screen is never turned into "delete everything"', () => {
  assert.equal(computeDelta([], buildBaseline([served(1, 0.1)])).fallback, 'empty-features')
})

test('ids like 123_p2 (legacy multipart) and missing baseline fall back to the full save', () => {
  const baseline = buildBaseline([served(1, 0.1)])
  assert.equal(computeDelta([{ ...served(1, 0.1), id: '123_p2' }], baseline).fallback, 'non-numeric-id')
  assert.equal(computeDelta([served(1, 0.1)], undefined).fallback, 'no-baseline')
  assert.equal(computeDelta([{ type: 'Feature', geometry: sq(0.5), properties: {} }], baseline).fallback, 'no-client-uid')
})

test('rebase keeps the hash but drops the version so a later edit cannot raise a false conflict', () => {
  const baseline = buildBaseline([served(1, 0.1)])
  const moved = served(1, 0.15)
  rebase(baseline, [moved])
  assert.deepEqual(baseline.get(1), { hash: featureHash(moved), version: null })
  assert.equal(computeDelta([moved], baseline).upserts.length, 0)
})

const idless = (f, uid) => { const g = clone(f); g.id = null; g.properties.id = null; g._uiId = uid; return g }

test('polygons that lost their id but equal a baseline polygon get that id back instead of delete + insert', () => {
  // production case: a restored local draft showed 230 saved polygons without ids and the delta replaced all of them
  const loaded = [served(1, 0.1), served(2, 0.2), served(3, 0.3)]
  const d = computeDelta([idless(loaded[0], 'u1'), clone(loaded[1]), idless(loaded[2], 'u3')], buildBaseline(loaded))
  assert.deepEqual([d.upserts.length, d.deletes.length], [0, 0])
  assert.deepEqual(d.adopted, { u1: 1, u3: 3 })
})

test('an id-less polygon that really differs is still inserted, and its old row is deleted', () => {
  const loaded = [served(1, 0.1), served(2, 0.2)]
  const edited = idless(loaded[1], 'u2')
  edited.properties.class_id = 7
  const d = computeDelta([clone(loaded[0]), edited], buildBaseline(loaded))
  assert.deepEqual(d.adopted, {})
  assert.deepEqual(d.upserts.map((u) => u.client_uid), ['u2'])
  assert.deepEqual(d.deletes.map((x) => x.id), [2])
})

test('two identical id-less copies adopt one baseline id, the other is inserted', () => {
  const loaded = [served(1, 0.1)]
  const d = computeDelta([idless(loaded[0], 'a'), idless(loaded[0], 'b')], buildBaseline(loaded))
  assert.deepEqual(d.adopted, { a: 1 })
  assert.deepEqual(d.upserts.map((u) => u.client_uid), ['b'])
  assert.equal(d.deletes.length, 0)
})
