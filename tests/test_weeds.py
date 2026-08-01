# -*- coding: utf-8 -*-
"""Weed strategies: frame, grid (no slice keep), region (nested waste)."""
from __future__ import division

from enaml.qt.QtCore import QPointF, QRectF
from enaml.qt.QtGui import QPainterPath

from inkcut.core.svg import QtSvgDoc
from inkcut.core.utils import split_painter_path
from inkcut.job.models import Job
from inkcut.job.weeds import (
    closed_fill_union, frame_weeds, generate_weeds, grid_weeds, list_closed_subpaths,
    region_weeds,
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
    assert not f.isEmpty()
    assert not g.isEmpty()
    assert not r.isEmpty()


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
