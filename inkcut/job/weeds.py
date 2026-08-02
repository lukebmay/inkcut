# -*- coding: utf-8 -*-
"""Weed-line strategies: frame, grid, region, auto peel.

Assumptions (region / auto / keep)
---------------------------------
- Closed subpaths are cut outlines; interiors use Qt's fill rule.
- Nesting: a path is a child of another if its centroid is inside the other
  and its area is smaller (point-in-path).
- Waste for nested parents = parent fill minus union of direct children.
- Without nesting, waste is the padded work rect minus union of all fills
  (outer peel only). Open strokes never form keep interiors.
- ``auto`` optimizes peel quality for adhesive vinyl: few smooth cuts,
  pocket release, outward delicate reliefs, selective bridges, long strips.
"""
from __future__ import division

import math

from enaml.qt.QtCore import QPointF, QRectF
from enaml.qt.QtGui import QPainterPath, QTransform

from inkcut.core.utils import split_painter_path


WEED_MODES = ('frame', 'grid', 'region', 'auto')
DEFAULT_WEED_MODE = 'frame'
DEFAULT_GRID_SPACING = 25.0

# Auto peel defaults (device units; mm-scale when job units are mm)
DEFAULT_MAX_CHUNK = 60.0
DEFAULT_BRIDGE_WIDTH = 4.0
DEFAULT_CLEARANCE = 0.5
DEFAULT_MIN_CUT = 2.0
DEFAULT_DELICATE_ANGLE_DEG = 55.0  # exterior turn sharper than this → relief

# padding indices match job.models.Padding
_LEFT, _TOP, _RIGHT, _BOTTOM = 0, 1, 2, 3


