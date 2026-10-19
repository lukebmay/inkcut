""" Origin, feed, and head marks for the pre-cut preview.

Path points use the job frame (y down). The plot shows y up, so a path
point (x, y) is drawn at (x, -y). Mark sizes stay in pixels.
"""
from enaml.qt import QtCore, QtGui
from enaml.qt.QtWidgets import QApplication
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject

from inkcut.device.plugin import feed_for_origin
from inkcut.job.models import travel_parts


FEED_BLUE = QtGui.QColor("#1783FF")
START_GREEN = QtGui.QColor("#1F9D55")
END_RED = QtGui.QColor("#E53935")
ORIGIN_BLACK = QtGui.QColor("#111111")

ORIGIN_DIAMETER = 14.0
START_DIAMETER = 7.0
CROSS_LENGTH = 13.0
CROSS_THICK = 3.8
LABEL_GAP = 14.0
ARROW_LENGTH = 42.0
ARROW_SHAFT = 6.0
ARROW_HEAD_W = 16.0
ARROW_HEAD_L = 14.0
ARROW_CLEAR = 18.0
TEXT_PX = 13


def placed_origin(device, job):
    """ Corner the preview calls the origin, in path coordinates. """
    if job is not None and job.feed_to_end:
        ox, oy = device.origin[0], device.origin[1]
        return (float(ox), -float(oy))
    return (0.0, 0.0)


def mounting_names(origin_side):
    """ Caption from the origin side. The arrow is the feed direction. """
    feed = feed_for_origin(origin_side)
    if origin_side == "right":
        return "Right", feed
    return "Left", feed


def origin_caption(name):
    if name == "Right":
        return QApplication.translate("preview", "Origin (Right)")
    return QApplication.translate("preview", "Origin (Left)")


def feed_caption():
    return QApplication.translate("preview", "Feed")


def text_size(metrics, text):
    rect = metrics.boundingRect(text)
    return (rect.width(), max(rect.height(), metrics.height()))


def line_path(segment):
    path = QtGui.QPainterPath()
    if segment is None:
        return path
    start, end = segment
    path.moveTo(start[0], start[1])
    path.lineTo(end[0], end[1])
    return path


def layout_pixels(feed, origin_size, feed_size):
    """ Pixel positions relative to the origin dot. +x right, +y down.

    `origin_size` and `feed_size` are (width, height) of the two labels.
    The arrow value is the tip.

    Down keeps the arrow up the left side, with the word outside it.
    Left puts one band under the art: the origin word, then "Feed",
    then a left-pointing arrow. The head stays to the right of the dot
    so it does not point into the origin word.
    """
    radius = ORIGIN_DIAMETER / 2.0
    origin_w, origin_h = origin_size
    feed_w, feed_h = feed_size
    origin_label = (
        -(radius + LABEL_GAP) - origin_w,
        radius + LABEL_GAP,
    )
    if feed == "left":
        tip_y = origin_label[1] + origin_h / 2.0
        feed_label = (
            radius + LABEL_GAP,
            tip_y - feed_h / 2.0,
        )
        tip = (feed_label[0] + feed_w + 8.0, tip_y)
    else:
        tip = (-(radius + ARROW_CLEAR), radius + 4.0)
        shaft_mid_y = tip[1] - ARROW_HEAD_L - (ARROW_LENGTH - ARROW_HEAD_L) / 2.0
        feed_label = (
            tip[0] - ARROW_HEAD_W / 2.0 - 8.0 - feed_w,
            shaft_mid_y - feed_h / 2.0,
        )
    return {
        "origin_label": origin_label,
        "arrow_tip": tip,
        "feed_label": feed_label,
    }


def _arrow_polygon(feed):
    shaft = ARROW_LENGTH - ARROW_HEAD_L
    half_head = ARROW_HEAD_W / 2.0
    half_shaft = ARROW_SHAFT / 2.0
    if feed == "left":
        points = [
            (0, 0),
            (ARROW_HEAD_L, half_head),
            (ARROW_HEAD_L, half_shaft),
            (ARROW_HEAD_L + shaft, half_shaft),
            (ARROW_HEAD_L + shaft, -half_shaft),
            (ARROW_HEAD_L, -half_shaft),
            (ARROW_HEAD_L, -half_head),
        ]
    else:
        points = [
            (0, 0),
            (-half_head, -ARROW_HEAD_L),
            (-half_shaft, -ARROW_HEAD_L),
            (-half_shaft, -ARROW_HEAD_L - shaft),
            (half_shaft, -ARROW_HEAD_L - shaft),
            (half_shaft, -ARROW_HEAD_L),
            (half_head, -ARROW_HEAD_L),
        ]
    return QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in points])


