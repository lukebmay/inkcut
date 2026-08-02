# -*- coding: utf-8 -*-
"""Weed strategies: frame, grid (no slice keep), region (nested waste)."""
from __future__ import division

from enaml.qt.QtCore import QPointF, QRectF
from enaml.qt.QtGui import QPainterPath

from inkcut.core.svg import QtSvgDoc
from inkcut.core.utils import split_painter_path
from inkcut.job.models import Job
from inkcut.job.weeds import (
    auto_weeds, closed_fill_union, frame_weeds, generate_weeds, grid_weeds,
    list_closed_subpaths, region_weeds, weed_path_stats,
)


def _rect_path(x, y, w, h):
    p = QPainterPath()
    p.addRect(QRectF(x, y, w, h))
    return p


def _circle_path(cx, cy, r):
    p = QPainterPath()
    p.addEllipse(QPointF(cx, cy), r, r)
    return p


def _nested_circle_island():
    """Outer circle with inner rectangular island (keep)."""
    p = QPainterPath()
    p.addPath(_circle_path(50, 50, 40))
    p.addPath(_rect_path(40, 40, 20, 20))
    return p


def _sample_points_on_path(path, step=2):
    """Approximate samples along line segments of path."""
    pts = []
    if path.isEmpty():
        return pts
    x0 = y0 = None
    for i in range(path.elementCount()):
        e = path.elementAt(i)
        if e.isMoveTo():
            x0, y0 = e.x, e.y
            continue
        x1, y1 = e.x, e.y
        if x0 is None:
            x0, y0 = x1, y1
            continue
        dx, dy = x1 - x0, y1 - y0
        length = (dx * dx + dy * dy) ** 0.5
        n = max(int(length / step), 1)
        for k in range(n + 1):
            t = k / float(n)
            pts.append(QPointF(x0 + dx * t, y0 + dy * t))
        x0, y0 = x1, y1
    return pts


def _fraction_inside(weed, keep_fill, step=1.5):
    pts = _sample_points_on_path(weed, step=step)
    if not pts:
        return 0.0
    inside = sum(1 for p in pts if keep_fill.contains(p))
    return inside / float(len(pts))


def test_frame_weeds_padded_rect():
    keep = _rect_path(10, 20, 30, 40)
    weed = frame_weeds(keep, padding=[5, 5, 5, 5])
    assert not weed.isEmpty()
    br = weed.boundingRect()
    assert abs(br.x() - 5) < 1e-6
    assert abs(br.y() - 15) < 1e-6
    assert abs(br.width() - 40) < 1e-6
    assert abs(br.height() - 50) < 1e-6


def test_generate_weeds_modes():
    keep = _rect_path(0, 0, 50, 50)
    f = generate_weeds(keep, mode='frame', padding=[2, 2, 2, 2])
    g = generate_weeds(keep, mode='grid', padding=[2, 2, 2, 2], spacing=10)
    r = generate_weeds(keep, mode='region', padding=[2, 2, 2, 2], spacing=10)
    a = generate_weeds(keep, mode='auto', padding=[2, 2, 2, 2], spacing=20)
    assert not f.isEmpty()
    assert not g.isEmpty()
    assert not r.isEmpty()
    assert not a.isEmpty()


def test_grid_does_not_slice_keep_island():
    keep = _rect_path(20, 20, 40, 40)
    keep_fill = closed_fill_union(keep)
    weed = grid_weeds(keep, padding=[10, 10, 10, 10], spacing=8)
    assert not weed.isEmpty()
    # Weed samples should almost never sit deep inside the keep fill
    frac = _fraction_inside(weed, keep_fill, step=1.0)
    assert frac < 0.05, "grid weed sliced keep interior (frac=%s)" % frac


def test_region_weeds_nested_circle_island():
    keep = _nested_circle_island()
    closed = list_closed_subpaths(keep)
    assert len(closed) >= 2
    outer = closed[0]
    island = closed[1]
    # Ensure nesting geometry: island centroid in outer, not vice-versa area
    assert outer.contains(island.boundingRect().center())

    weed = region_weeds(keep, padding=[5, 5, 5, 5], spacing=12)
    assert not weed.isEmpty()

    # Waste ring point should see nearby weed activity in region mode
    waste = QPainterPath(outer).subtracted(island)
    assert waste.contains(QPointF(20, 50))

    # Island interior must not be sliced
    island_fill = QPainterPath(island)
    frac = _fraction_inside(weed, island_fill, step=1.0)
    assert frac < 0.08, "region weed sliced island (frac=%s)" % frac

    # At least some weed samples should land in the waste annulus
    pts = _sample_points_on_path(weed, step=2)
    in_waste = sum(1 for p in pts if waste.contains(p))
    assert in_waste > 0, "region weed never entered nested waste"


def test_job_plan_emits_weed_segment_frame():
    svg = '''<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">
  <rect x="10" y="10" width="80" height="30" fill="none" stroke="black"/>
</svg>'''
    doc = QtSvgDoc(svg)
    job = Job()
    job.doc = doc
    job.path = doc
    job.optimized_path = doc
    job.plot_weedline = True
    job.plot_weedline_padding = [10, 10, 10, 10]
    job.weed_mode = 'frame'
    job.feed_to_end = False

    plan = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y', epilogue='none')
    assert plan is not None
    kinds = [s.kind for s in plan.segments]
    assert 'cut' in kinds
    assert 'weed' in kinds
    weeds = plan.weeds()
    assert not weeds.isEmpty()
    assert plan.weeds().elementCount() > 0
    # Stream still includes weeds (blade-down)
    stream = plan.to_device_stream()
    assert stream.elementCount() >= plan.cuts().elementCount()


