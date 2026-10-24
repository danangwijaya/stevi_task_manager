import test from 'node:test'
import assert from 'node:assert/strict'
import { checkOnce } from '../src/services/versionCheck.js'

const reply = (body, ok = true) => async () => ({ ok, json: async () => body })

test('a different build id on the server means a new version', async () => {
  assert.equal(await checkOnce('20261024100000', reply({ build: '20261024150000' })), true)
})

test('the same build id is not a new version', async () => {
  assert.equal(await checkOnce('20261024100000', reply({ build: '20261024100000' })), false)
})

test('a missing file, a broken answer or an offline tab say nothing', async () => {
  assert.equal(await checkOnce('x', reply({}, false)), false)                       // 404 (dev server)
  assert.equal(await checkOnce('x', reply({ build: '' })), false)
  assert.equal(await checkOnce('x', reply({ other: 1 })), false)
  assert.equal(await checkOnce('x', reply(null)), false)
  assert.equal(await checkOnce('x', async () => { throw new Error('offline') }), false)
})

test('the request is never served from a cache', async () => {
  let seen
  await checkOnce('x', async (url, opts) => { seen = { url, opts }; return { ok: true, json: async () => ({ build: 'x' }) } })
  assert.match(seen.url, /^\/version\.json\?t=\d+$/)
  assert.equal(seen.opts.cache, 'no-store')
})
