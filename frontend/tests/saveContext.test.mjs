import test from 'node:test'
import assert from 'node:assert/strict'
import { noteOp, markGridLoaded, buildContext } from '../src/services/saveContext.js'

test('the context lists the latest operations with their age and the extra facts of the save', () => {
  markGridLoaded(129, 'draft')
  noteOp('undo')
  noteOp('split_poly', { created: 2 })
  const ctx = buildContext({ features: 10, no_id: 3 })
  assert.equal(ctx.grid, 129)
  assert.equal(ctx.features, 10)
  assert.equal(ctx.no_id, 3)
  assert.deepEqual(ctx.ops.map((o) => o.op), ['load_draft', 'undo', 'split_poly'])
  assert.equal(ctx.ops[2].created, 2)
  assert.ok(ctx.ops.every((o) => typeof o.ago === 'number' && !('at' in o)))
})

test('loading a grid starts a fresh trail and only the last operations are kept', () => {
  markGridLoaded(5)
  for (let i = 0; i < 30; i++) noteOp(`op${i}`)
  const ctx = buildContext()
  assert.equal(ctx.ops.length, 12)
  assert.equal(ctx.ops[11].op, 'op29')
  markGridLoaded(6)
  assert.deepEqual(buildContext().ops.map((o) => o.op), ['load_server'])
})

test('breadcrumbs never throw, whatever they are given', () => {
  assert.doesNotThrow(() => noteOp(undefined, 'not an object'))
  assert.doesNotThrow(() => noteOp({ weird: true }, null))
  assert.ok(buildContext(null).tab)
})

test('a run of the same operation is one entry with a count, so vertex edits do not push the rest out', () => {
  markGridLoaded(7)
  noteOp('undo')
  for (let i = 0; i < 40; i++) noteOp('edit_vertices')
  const ops = buildContext().ops
  assert.deepEqual(ops.map((o) => o.op), ['load_server', 'undo', 'edit_vertices'])
  assert.equal(ops[2].n, 40)
})
