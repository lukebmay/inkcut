# -*- coding: utf-8 -*-
"""Weed-line strategies: frame, grid (clipped), region (nesting + fan).

Assumptions (region / keep)
---------------------------
- Closed subpaths are cut outlines; interiors use Qt's fill rule.
- Nesting: a path is a child of another if its centroid is inside the other
  and its area is smaller (point-in-path).
- Waste for nested parents = parent fill minus union of direct children.
- Without nesting, waste is the padded work rect minus union of all fills
  (outer peel only). Open strokes never form keep interiors.
- Goal is peelable chunks, not min cut count.
"""
from __future__ import division

import math

from enaml.qt.QtCore import QPointF, QRectF
from enaml.qt.QtGui import QPainterPath

from inkcut.core.utils import split_painter_path


WEED_MODES = ('frame', 'grid', 'region')
DEFAULT_WEED_MODE = 'frame'
DEFAULT_GRID_SPACING = 25.0

# padding indices match job.models.Padding
_LEFT, _TOP, _RIGHT, _BOTTOM = 0, 1, 2, 3


def generate_weeds(keep_path,
                   mode=DEFAULT_WEED_MODE,
                   padding=None,
                   spacing=DEFAULT_GRID_SPACING):
    """Build a weed QPainterPath for keep geometry.

    Parameters
    ----------
    keep_path : QPainterPath
        Design cuts (blade-down geometry) to protect / nest against.
    mode : str
        ``frame`` | ``grid`` | ``region``.
    padding : sequence of 4 floats, optional
        Left, top, right, bottom pad around keep bbox.
    spacing : float
        Grid / region partition spacing (device units).
    """
    if keep_path is None or keep_path.isEmpty():
        return QPainterPath()
    mode = mode if mode in WEED_MODES else DEFAULT_WEED_MODE
    padding = _normalize_padding(padding)
    spacing = max(float(spacing or DEFAULT_GRID_SPACING), 1e-6)

    if mode == 'frame':
        return frame_weeds(keep_path, padding)
    if mode == 'grid':
        return grid_weeds(keep_path, padding, spacing)
    return region_weeds(keep_path, padding, spacing)


def frame_weeds(keep_path, padding=None):
    """Padded rectangle around keep bbox (legacy weedline)."""
    padding = _normalize_padding(padding)
    rect = _padded_rect(keep_path.boundingRect(), padding)
    out = QPainterPath()
    out.addRect(rect)
    return out


def grid_weeds(keep_path, padding=None, spacing=DEFAULT_GRID_SPACING):
    """Axis-aligned grid over padded bbox; omit parts inside keep fills."""
    padding = _normalize_padding(padding)
    spacing = max(float(spacing), 1e-6)
    work = _padded_rect(keep_path.boundingRect(), padding)
    keep_fill = closed_fill_union(keep_path)
    return _grid_in_region(work, keep_fill, spacing, invert_keep=True)


def region_weeds(keep_path, padding=None, spacing=DEFAULT_GRID_SPACING):
    """Nesting-aware weeds: fan to islands + grid-in-waste.

    Closed-path nesting via centroid containment. Waste for a parent with
    children is parent fill minus children. Fan rays connect islands to the
    outer waste; a coarse grid fills remaining waste. Falls back to frame
    when no closed paths exist.
    """
    padding = _normalize_padding(padding)
    spacing = max(float(spacing), 1e-6)
    closed = list_closed_subpaths(keep_path)
    if not closed:
        return frame_weeds(keep_path, padding)

    out = QPainterPath()
    # Always peel frame around the plot
    out.addPath(frame_weeds(keep_path, padding))

    nodes = _nest_closed_paths(closed)
    waste_regions = []
    roots = [n for n in nodes if n['parent'] is None]
    for node in nodes:
        children = node['children']
        if not children:
            continue
        waste = QPainterPath(node['path'])
        for ch in children:
            waste = waste.subtracted(ch['path'])
        if not waste.isEmpty():
            waste_regions.append((waste, children))

    if not waste_regions:
        # No nesting: outer waste only (grid in padded rect minus fills)
        work = _padded_rect(keep_path.boundingRect(), padding)
        keep_fill = closed_fill_union(keep_path)
        out.addPath(_grid_in_region(work, keep_fill, spacing, invert_keep=True))
        return out

    for waste, children in waste_regions:
        out.addPath(_fan_in_waste(waste, children))
        br = waste.boundingRect()
        out.addPath(_grid_in_region(br, waste, spacing, invert_keep=False))

    # Outer margin outside root fills still helps peel
    work = _padded_rect(keep_path.boundingRect(), padding)
    root_fill = QPainterPath()
    for r in roots:
        root_fill.addPath(r['path'])
    out.addPath(_grid_in_region(work, root_fill, spacing, invert_keep=True))
    return out


def list_closed_subpaths(path, tol=1e-4):
    """Return closed subpaths of *path* (start≈end, enough elements)."""
    result = []
    for sp in split_painter_path(path):
        if _subpath_is_closed(sp, tol=tol):
            result.append(sp)
    return result


