# Data repair scripts

Tools used to repair polygon data of single grids in production. They import the app (`app.db`, `app.api`), so run them
inside the backend container (or any environment with `PYTHONPATH=backend` and `DATABASE_URL` set):

```
docker cp backend/scripts/<script>.py geoai_backend:/tmp/<script>.py     # /tmp of the container is wiped by every rebuild
docker exec -e PYTHONPATH=/app geoai_backend python -W ignore /tmp/<script>.py <task_grid_id> [options]
```

Every script that writes is a **dry run by default**. Writing needs `--apply`, refuses to run when the mapper saved the grid less than
`--idle-min` minutes ago (default 30), takes a snapshot (`grid_snapshots`) first, and ends in one `commit`.

| script | what it does | options |
|---|---|---|
| `absorb_gaps.py` | closes gaps between polygons: small or thin gaps are absorbed by the neighbour sharing the longest boundary, big voids become one class-0 polygon each | `--apply --idle-min=N` |
| `dedupe_giants.py` | deletes stale copies of large polygons that were stacked on each other (IoU >= `--min-iou`, area >= `--min-ha`); the newest row (highest id) is kept | `--apply --idle-min=N --min-ha=10000 --min-iou=0.98` |
| `resolve_overlaps.py` | where two polygons overlap, the overlapping part is cut out of the larger one (the smaller wins); polygons that would split or turn invalid are skipped | `--apply --idle-min=N --min-m2=1` |
| `grid_health_sweep.py` | read-only sweep of many grids on a local copy: coverage, gaps, open holes, overlaps, duplicates | `<folder>` |

## Rules we work by

1. Take a fresh backup first: `pg_dump -Fc`, then `pg_restore -l` on the file to check it.
2. Read the dry run. Apply **one grid per command**.
3. Order on one grid: `dedupe_giants.py` (e.g. `--min-ha=100 --min-iou=0.9`), then `resolve_overlaps.py`, then `absorb_gaps.py`.
   Cutting overlaps before the stale copies are gone leaves hundreds of hectares overlapping.
4. Never write to a grid that is SUBMITTED or APPROVED, or to a grid whose mapper is active. A stale browser tab can overwrite the result.
5. After applying, measure again from the database (union area must not change for `resolve_overlaps.py`).
6. Class-0 polygons created by `absorb_gaps.py` are real unmapped voids: tell the mapper to classify them and to hard refresh.

## Exports for `grid_health_sweep.py`

```
COPY (select t.id, t.grid_code, t.year, t.status, coalesce(t.assigned_user_id,0), t.min_lon, t.min_lat, t.max_lon, t.max_lat
      from task_grids t where t.year in (2022,2025) and exists (select 1 from annotations a where a.task_grid_id=t.id) order by t.id)
  TO STDOUT WITH (FORMAT text, DELIMITER '|');                                   -- grids.txt
COPY (select a.id, a.task_grid_id, a.class_id, coalesce(a.user_id,0), a.created_at, a.updated_at, a.geom_geojson
      from annotations a join task_grids t on t.id=a.task_grid_id where t.year in (2022,2025) order by a.id)
  TO STDOUT WITH (FORMAT text, DELIMITER '|');                                   -- polys.txt
```