def test_job_plan_grid_mode_typed_weed():
    svg = '''<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80">
  <rect x="20" y="20" width="40" height="40" fill="none" stroke="black"/>
</svg>'''
    doc = QtSvgDoc(svg)
    job = Job()
    job.doc = doc
    job.path = doc
    job.optimized_path = doc
    job.plot_weedline = True
    job.weed_mode = 'grid'
    job.weed_grid_spacing = 15
    job.plot_weedline_padding = [10, 10, 10, 10]

    plan = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y', epilogue='return')
    weed_segs = [s for s in plan.segments if s.kind == 'weed']
    assert len(weed_segs) == 1
    assert weed_segs[0].meta.get('mode') == 'grid'
    # Epilogue after weeds
    assert plan.segments[-1].kind == 'epilogue'


def test_legacy_add_weedline_uses_frame():
    path = _rect_path(0, 0, 10, 10)
    job = Job()
    job._add_weedline(path, [1, 1, 1, 1])
    # Original path + frame rect
    assert path.boundingRect().width() >= 12


def _sharp_diamond():
    """Diamond with acute corners (delicate tips)."""
    p = QPainterPath()
    p.moveTo(50, 10)
    p.lineTo(70, 50)
    p.lineTo(50, 90)
    p.lineTo(30, 50)
    p.closeSubpath()
    return p


def test_auto_fewer_segments_than_dense_grid():
    keep = _rect_path(20, 20, 60, 40)
    pad = [15, 15, 15, 15]
    grid = grid_weeds(keep, padding=pad, spacing=8)
    auto = auto_weeds(keep, padding=pad, spacing=25, max_chunk=50)
    g = weed_path_stats(grid)
    a = weed_path_stats(auto)
    assert a['segments'] < g['segments'], (
        "auto should use fewer cuts than dense grid (%s vs %s)" % (
            a['segments'], g['segments']))


def test_auto_does_not_slice_keep():
    # Nested: outer is boundary, island is solid keep (annulus is waste).
    keep = _nested_circle_island()
    closed = list_closed_subpaths(keep)
    island_fill = QPainterPath(closed[1])
    weed = auto_weeds(keep, padding=[8, 8, 8, 8], spacing=20, max_chunk=40)
    assert not weed.isEmpty()
    frac = _fraction_inside(weed, island_fill, step=1.0)
    assert frac < 0.08, "auto weed sliced island keep (frac=%s)" % frac

    # Simple solid rect: weeds stay outside
    solid = _rect_path(20, 20, 40, 30)
    solid_fill = closed_fill_union(solid)
    weed2 = auto_weeds(solid, padding=[10, 10, 10, 10], spacing=20, max_chunk=40)
    frac2 = _fraction_inside(weed2, solid_fill, step=1.0)
    assert frac2 < 0.08, "auto weed sliced solid keep (frac=%s)" % frac2


def test_auto_pocket_release_enters_nested_waste():
    keep = _nested_circle_island()
    closed = list_closed_subpaths(keep)
    outer, island = closed[0], closed[1]
    waste = QPainterPath(outer).subtracted(island)
    weed = auto_weeds(keep, padding=[5, 5, 5, 5], spacing=20, max_chunk=40)
    pts = _sample_points_on_path(weed, step=1.5)
    in_waste = sum(1 for p in pts if waste.contains(p))
    assert in_waste > 0, "auto never released nested pocket waste"


def test_auto_delicate_emits_outward_from_sharp_corners():
    keep = _sharp_diamond()
    pad = [20, 20, 20, 20]
    weed = auto_weeds(
        keep, padding=pad, spacing=30, max_chunk=50,
        delicate_angle_deg=40.0)
    assert not weed.isEmpty()
    # Top tip at (50, 10): expect some weed sample outward (above or away)
    tip = QPointF(50, 10)
    pts = _sample_points_on_path(weed, step=1.0)
    near_outward = [
        p for p in pts
        if abs(p.x() - 50) < 8 and p.y() < 10 - 1.0
    ]
    # Also accept any relief starting near tip going outside keep
    keep_fill = closed_fill_union(keep)
    near_tip_outside = [
        p for p in pts
        if math_hypot(p, tip) < 25 and not keep_fill.contains(p)
    ]
    assert near_outward or near_tip_outside, (
        "auto produced no outward relief near diamond tip")


def math_hypot(p, q):
    return ((p.x() - q.x()) ** 2 + (p.y() - q.y()) ** 2) ** 0.5


def test_job_plan_auto_mode_typed_weed():
    svg = '''<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="80">
  <rect x="25" y="20" width="50" height="40" fill="none" stroke="black"/>
</svg>'''
    doc = QtSvgDoc(svg)
    job = Job()
    job.doc = doc
    job.path = doc
    job.optimized_path = doc
    job.plot_weedline = True
    job.weed_mode = 'auto'
    job.weed_grid_spacing = 20
    job.plot_weedline_padding = [12, 12, 12, 12]

    plan = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y', epilogue='none')
    weed_segs = [s for s in plan.segments if s.kind == 'weed']
    assert len(weed_segs) == 1
    assert weed_segs[0].meta.get('mode') == 'auto'
    assert not plan.weeds().isEmpty()