def generate_weeds(keep_path,
                   mode=DEFAULT_WEED_MODE,
                   padding=None,
                   spacing=DEFAULT_GRID_SPACING,
                   max_chunk=None,
                   bridge_width=None,
                   clearance=None,
                   min_cut=None,
                   delicate_angle_deg=None):
    """Build a weed QPainterPath for keep geometry.

    Parameters
    ----------
    keep_path : QPainterPath
        Design cuts (blade-down geometry) to protect / nest against.
    mode : str
        ``frame`` | ``grid`` | ``region`` | ``auto``.
    padding : sequence of 4 floats, optional
        Left, top, right, bottom pad around keep bbox.
    spacing : float
        Grid / region / auto strip spacing (device units).
    max_chunk, bridge_width, clearance, min_cut, delicate_angle_deg
        Auto-mode physical knobs (ignored by other modes).
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
    if mode == 'region':
        return region_weeds(keep_path, padding, spacing)
    return auto_weeds(
        keep_path,
        padding=padding,
        spacing=spacing,
        max_chunk=max_chunk,
        bridge_width=bridge_width,
        clearance=clearance,
        min_cut=min_cut,
        delicate_angle_deg=delicate_angle_deg,
    )


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


def auto_weeds(keep_path,
               padding=None,
               spacing=DEFAULT_GRID_SPACING,
               max_chunk=None,
               bridge_width=None,
               clearance=None,
               min_cut=None,
               delicate_angle_deg=None):
    """First-pass adhesive peel weeds: few smooth strategic cuts.

    Stages (all waste-only, straight segments preferred):
    1. Outer frame
    2. Pocket release (nested hole → outer waste)
    3. Delicate corner outward reliefs
    4. Selective bridge cuts between close keep bodies
    5. Sparse long strips on oversized outer waste (not dense grid)
    """
    padding = _normalize_padding(padding)
    spacing = max(float(spacing or DEFAULT_GRID_SPACING), 1e-6)
    max_chunk = float(max_chunk if max_chunk is not None else DEFAULT_MAX_CHUNK)
    max_chunk = max(max_chunk, spacing)
    bridge_width = float(
        bridge_width if bridge_width is not None else DEFAULT_BRIDGE_WIDTH)
    clearance = float(clearance if clearance is not None else DEFAULT_CLEARANCE)
    min_cut = float(min_cut if min_cut is not None else DEFAULT_MIN_CUT)
    delicate_angle = float(
        delicate_angle_deg if delicate_angle_deg is not None
        else DEFAULT_DELICATE_ANGLE_DEG)

    closed = list_closed_subpaths(keep_path)
    out = QPainterPath()
    out.addPath(frame_weeds(keep_path, padding))
    work = _padded_rect(keep_path.boundingRect(), padding)

    if not closed:
        # Open strokes only: frame + sparse outer strips on padded rect
        out.addPath(_sparse_strips_in_rect(
            work, keep_path, spacing, max_chunk, invert_keep=True,
            min_cut=min_cut))
        return out

    nodes = _nest_closed_paths(closed)
    # Solid keep = leaf islands + root shapes with no children.
    # Nested parents are outer boundaries; parent−children is waste (peel).
    keep_solid = _solid_keep_from_nodes(nodes)
    if keep_solid.isEmpty():
        keep_solid = closed_fill_union(keep_path)
    if clearance > 1e-9:
        keep_guard = _offset_path_approx(keep_solid, clearance)
    else:
        keep_guard = keep_solid

    # --- pocket release: parent waste annuli / children ---
    for node in nodes:
        if not node['children']:
            continue
        waste = QPainterPath(node['path'])
        for ch in node['children']:
            waste = waste.subtracted(ch['path'])
        if waste.isEmpty():
            continue
        for ch in node['children']:
            out.addPath(_pocket_release_cut(
                ch['path'], waste, keep_guard, min_cut=min_cut))

    # --- delicate outward reliefs on solid keep outlines only ---
    for node in nodes:
        if node['children']:
            # Outer boundary: relief into *outer* margin, not into pocket
            out.addPath(_delicate_outward_reliefs(
                node['path'], work, keep_guard,
                angle_deg=delicate_angle, min_cut=min_cut, max_len=max_chunk,
                prefer_outside_bbox=True))
        else:
            out.addPath(_delicate_outward_reliefs(
                node['path'], work, keep_guard,
                angle_deg=delicate_angle, min_cut=min_cut, max_len=max_chunk))

    # --- bridges between solid keep bodies (leaves + solid roots) ---
    solid_nodes = [n for n in nodes if not n['children']]
    if len(solid_nodes) >= 2:
        out.addPath(_bridge_cuts(
            [b['path'] for b in solid_nodes], keep_guard, bridge_width,
            min_cut=min_cut))

    # --- sparse long strips on outer waste (outside all root outlines) ---
    roots = [n for n in nodes if n['parent'] is None]
    outer_block = QPainterPath()
    for r in roots:
        outer_block = (
            QPainterPath(r['path']) if outer_block.isEmpty()
            else outer_block.united(r['path']))
    if outer_block.isEmpty():
        outer_block = keep_solid
    out.addPath(_sparse_strips_in_rect(
        work, outer_block, spacing, max_chunk, invert_keep=True,
        min_cut=min_cut))

    # Nested waste pockets: sparse strips if still large
    for node in nodes:
        if not node['children']:
            continue
        waste = QPainterPath(node['path'])
        for ch in node['children']:
            waste = waste.subtracted(ch['path'])
        if waste.isEmpty():
            continue
        br = waste.boundingRect()
        if max(br.width(), br.height()) > max_chunk:
            out.addPath(_sparse_strips_in_rect(
                br, waste, spacing, max_chunk, invert_keep=False,
                min_cut=min_cut))

    return out


def _solid_keep_from_nodes(nodes):
    """Vinyl that must stay: leaf islands and un-nested root shapes."""
    solid = QPainterPath()
    for n in nodes:
        if n['children']:
            continue
        if solid.isEmpty():
            solid = QPainterPath(n['path'])
        else:
            solid = solid.united(n['path'])
    return solid


def list_closed_subpaths(path, tol=1e-4):
    """Return closed subpaths of *path* (start≈end, enough elements)."""
    result = []
    for sp in split_painter_path(path):
        if _subpath_is_closed(sp, tol=tol):
            result.append(sp)
    return result


def closed_fill_union(path):
    """Solid union of closed subpath fills (islands stay keep, not holes)."""
    union = QPainterPath()
    for sp in list_closed_subpaths(path):
        if union.isEmpty():
            union = QPainterPath(sp)
        else:
            union = union.united(sp)
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


# ---------------------------------------------------------------------------
# Auto peel helpers
# ---------------------------------------------------------------------------


def _path_length(path):
    """Sum of polyline segment lengths (approx for curves)."""
    total = 0.0
    x0 = y0 = None
    for i in range(path.elementCount()):
        e = path.elementAt(i)
        if e.isMoveTo():
            x0, y0 = e.x, e.y
            continue
        if x0 is None:
            x0, y0 = e.x, e.y
            continue
        total += math.hypot(e.x - x0, e.y - y0)
        x0, y0 = e.x, e.y
    return total


def _offset_path_approx(path, delta):
    """Approximate outward offset via scale about center (cheap first pass)."""
    if path is None or path.isEmpty() or abs(delta) < 1e-12:
        return QPainterPath(path) if path is not None else QPainterPath()
    br = path.boundingRect()
    if br.width() < 1e-9 or br.height() < 1e-9:
        return QPainterPath(path)
    cx, cy = br.center().x(), br.center().y()
    # Expand each axis by ~delta on each side
    sx = (br.width() + 2.0 * delta) / br.width()
    sy = (br.height() + 2.0 * delta) / br.height()
    t = QTransform()
    t.translate(cx, cy)
    t.scale(sx, sy)
    t.translate(-cx, -cy)
    return t.map(path)


def _polyline_points(path, max_pts=256):
    """Sample vertices from path elements (move/line; curves as end points)."""
    pts = []
    for i in range(path.elementCount()):
        e = path.elementAt(i)
        pts.append(QPointF(e.x, e.y))
    if len(pts) <= max_pts:
        return pts
    # Decimate
    step = max(len(pts) // max_pts, 1)
    return pts[::step]


def _angle_turn_deg(p0, p1, p2):
    """Exterior turn angle at p1 in degrees (0 = straight, 180 = reverse)."""
    v1x, v1y = p0.x() - p1.x(), p0.y() - p1.y()
    v2x, v2y = p2.x() - p1.x(), p2.y() - p1.y()
    n1 = math.hypot(v1x, v1y)
    n2 = math.hypot(v2x, v2y)
    if n1 < 1e-12 or n2 < 1e-12:
        return 0.0
    v1x, v1y = v1x / n1, v1y / n1
    v2x, v2y = v2x / n2, v2y / n2
    # Interior angle between -incoming and outgoing
    dot = max(-1.0, min(1.0, v1x * v2x + v1y * v2y))
    interior = math.degrees(math.acos(dot))
    # Turn amount: how sharp (180 - interior for exterior corner sharpness)
    return 180.0 - interior


def _outward_normal_at_corner(p0, p1, p2, keep_path):
    """Unit direction from corner into waste (away from keep interior)."""
    # Bisector of angle at p1, pick the side outside keep
    v1x, v1y = p0.x() - p1.x(), p0.y() - p1.y()
    v2x, v2y = p2.x() - p1.x(), p2.y() - p1.y()
    n1 = math.hypot(v1x, v1y) or 1.0
    n2 = math.hypot(v2x, v2y) or 1.0
    v1x, v1y = v1x / n1, v1y / n1
    v2x, v2y = v2x / n2, v2y / n2
    bx, by = v1x + v2x, v1y + v2y
    bn = math.hypot(bx, by)
    if bn < 1e-9:
        # 180°: use perpendicular to edge
        bx, by = -v1y, v1x
        bn = 1.0
    bx, by = bx / bn, by / bn
    # Probe both ways
    probe = 2.0
    a = QPointF(p1.x() + bx * probe, p1.y() + by * probe)
    b = QPointF(p1.x() - bx * probe, p1.y() - by * probe)
    a_in = keep_path.contains(a)
    b_in = keep_path.contains(b)
    if a_in and not b_in:
        return -bx, -by
    if b_in and not a_in:
        return bx, by
    # Prefer direction away from path centroid
    c = _path_centroid(keep_path)
    to_c_x, to_c_y = c.x() - p1.x(), c.y() - p1.y()
    if bx * to_c_x + by * to_c_y > 0:
        return -bx, -by
    return bx, by


def _longest_waste_segment(x0, y0, x1, y1, keep_guard, min_cut, samples=64):
    """Longest subsegment of the ray that stays outside keep_guard."""
    segs = _clip_line_to_region(
        x0, y0, x1, y1, keep_guard, invert_keep=True,
        samples=samples, min_len=min_cut)
    if not segs:
        return None
    best = None
    best_len = -1.0
    for s in segs:
        ln = math.hypot(s[2] - s[0], s[3] - s[1])
        if ln > best_len:
            best_len = ln
            best = s
    return best


def _add_seg(out, seg, min_cut):
    if seg is None:
        return
    x0, y0, x1, y1 = seg
    if math.hypot(x1 - x0, y1 - y0) < min_cut:
        return
    out.moveTo(x0, y0)
    out.lineTo(x1, y1)


def _pocket_release_cut(island_path, waste, keep_guard, min_cut=DEFAULT_MIN_CUT):
    """One smooth cut from island toward outer waste through the pocket."""
    out = QPainterPath()
    if island_path is None or waste is None or waste.isEmpty():
        return out
    c = _path_centroid(island_path)
    wbr = waste.boundingRect()
    # Aim toward nearest outer waste bbox edge from island center
    cx, cy = c.x(), c.y()
    candidates = [
        (wbr.left() - 1.0, cy),
        (wbr.right() + 1.0, cy),
        (cx, wbr.top() - 1.0),
        (cx, wbr.bottom() + 1.0),
    ]
    best_seg = None
    best_score = -1.0
    for ex, ey in candidates:
        # Start just outside island toward target
        dx, dy = ex - cx, ey - cy
        mag = math.hypot(dx, dy) or 1.0
        dx, dy = dx / mag, dy / mag
        # Walk from island edge approx: center → target, clip to waste
        segs = _clip_line_to_region(
            cx, cy, ex, ey, waste, invert_keep=False,
            samples=80, min_len=min_cut)
        for s in segs:
            # Prefer segments that also avoid keep_guard interior
            mid = QPointF(0.5 * (s[0] + s[2]), 0.5 * (s[1] + s[3]))
            if keep_guard.contains(mid):
                continue
            ln = math.hypot(s[2] - s[0], s[3] - s[1])
            # Prefer cuts that run farther from island center (escape)
            end_d = math.hypot(s[2] - cx, s[3] - cy)
            score = ln + 0.25 * end_d
            if score > best_score:
                best_score = score
                best_seg = s
    _add_seg(out, best_seg, min_cut)
    # Fallback: any ray through waste from centroid
    if out.isEmpty():
        radius = math.hypot(wbr.width(), wbr.height()) + 2.0
        for k in range(8):
            ang = (2.0 * math.pi * k) / 8.0
            ex = cx + radius * math.cos(ang)
            ey = cy + radius * math.sin(ang)
            segs = _clip_line_to_region(
                cx, cy, ex, ey, waste, invert_keep=False,
                samples=80, min_len=min_cut)
            if segs:
                _add_seg(out, segs[0], min_cut)
                break
    return out


def _delicate_outward_reliefs(keep_path, work_rect, keep_guard,
                             angle_deg=DEFAULT_DELICATE_ANGLE_DEG,
                             min_cut=DEFAULT_MIN_CUT,
                             max_len=DEFAULT_MAX_CHUNK,
                             max_reliefs=12,
                             prefer_outside_bbox=False):
    """Straight reliefs from sharp keep corners outward into waste."""
    out = QPainterPath()
    pts = _polyline_points(keep_path)
    n = len(pts)
    if n < 3:
        return out
    # Close ring if needed
    if math.hypot(pts[0].x() - pts[-1].x(), pts[0].y() - pts[-1].y()) > 1e-6:
        pts = pts + [pts[0]]
        n = len(pts)

    corners = []
    for i in range(1, n - 1):
        turn = _angle_turn_deg(pts[i - 1], pts[i], pts[i + 1])
        if turn >= angle_deg:
            corners.append((turn, i, pts[i], pts[i - 1], pts[i + 1]))
    # Also check wrap at start if closed
    if n >= 4:
        turn = _angle_turn_deg(pts[-2], pts[0], pts[1])
        if turn >= angle_deg:
            corners.append((turn, 0, pts[0], pts[-2], pts[1]))

    # Sharpest first; cap count
    corners.sort(key=lambda t: -t[0])
    used = []
    radius = max(work_rect.width(), work_rect.height()) + 2.0
    max_len = max(float(max_len), min_cut)
    kbr = keep_path.boundingRect()

    for turn, idx, p1, p0, p2 in corners:
        if len(used) >= max_reliefs:
            break
        # Skip corners clustered near an already-used relief
        if any(math.hypot(p1.x() - u.x(), p1.y() - u.y()) < min_cut * 3
               for u in used):
            continue
        dx, dy = _outward_normal_at_corner(p0, p1, p2, keep_path)
        if prefer_outside_bbox:
            # Force direction away from shape center (outer margin)
            c = kbr.center()
            ox, oy = p1.x() - c.x(), p1.y() - c.y()
            on = math.hypot(ox, oy) or 1.0
            dx, dy = ox / on, oy / on
        ex = p1.x() + dx * radius
        ey = p1.y() + dy * radius
        # Start slightly outside keep
        sx = p1.x() + dx * max(clearance_default(), min_cut * 0.25)
        sy = p1.y() + dy * max(clearance_default(), min_cut * 0.25)
        seg = _longest_waste_segment(
            sx, sy, ex, ey, keep_guard, min_cut, samples=96)
        if seg is None:
            continue
        # Cap length
        x0, y0, x1, y1 = seg
        ln = math.hypot(x1 - x0, y1 - y0)
        if ln > max_len:
            t = max_len / ln
            x1 = x0 + (x1 - x0) * t
            y1 = y0 + (y1 - y0) * t
            seg = (x0, y0, x1, y1)
        mid = QPointF(0.5 * (seg[0] + seg[2]), 0.5 * (seg[1] + seg[3]))
        if keep_guard.contains(mid):
            continue
        _add_seg(out, seg, min_cut)
        used.append(p1)
    return out


def clearance_default():
    return DEFAULT_CLEARANCE


def _bridge_cuts(keep_paths, keep_guard, bridge_width, min_cut=DEFAULT_MIN_CUT):
    """Straight cuts between nearby keep bodies through the gap."""
    out = QPainterPath()
    n = len(keep_paths)
    if n < 2:
        return out
    bridge_width = max(float(bridge_width), min_cut)
    # Limit pairs for first pass
    max_pairs = 24
    pairs = []
    for i in range(n):
        bi = keep_paths[i].boundingRect()
        ci = bi.center()
        for j in range(i + 1, n):
            bj = keep_paths[j].boundingRect()
            cj = bj.center()
            # Approximate gap: center distance minus half extents along line
            dx, dy = cj.x() - ci.x(), cj.y() - ci.y()
            dist = math.hypot(dx, dy)
            if dist < 1e-9:
                continue
            # Rough gap estimate
            ri = 0.5 * min(bi.width(), bi.height())
            rj = 0.5 * min(bj.width(), bj.height())
            gap = dist - ri - rj
            if 0 < gap <= bridge_width * 2.5:
                pairs.append((gap, i, j, ci, cj, dx / dist, dy / dist))
    pairs.sort(key=lambda t: t[0])
    for gap, i, j, ci, cj, ux, uy in pairs[:max_pairs]:
        # Line between centers; take middle portion outside both keeps
        segs = _clip_line_to_region(
            ci.x(), ci.y(), cj.x(), cj.y(), keep_guard,
            invert_keep=True, samples=48, min_len=min_cut)
        if not segs:
            continue
        # Pick segment nearest midpoint
        mx, my = 0.5 * (ci.x() + cj.x()), 0.5 * (ci.y() + cj.y())
        best = min(
            segs,
            key=lambda s: math.hypot(
                0.5 * (s[0] + s[2]) - mx, 0.5 * (s[1] + s[3]) - my))
        # Cap to roughly bridge_width * 2 length centered
        x0, y0, x1, y1 = best
        ln = math.hypot(x1 - x0, y1 - y0)
        max_bridge_len = bridge_width * 3.0
        if ln > max_bridge_len:
            cxm, cym = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
            hx, hy = (x1 - x0) / ln, (y1 - y0) / ln
            half = 0.5 * max_bridge_len
            best = (cxm - hx * half, cym - hy * half,
                    cxm + hx * half, cym + hy * half)
        _add_seg(out, best, min_cut)
    return out


def _sparse_strips_in_rect(rect, region_path, spacing, max_chunk,
                           invert_keep, min_cut=DEFAULT_MIN_CUT):
    """Few long axis-aligned strips — not a full dense grid.

    Uses spacing as preferred strip pitch, but only emits lines when the
    component span exceeds max_chunk (or always a single mid-line if large).
    """
    out = QPainterPath()
    if isinstance(rect, QRectF):
        x0, y0, x1, y1 = rect.left(), rect.top(), rect.right(), rect.bottom()
        w, h = rect.width(), rect.height()
    else:
        # QPainterPath waste region
        br = rect if isinstance(rect, QRectF) else region_path.boundingRect()
        x0, y0, x1, y1 = br.left(), br.top(), br.right(), br.bottom()
        w, h = br.width(), br.height()

    if w <= 0 or h <= 0:
        return out

    spacing = max(float(spacing), 1e-6)
    max_chunk = max(float(max_chunk), spacing)
    # How many strips needed so pieces ≤ max_chunk
    # Prefer cutting along the long axis with lines perpendicular to it
    if w >= h:
        # Vertical strip cuts (split width)
        n_needed = max(int(math.ceil(w / max_chunk)) - 1, 0)
        # Cap density: at most one line per spacing
        n_max = max(int(math.floor(w / spacing)) - 1, 0)
        n = min(n_needed, n_max) if n_max else n_needed
        n = min(n, 8)  # hard cap for first pass
        if n <= 0 and w > max_chunk:
            n = 1
        if n <= 0:
            return out
        for i in range(1, n + 1):
            x = x0 + w * i / float(n + 1)
            segs = _clip_line_to_region(
                x, y0, x, y1, region_path, invert_keep=invert_keep,
                samples=64, min_len=min_cut)
            _add_line_segs(out, segs)
    else:
        n_needed = max(int(math.ceil(h / max_chunk)) - 1, 0)
        n_max = max(int(math.floor(h / spacing)) - 1, 0)
        n = min(n_needed, n_max) if n_max else n_needed
        n = min(n, 8)
        if n <= 0 and h > max_chunk:
            n = 1
        if n <= 0:
            return out
        for i in range(1, n + 1):
            y = y0 + h * i / float(n + 1)
            segs = _clip_line_to_region(
                x0, y, x1, y, region_path, invert_keep=invert_keep,
                samples=64, min_len=min_cut)
            _add_line_segs(out, segs)
    return out


def weed_path_stats(path):
    """Debug/metrics: segment count and total length."""
    segs = 0
    length = 0.0
    x0 = y0 = None
    for i in range(path.elementCount() if path is not None else 0):
        e = path.elementAt(i)
        if e.isMoveTo():
            x0, y0 = e.x, e.y
            continue
        if x0 is not None:
            length += math.hypot(e.x - x0, e.y - y0)
            segs += 1
        x0, y0 = e.x, e.y
    return {'segments': segs, 'length': length}
