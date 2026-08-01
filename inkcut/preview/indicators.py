# -*- coding: utf-8 -*-
"""Preview origin/feed indicators and plan layer paths (QPainterPath)."""
from enaml.qt.QtCore import QPointF
from enaml.qt.QtGui import QPainterPath

from inkcut.device.frame import feed_vector as frame_feed_vector


def path_last_point(path):
    """Last element position of path, or None if empty."""
    if path is None or path.elementCount() == 0:
        return None
    e = path.elementAt(path.elementCount() - 1)
    return QPointF(e.x, e.y)


def moves_to_lines(path):
    """Convert pen-up moveTo elements into visible travel lines."""
    out = QPainterPath()
    if path is None or path.elementCount() == 0:
        return out
    for i in range(path.elementCount()):
        e = path.elementAt(i)
        if e.isMoveTo():
            out.lineTo(e.x, e.y)
        else:
            out.moveTo(e.x, e.y)
    return out


def indicator_length(size, fraction=0.12, minimum=15.0, maximum=None):
    """Arrow/crosshair size from material/device (w, h)."""
    if size is None:
        w = h = 0.0
    elif hasattr(size, 'width'):
        w, h = float(size.width()), float(size.height())
    else:
        w, h = float(size[0]), float(size[1])
    base = max(w, h, 0.0)
    length = max(minimum, base * fraction)
    if maximum is not None:
        length = min(length, float(maximum))
    return length


def origin_crosshair_path(origin=None, arm=20.0):
    """Crosshair at machine origin (default 0,0)."""
    if origin is None:
        ox, oy = 0.0, 0.0
    else:
        ox, oy = float(origin.x()), float(origin.y())
    arm = float(arm)
    path = QPainterPath()
    path.moveTo(ox - arm, oy)
    path.lineTo(ox + arm, oy)
    path.moveTo(ox, oy - arm)
    path.lineTo(ox, oy + arm)
    # small diamond for the point
    d = arm * 0.2
    path.moveTo(ox, oy - d)
    path.lineTo(ox + d, oy)
    path.lineTo(ox, oy + d)
    path.lineTo(ox - d, oy)
    path.lineTo(ox, oy - d)
    return path


def feed_arrow_path(origin=None, direction=None, length=50.0, head=None):
    """Arrow from origin along unit feed direction (machine space)."""
    if origin is None:
        ox, oy = 0.0, 0.0
    else:
        ox, oy = float(origin.x()), float(origin.y())
    if direction is None:
        dx, dy = 0.0, -1.0
    else:
        dx, dy = float(direction.x()), float(direction.y())
    mag = (dx * dx + dy * dy) ** 0.5
    if mag < 1e-12:
        dx, dy = 0.0, -1.0
        mag = 1.0
    dx, dy = dx / mag, dy / mag
    length = float(length)
    if head is None:
        head = max(4.0, length * 0.2)
    else:
        head = float(head)

    ex, ey = ox + dx * length, oy + dy * length
    # unit perpendicular
    px, py = -dy, dx

    path = QPainterPath()
    path.moveTo(ox, oy)
    path.lineTo(ex, ey)
    # chevron head
    path.moveTo(ex - dx * head + px * head * 0.5,
                ey - dy * head + py * head * 0.5)
    path.lineTo(ex, ey)
    path.lineTo(ex - dx * head - px * head * 0.5,
                ey - dy * head - py * head * 0.5)
    return path


def epilogue_as_travel(plan, start=None):
    """Visible line(s) from last cut (or start) to each epilogue end."""
    out = QPainterPath()
    if plan is None:
        return out
    if start is None:
        start = path_last_point(plan.cuts())
    if start is None:
        start = QPointF(0.0, 0.0)
    cur = QPointF(start.x(), start.y())
    for seg in plan.segments:
        if seg.kind != 'epilogue':
            continue
        end = seg.meta.get('end') if seg.meta else None
        if end is None and seg.path and seg.path.elementCount():
            end = path_last_point(seg.path)
        if end is None:
            continue
        out.moveTo(cur)
        out.lineTo(end.x(), end.y())
        cur = QPointF(end.x(), end.y())
    return out


def resolve_feed_direction(plan=None, feed_axis=None, feed_sense=None):
    """Unit feed vector from plan or frame settings."""
    if plan is not None and plan.feed_vector is not None:
        return plan.feed_vector
    return frame_feed_vector(feed_axis, feed_sense)


def plan_layer_paths(plan=None, move_path=None, cut_path=None):
    """Named layer paths for preview; prefer plan segments when present."""
    layers = {
        'cut': QPainterPath(),
        'travel': QPainterPath(),
        'weed': QPainterPath(),
        'epilogue': QPainterPath(),
    }
    if plan is not None:
        cuts = plan.cuts()
        weeds = plan.weeds()
        travels = plan.travels()  # line geometry when typed travels present
        layers['cut'] = cuts
        layers['weed'] = weeds
        if travels is not None and not travels.isEmpty():
            layers['travel'] = travels
        else:
            # Fallback: dig moveTos out of monolithic cut path
            layers['travel'] = moves_to_lines(cuts)
        layers['epilogue'] = epilogue_as_travel(plan)
        return layers

    if cut_path is not None:
        layers['cut'] = cut_path
    if move_path is not None:
        layers['travel'] = move_path
    elif cut_path is not None:
        layers['travel'] = moves_to_lines(cut_path)
    return layers
