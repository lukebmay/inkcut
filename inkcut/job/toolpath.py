# -*- coding: utf-8 -*-
"""Typed toolpath layers: cuts/weeds separate from machine epilogue."""
from enaml.qt.QtCore import QPointF, QRectF
from enaml.qt.QtGui import QPainterPath


SEGMENT_KINDS = ('cut', 'travel', 'weed', 'epilogue')


class PathSegment(object):
    """One typed piece of a job path."""

    __slots__ = ('kind', 'path', 'meta')

    def __init__(self, kind, path, meta=None):
        if kind not in SEGMENT_KINDS:
            raise ValueError("invalid segment kind: %r" % (kind,))
        self.kind = kind
        self.path = path
        self.meta = meta if meta is not None else {}


class ToolpathPlan(object):
    """Ordered segments in machine space after design/frame mapping."""

    __slots__ = ('segments', 'origin', 'feed_vector', 'bounds')

    def __init__(self, segments=None, origin=None, feed_vector=None,
                 bounds=None):
        self.segments = list(segments or [])
        self.origin = origin if origin is not None else QPointF(0, 0)
        self.feed_vector = (feed_vector if feed_vector is not None
                            else QPointF(0, 1))
        self.bounds = bounds if bounds is not None else QRectF()

    def _concat(self, kinds):
        result = QPainterPath()
        for seg in self.segments:
            if seg.kind in kinds and seg.path and not seg.path.isEmpty():
                result.addPath(seg.path)
        return result

    def cuts(self):
        return self._concat(('cut',))

    def travels(self):
        return self._concat(('travel',))

    def weeds(self):
        return self._concat(('weed',))

    def epilogue(self):
        """Epilogue path (may be move-only; not always addPath-safe)."""
        result = QPainterPath()
        for seg in self.segments:
            if seg.kind != 'epilogue' or not seg.path:
                continue
            self._append_epilogue_path(result, seg.path)
        return result

    def to_device_stream(self):
        """Concatenate for existing protocols (single QPainterPath)."""
        result = QPainterPath()
        for seg in self.segments:
            if not seg.path or seg.path.elementCount() == 0:
                continue
            if seg.kind == 'epilogue':
                # Pure moveTo paths are dropped by addPath; apply explicitly
                self._append_epilogue_path(result, seg.path)
            else:
                result.addPath(seg.path)
        return result

    @staticmethod
    def _append_epilogue_path(result, path):
        for i in range(path.elementCount()):
            e = path.elementAt(i)
            if e.isMoveTo():
                result.moveTo(e.x, e.y)
            elif e.isLineTo():
                result.lineTo(e.x, e.y)
            else:
                result.lineTo(e.x, e.y)
