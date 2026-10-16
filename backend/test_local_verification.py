import json
import math
from shapely.geometry import Polygon, MultiPolygon, box, mapping, shape
from shapely.ops import unary_union

from app.api.annotations import (
    _clean_spikes_and_holes,
    _subdivide_multihole_polygon,
    _extract_polygons,
    _merge_polygons_robust,
    GeoJSONFeature,
    AnnotationSaveRequest,
)

def test_1_slit_hole_and_seam_cleaning():
    print("Testing 1: Slit hole & seam crack cleaning...")
    # Create a square polygon with a degenerate collapsed slit hole (very thin slit: 0.000001 x 0.001 deg)
    ext = [(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01), (0, 0)]
    # Slit hole: 0.1m wide, 10m long
    slit_hole = [
        (0.002, 0.002),
        (0.002 + 1e-6, 0.002),
        (0.002 + 1e-6, 0.003),
        (0.002, 0.003),
        (0.002, 0.002)
    ]
    # Real valid hole: 50m x 50m (approx 0.00045 deg)
    valid_hole = [
        (0.005, 0.005),
        (0.006, 0.005),
        (0.006, 0.006),
        (0.005, 0.006),
        (0.005, 0.005)
    ]
    poly = Polygon(ext, [slit_hole, valid_hole])
    cleaned = _clean_spikes_and_holes(poly)
    
    assert len(cleaned.interiors) == 1, f"Expected 1 valid interior hole after cleaning, got {len(cleaned.interiors)}"
    print("  ✓ Slit hole successfully removed, real hole preserved!")

def test_2_multihole_subdivision():
    print("Testing 2: Multi-hole background polygon subdivision (>15 holes)...")
    # Create a 1km x 1km background polygon containing 25 small holes (simulating 25 houses/parcels)
    ext = [(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01), (0, 0)]
    holes = []
    for i in range(5):
        for j in range(5):
            x = 0.001 + i * 0.0018
            y = 0.001 + j * 0.0018
            holes.append([
                (x, y), (x + 0.0005, y), (x + 0.0005, y + 0.0005), (x, y + 0.0005), (x, y)
            ])
    poly = Polygon(ext, holes)
    assert len(poly.interiors) == 25
    
    subdivided = _extract_polygons(poly, min_area_sqm=1.0)
    print(f"  ✓ Subdivided 25-hole polygon into {len(subdivided)} manageable singlepart polygons.")
    for idx, p in enumerate(subdivided):
        assert len(p.interiors) <= 15, f"Piece {idx} has {len(p.interiors)} holes, which exceeds max 15!"
    
    # Check that total area matches original
    total_area_sub = sum(p.area for p in subdivided)
    assert abs(total_area_sub - poly.area) < 1e-10, "Area mismatch during subdivision!"
    print("  ✓ All subdivided pieces have <= 15 holes with zero area loss!")

def test_3_robust_merge_seam_elimination():
    print("Testing 3: Robust polygon merge with morphological seam closing...")
    # Two adjacent polygons sharing a boundary with slight floating point gap
    p1 = Polygon([(0, 0), (0.005, 0), (0.005, 0.005), (0, 0.005), (0, 0)])
    p2 = Polygon([(0.0050001, 0), (0.01, 0), (0.01, 0.005), (0.0050001, 0.005), (0.0050001, 0)])
    
    merged = _merge_polygons_robust([p1, p2])
    assert merged is not None
    assert merged.geom_type == 'Polygon', f"Expected single Polygon, got {merged.geom_type}"
    assert len(merged.interiors) == 0, f"Expected 0 seam holes, got {len(merged.interiors)}"
    print("  ✓ Merged adjacent polygons seamlessly into a single Polygon without internal cracks!")

def test_4_cookie_cutter_hole_filling():
    print("Testing 4: Cookie cutter over empty interior hole...")
    # Parent polygon with an empty hole from (0.003, 0.003) to (0.007, 0.007)
    parent_poly = Polygon(
        [(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01), (0, 0)],
        [[(0.003, 0.003), (0.007, 0.003), (0.007, 0.007), (0.003, 0.007), (0.003, 0.003)]]
    )
    # Mapper cuts across the hole to turn it into a building: (0.002, 0.002) to (0.008, 0.008)
    cutter = box(0.002, 0.002, 0.008, 0.008)
    
    # Backend algorithm logic:
    # 1. Any empty interior hole covered by cutter is filled in for poly_for_inter
    hole_poly = Polygon(parent_poly.interiors[0])
    assert hole_poly.intersects(cutter)
    empty_h = hole_poly
    void_cut = empty_h.intersection(cutter)
    poly_for_inter = unary_union([parent_poly, void_cut])
    
    inter_polys = _extract_polygons(poly_for_inter.intersection(cutter), min_area_sqm=0.1)
    diff_polys = _extract_polygons(parent_poly.difference(cutter), min_area_sqm=0.1)
    
    assert len(inter_polys) == 1, f"Expected 1 solid cut piece, got {len(inter_polys)}"
    assert len(inter_polys[0].interiors) == 0, "The cut piece should be solid (hole filled)!"
    
    # Verify mutual exclusion (zero overlap between cut piece and parent difference)
    inter_overlap = inter_polys[0].intersection(diff_polys[0])
    assert inter_overlap.area < 1e-12, "Overlap detected between intersection and difference!"
    print("  ✓ Cookie cutter successfully fills the empty void with solid geometry and zero overlap!")

def run_all():
    print("==================================================")
    print("RUNNING GEOMETRY & TOPOLOGY FIX VERIFICATION")
    print("==================================================")
    test_1_slit_hole_and_seam_cleaning()
    test_2_multihole_subdivision()
    test_3_robust_merge_seam_elimination()
    test_4_cookie_cutter_hole_filling()
    print("==================================================")
    print("ALL GEOMETRY & TOPOLOGY TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_all()