class PreviewMarks(GraphicsObject):
    """ Pixel-sized origin, feed arrow, head start, and head finish. """

    def __init__(self, origin, start, final, feed, origin_name):
        GraphicsObject.__init__(self)
        self.origin = origin
        self.start = start
        self.final = final
        self.feed = feed
        self.origin_name = origin_name
        self._bounds = None
        self.setZValue(20)

    def _view(self, point):
        return QtCore.QPointF(point[0], -point[1])

    def dataBounds(self, ax, frac=1.0, orthoRange=None):
        points = [self._view(self.origin), self._view(self.final), self._view(self.start)]
        values = [point.x() if ax == 0 else point.y() for point in points]
        return (min(values), max(values))

    def viewTransformChanged(self):
        self.prepareGeometryChange()
        self._bounds = None
        self.update()

    def boundingRect(self):
        if self._bounds is not None:
            return self._bounds
        points = [self._view(self.origin), self._view(self.final), self._view(self.start)]
        pw = self.pixelWidth() or 1.0
        ph = self.pixelHeight() or 1.0
        pad_x = 160.0 * pw
        pad_y = 160.0 * ph
        left = min(point.x() for point in points) - pad_x
        right = max(point.x() for point in points) + pad_x
        top = min(point.y() for point in points) - pad_y
        bottom = max(point.y() for point in points) + pad_y
        self._bounds = QtCore.QRectF(left, top, right - left, bottom - top)
        return self._bounds

    def paint(self, painter, *args):
        pw = self.pixelWidth()
        ph = self.pixelHeight()
        if not pw or not ph:
            return
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self._paint_origin_cluster(painter, pw, ph)
        self._paint_travel_mark(painter, self._view(self.start), "start", pw, ph)
        # Finish stays visible when the head ends on the origin.
        self._paint_travel_mark(painter, self._view(self.final), "end", pw, ph)

    def _pixel_transform(self, painter, anchor, pw, ph):
        painter.translate(anchor)
        # Plot +y is up. Pixel +y is down the screen.
        painter.scale(pw, -ph)
        # Whole pixels, or the cross arms blur into one blob.
        origin = painter.transform().map(QtCore.QPointF(0, 0))
        frac_x = origin.x() - round(origin.x())
        frac_y = origin.y() - round(origin.y())
        painter.translate(-frac_x, frac_y)

    def _font(self):
        font = QtGui.QFont()
        font.setPixelSize(TEXT_PX)
        return font

    def _paint_origin_cluster(self, painter, pw, ph):
        anchor = self._view(self.origin)
        font = self._font()
        metrics = QtGui.QFontMetrics(font)
        origin_text = origin_caption(self.origin_name)
        feed_text = feed_caption()
        origin_size = text_size(metrics, origin_text)
        feed_size = text_size(metrics, feed_text)
        places = layout_pixels(self.feed, origin_size, feed_size)

        painter.save()
        self._pixel_transform(painter, anchor, pw, ph)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(ORIGIN_BLACK))
        radius = ORIGIN_DIAMETER / 2.0
        painter.drawEllipse(QtCore.QRectF(-radius, -radius, ORIGIN_DIAMETER, ORIGIN_DIAMETER))

        painter.setBrush(QtGui.QBrush(FEED_BLUE))
        tip = places["arrow_tip"]
        painter.save()
        painter.translate(tip[0], tip[1])
        painter.drawPolygon(_arrow_polygon(self.feed))
        painter.restore()

        painter.setFont(font)
        painter.setPen(QtGui.QPen(ORIGIN_BLACK))
        self._draw_label(painter, places["origin_label"], origin_text)
        painter.setPen(QtGui.QPen(FEED_BLUE))
        self._draw_label(painter, places["feed_label"], feed_text)
        painter.restore()

    def _draw_label(self, painter, top_left, text):
        painter.drawText(
            QtCore.QPointF(top_left[0], top_left[1] + painter.fontMetrics().ascent()),
            text,
        )

    def _paint_travel_mark(self, painter, anchor, kind, pw, ph):
        painter.save()
        self._pixel_transform(painter, anchor, pw, ph)
        painter.setPen(QtCore.Qt.NoPen)
        if kind == "start":
            painter.setBrush(QtGui.QBrush(START_GREEN))
            diameter = START_DIAMETER
            painter.drawEllipse(QtCore.QRectF(
                -diameter / 2.0, -diameter / 2.0, diameter, diameter))
        else:
            painter.setBrush(QtGui.QBrush(END_RED))
            painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
            rect = QtCore.QRectF(
                -CROSS_LENGTH / 2.0, -CROSS_THICK / 2.0, CROSS_LENGTH, CROSS_THICK)
            painter.save()
            painter.rotate(45)
            painter.drawRect(rect)
            painter.restore()
            painter.save()
            painter.rotate(-45)
            painter.drawRect(rect)
            painter.restore()
        painter.restore()


def cut_overlay(path, head, origin_side):
    """ Middle travel, approach, finish, and the marker item for one path. """
    approach, middle, finish = travel_parts(path, head)
    if finish is not None:
        final = finish[1]
    elif path is not None and path.elementCount():
        end = path.elementAt(path.elementCount() - 1)
        final = (end.x, end.y)
    else:
        final = head
    origin_name, feed = mounting_names(origin_side)
    marks = PreviewMarks(head, head, final, feed, origin_name)
    return middle, line_path(approach), line_path(finish), marks
