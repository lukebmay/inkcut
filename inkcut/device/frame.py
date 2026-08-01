# -*- coding: utf-8 -*-
"""Physical machine frame (origin corner, feed axis/sense).

Protocol (swap_xy / mirrors / scale / rotation) is applied later by
Device.protocol_transform / Device.init — not here.
"""
from enaml.qt.QtCore import QPointF, QRectF
from enaml.qt.QtGui import QTransform


ORIGIN_CORNERS = ('bottom_left', 'bottom_right', 'top_left', 'top_right')
FEED_AXES = ('x', 'y')
FEED_SENSES = ('positive', 'negative')

# Stock bottom_left + y feed-after was toward -Y in machine space.
DEFAULT_ORIGIN_CORNER = 'bottom_left'
DEFAULT_FEED_AXIS = 'y'
DEFAULT_FEED_SENSE = 'negative'


def normalize_origin_corner(origin_corner=None, origin_position=None):
    """Prefer origin_corner; accept legacy origin_position."""
    corner = origin_corner if origin_corner is not None else origin_position
    if corner is None:
        return DEFAULT_ORIGIN_CORNER
    if corner not in ORIGIN_CORNERS:
        raise ValueError("invalid origin corner: %r" % (corner,))
    return corner


def normalize_feed_axis(feed_axis=None):
    if feed_axis is None:
        return DEFAULT_FEED_AXIS
    if feed_axis not in FEED_AXES:
        raise ValueError("invalid feed_axis: %r" % (feed_axis,))
    return feed_axis


def normalize_feed_sense(feed_sense=None):
    if feed_sense is None:
        return DEFAULT_FEED_SENSE
    if feed_sense not in FEED_SENSES:
        raise ValueError("invalid feed_sense: %r" % (feed_sense,))
    return feed_sense


def corner_point(bbox, origin_corner):
    """Corner of bbox that maps to machine (0, 0)."""
    origin_corner = normalize_origin_corner(origin_corner)
    if origin_corner == 'bottom_left':
        return bbox.bottomLeft()
    if origin_corner == 'bottom_right':
        return bbox.bottomRight()
    if origin_corner == 'top_left':
        return bbox.topLeft()
    return bbox.topRight()


def origin_shift(bbox, origin_corner):
    """(dx, dy) so origin_corner of bbox lands at (0, 0)."""
    p = corner_point(bbox, origin_corner)
    return -p.x(), -p.y()


def design_to_machine_transform(bbox, origin_corner, dx=0.0, dy=0.0):
    """Map design bbox into machine frame (origin at chosen corner + offset)."""
    ox, oy = origin_shift(bbox, origin_corner)
    return QTransform.fromTranslate(ox + dx, oy + dy)


def feed_sign(feed_sense):
    feed_sense = normalize_feed_sense(feed_sense)
    return 1 if feed_sense == 'positive' else -1


def feed_vector(feed_axis, feed_sense):
    """Unit feed / unroll vector in machine space."""
    feed_axis = normalize_feed_axis(feed_axis)
    s = feed_sign(feed_sense)
    if feed_axis == 'x':
        return QPointF(float(s), 0.0)
    return QPointF(0.0, float(s))


def feed_end_point(bbox, feed_axis, feed_sense, feed_after):
    """Machine-space feed-after point (past cut bbox along feed axis)."""
    feed_axis = normalize_feed_axis(feed_axis)
    s = feed_sign(feed_sense)
    if feed_axis == 'x':
        if s > 0:
            return QPointF(bbox.right() + feed_after, 0.0)
        return QPointF(bbox.left() - feed_after, 0.0)
    if s > 0:
        return QPointF(0.0, bbox.bottom() + feed_after)
    return QPointF(0.0, bbox.top() - feed_after)


def material_rect(size, origin_corner):
    """Material QRectF of size (w, h) with machine origin at origin_corner."""
    w, h = size
    origin_corner = normalize_origin_corner(origin_corner)
    if origin_corner == 'bottom_left':
        return QRectF(0, -h, w, h)
    if origin_corner == 'bottom_right':
        return QRectF(-w, -h, w, h)
    if origin_corner == 'top_left':
        return QRectF(0, 0, w, h)
    return QRectF(-w, 0, w, h)