def closed_fill_union(path):
    """Union of closed subpath fills (empty if none closed)."""
    union = QPainterPath()
    for sp in list_closed_subpaths(path):
        union.addPath(sp)
    return union


def _normalize_padding(padding):
    if not padding:
        return [0.0, 0.0, 0.0, 0.0]
    pad = list(padding)
    while len(pad) < 4:
        pad.append(0.0)
    return [float(pad[i]) for i in range(4)]


def _padded_rect(bbox, padding):
    x = bbox.x() - padding[_LEFT]
    y = bbox.y() - padding[_TOP]
    w = bbox.width() + padding[_LEFT] + padding[_RIGHT]
    h = bbox.height() + padding[_TOP] + padding[_BOTTOM]
    return QRectF(x, y, w, h)


def _subpath_is_closed(sp, tol=1e-4):
    n = sp.elementCount()
    if n < 3:
        return False
    e0 = sp.elementAt(0)
    eN = sp.elementAt(n - 1)
    return (abs(e0.x - eN.x) <= tol and abs(e0.y - eN.y) <= tol)


def _path_area(path):
    r = path.boundingRect()
    return abs(r.width() * r.height())


def _path_centroid(path):
    r = path.boundingRect()
    return QPointF(r.center())


def _nest_closed_paths(closed_paths):
    """Assign parent/children by containment of centroid + smaller area."""
    nodes = []
    for p in closed_paths:
        nodes.append({
            'path': p,
            'area': _path_area(p),
            'centroid': _path_centroid(p),
            'parent': None,
            'children': [],
        })
    # Smallest-area parent that contains centroid
    for i, child in enumerate(nodes):
        best = None
        best_area = None
        c = child['centroid']
        for j, parent in enumerate(nodes):
            if i == j:
                continue
            if parent['area'] <= child['area']:
                continue
            if not parent['path'].contains(c):
                continue
            if best is None or parent['area'] < best_area:
                best = parent
                best_area = parent['area']
        if best is not None:
            child['parent'] = best
            best['children'].append(child)
    return nodes


def _point_allowed(x, y, region_path, invert_keep):
    """If invert_keep, region is keep-fill (allow outside). Else allow inside."""
    inside = region_path.contains(QPointF(x, y))
    if region_path.isEmpty():
        return True
    return (not inside) if invert_keep else inside


def _clip_line_to_region(x0, y0, x1, y1, region_path, invert_keep,
                        samples=64, min_len=0.5):
    """Return list of (x0,y0,x1,y1) segments allowed by region test."""
    n = max(int(samples), 8)
    flags = []
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        pts.append((x, y))
        flags.append(_point_allowed(x, y, region_path, invert_keep))

    segs = []
    run = None
    for i, ok in enumerate(flags):
        if ok:
            if run is None:
                run = i
        else:
            if run is not None and i - 1 > run:
                xa, ya = pts[run]
                xb, yb = pts[i - 1]
                if math.hypot(xb - xa, yb - ya) >= min_len:
                    segs.append((xa, ya, xb, yb))
            run = None
    if run is not None and n > run:
        xa, ya = pts[run]
        xb, yb = pts[n]
        if math.hypot(xb - xa, yb - ya) >= min_len:
            segs.append((xa, ya, xb, yb))
    return segs


def _add_line_segs(out, segs):
    for x0, y0, x1, y1 in segs:
        out.moveTo(x0, y0)
        out.lineTo(x1, y1)


def _grid_in_region(rect, region_path, spacing, invert_keep):
    """Vertical + horizontal lines over rect, clipped by region test."""
    out = QPainterPath()
    if rect.width() <= 0 or rect.height() <= 0:
        return out
    spacing = max(float(spacing), 1e-6)
    x0, y0 = rect.left(), rect.top()
    x1, y1 = rect.right(), rect.bottom()

    x = x0
    # Include edges lightly inside so frame-adjacent lines appear
    while x <= x1 + 1e-9:
        segs = _clip_line_to_region(
            x, y0, x, y1, region_path, invert_keep=invert_keep)
        _add_line_segs(out, segs)
        x += spacing

    y = y0
    while y <= y1 + 1e-9:
        segs = _clip_line_to_region(
            x0, y, x1, y, region_path, invert_keep=invert_keep)
        _add_line_segs(out, segs)
        y += spacing
    return out


def _fan_in_waste(waste, child_nodes, rays=8):
    """Rays from each island centroid through waste to outer reach."""
    out = QPainterPath()
    if waste.isEmpty():
        return out
    br = waste.boundingRect()
    radius = math.hypot(br.width(), br.height()) + 1.0
    for ch in child_nodes:
        c = ch['centroid']
        cx, cy = c.x(), c.y()
        for k in range(rays):
            ang = (2.0 * math.pi * k) / float(rays)
            ex = cx + radius * math.cos(ang)
            ey = cy + radius * math.sin(ang)
            segs = _clip_line_to_region(
                cx, cy, ex, ey, waste, invert_keep=False, samples=96)
            _add_line_segs(out, segs)
    return out
