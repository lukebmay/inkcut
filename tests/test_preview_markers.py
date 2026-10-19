""" Preview marks sit off the artwork and the head's first and last moves split out.

No cutter. Run with QT_QPA_PLATFORM=offscreen.
"""
import traceback

from enaml.qt.QtCore import QPointF, Qt
from enaml.qt.QtGui import QColor, QImage, QPainter, QPainterPath, QPen

from inkcut.job.models import move_path_of, travel_parts
from inkcut.preview.markers import (
    LABEL_GAP,
    ORIGIN_DIAMETER,
    PreviewMarks,
    cut_overlay,
    layout_pixels,
    mounting_names,
)


def rect_path():
    path = QPainterPath()
    path.moveTo(0, -50)
    path.lineTo(200, -50)
    path.lineTo(200, 0)
    path.lineTo(0, 0)
    path.lineTo(0, -50)
    path.moveTo(0, -80)
    return path


def _segments(path):
    found = []
    current = None
    for index in range(path.elementCount()):
        element = path.elementAt(index)
        point = (element.x, element.y)
        if element.isLineTo() and current is not None:
            found.append((current, point))
        current = point
    return found


def test_travel_splits_the_approach_and_the_finish():
    path = rect_path()
    approach, middle, finish = travel_parts(path, (0.0, 0.0))
    assert approach == ((0.0, 0.0), (0.0, -50.0))
    assert finish == ((0.0, -50.0), (0.0, -80.0))
    assert _segments(middle) == []
    whole = _segments(move_path_of(path))
    assert whole == [approach, finish]


def test_swap_on_names_the_d760_picture():
    assert mounting_names("left") == ("Left", "down")
    assert mounting_names("right") == ("Right", "left")
    _middle, approach, finish, marks = cut_overlay(
        rect_path(), (0.0, 0.0), "right")
    assert marks.origin_name == "Right"
    assert marks.feed == "left"
    assert marks.final == (0.0, -80.0)
    assert _segments(approach) == [((0.0, 0.0), (0.0, -50.0))]
    assert _segments(finish) == [((0.0, -50.0), (0.0, -80.0))]


def _rect(top_left, size):
    return (top_left[0], top_left[1], size[0], size[1])


def _gap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    dx = max(ax - (bx + bw), bx - (ax + aw), 0.0)
    dy = max(ay - (by + bh), by - (ay + ah), 0.0)
    return (dx * dx + dy * dy) ** 0.5


def _closest(rect, point):
    x, y, w, h = rect
    px, py = point
    cx = min(max(px, x), x + w)
    cy = min(max(py, y), y + h)
    return ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5


def test_labels_clear_the_origin_and_each_other():
    # Wider than 13px "Origin (Right)" and "Feed" on this machine, so a
    # slightly larger font still clears the dot.
    origin_size = (96, 20)
    feed_size = (48, 20)
    radius = ORIGIN_DIAMETER / 2.0
    for feed in ("down", "left"):
        places = layout_pixels(feed, origin_size, feed_size)
        origin = _rect(places["origin_label"], origin_size)
        feed_label = _rect(places["feed_label"], feed_size)
        assert _closest(origin, (0.0, 0.0)) >= radius + LABEL_GAP - 0.5
        assert _gap(origin, feed_label) >= 6.0
        tip = places["arrow_tip"]
        if feed == "down":
            assert tip[0] < -radius
            assert feed_label[0] + feed_size[0] < tip[0]
        else:
            # Word, then the head, on the origin label's band and
            # to the right of the dot. The shaft runs further right.
            origin_mid = places["origin_label"][1] + origin_size[1] / 2.0
            feed_mid = feed_label[1] + feed_size[1] / 2.0
            assert tip[0] > radius
            assert feed_label[0] > radius
            assert feed_label[0] + feed_size[0] + 6.0 <= tip[0]
            assert abs(tip[1] - origin_mid) < 1.0
            assert abs(feed_mid - tip[1]) < 1.0


def _ensure_qt():
    from enaml.qt.qt_application import QtApplication
    app = QtApplication.instance()
    if app is None:
        app = QtApplication()
    return app


def _path_points(path):
    return [
        (path.elementAt(index).x, path.elementAt(index).y)
        for index in range(path.elementCount())
    ]


def test_travel_lines_follow_the_pen_up_stroke():
    # plot_view registers its factory at import, which needs an app.
    _ensure_qt()
    from inkcut.preview.plugin import PreviewModel
    from inkcut.preview.plot_view import PainterPathPlotItem

    model = PreviewModel()
    assert model.pen_start.widthF() == model.pen_up.widthF()
    assert model.pen_end.widthF() == model.pen_up.widthF()
    assert model.pen_start.widthF() <= 1.0
    assert model.pen_start.isCosmetic()
    assert model.pen_end.isCosmetic()
    assert model.pen_start.color().alphaF() == 1.0
    assert model.pen_end.color().alphaF() == 1.0
    assert (model.pen_start.color().red(), model.pen_start.color().green(),
            model.pen_start.color().blue()) == (0x1F, 0x9D, 0x55)
    assert (model.pen_end.color().red(), model.pen_end.color().green(),
            model.pen_end.color().blue()) == (0xE5, 0x39, 0x35)

    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(50, -200)
    item = PainterPathPlotItem(path, pen=model.pen_start)
    assert item._shouldUseDrawLineSegments(item.opts["pen"]) is False
    # Y flip keeps the real approach. Segment mode would draw the other diagonal.
    assert _path_points(item.getPath()) == [(0.0, 0.0), (50.0, 200.0)]


def test_finish_mark_paints_over_the_start_mark():
    _ensure_qt()
    image = QImage(32, 32, QImage.Format_ARGB32)
    image.fill(Qt.white)
    painter = QPainter(image)
    marks = PreviewMarks((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), "down", "Left")
    painter.translate(16, 16)
    marks._paint_travel_mark(painter, QPointF(0, 0), "start", 1.0, 1.0)
    marks._paint_travel_mark(painter, QPointF(0, 0), "end", 1.0, 1.0)
    painter.end()
    pixel = image.pixelColor(16, 16)
    assert (pixel.red(), pixel.green(), pixel.blue()) == (0xE5, 0x39, 0x35)


def _art_pen():
    pen = QPen(QColor('#111111'))
    pen.setWidthF(2.0)
    pen.setCosmetic(True)
    return pen


def _contains_art(view):
    (x0, x1), (y0, y1) = view.viewRange()
    # addRect(0, -50, 200, 50) flips to x 0..200, y 0..50.
    return x0 <= 0.0 and x1 >= 200.0 and y0 <= 0.0 and y1 >= 50.0


def _axis_is_a_few_tens(axis, kind):
    if kind == 'width':
        span = axis.minimumWidth()
        cap = axis.maximumWidth()
    else:
        span = axis.minimumHeight()
        cap = axis.maximumHeight()
    assert 10 <= span <= 80
    assert cap != 16777215
    assert span != 16777215


def _shown_plot(fit_once):
    from enaml.qt.QtWidgets import QApplication
    from inkcut.preview.plot_view import PainterPathPlotItem, PlotView, QtPlotView

    proxy = QtPlotView()
    proxy.declaration = PlotView(fit_once=fit_once, range_padding=0.28)
    proxy.create_widget()
    widget = proxy.widget
    widget.resize(640, 480)
    widget.show()
    path = QPainterPath()
    path.addRect(0, -50, 200, 50)
    proxy._set_graphic_items([PainterPathPlotItem(path, pen=_art_pen())])
    if fit_once:
        view = widget.getViewBox()
        for _ in range(6):
            QApplication.processEvents()
            if (view.width() > 1 and view.height() > 1
                    and view.autoRangeEnabled() == [False, False]
                    and _contains_art(view)):
                break
        else:
            raise AssertionError('preview did not fit')
    return proxy, widget


def _grab_has_ink(widget):
    image = widget.grab().toImage()
    assert not image.isNull()
    assert image.width() > 1 and image.height() > 1
    for y in range(0, image.height(), 3):
        for x in range(0, image.width(), 3):
            color = image.pixelColor(x, y)
            if color.red() < 250 or color.green() < 250 or color.blue() < 250:
                return
    raise AssertionError('preview grab is all white')


def _close_plot(widget):
    from enaml.qt.QtWidgets import QApplication

    widget.hide()
    widget.deleteLater()
    QApplication.processEvents()


def test_preview_fits_once_and_stays_still():
    _ensure_qt()
    from enaml.qt.QtWidgets import QApplication

    proxy, widget = _shown_plot(True)
    view = widget.getViewBox()
    left = widget.plotItem.getAxis('left')
    bottom = widget.plotItem.getAxis('bottom')
    assert view.autoRangeEnabled() == [False, False]
    assert _contains_art(view)
    assert view.width() > 1 and view.height() > 1
    _grab_has_ink(widget)
    assert left.style['autoExpandTextSpace'] is False
    assert left.style['autoReduceTextSpace'] is False
    assert bottom.style['autoExpandTextSpace'] is False
    assert bottom.style['autoReduceTextSpace'] is False
    assert left.style['tickTextWidth'] == 30
    assert bottom.style['tickTextHeight'] == 18
    _axis_is_a_few_tens(left, 'width')
    _axis_is_a_few_tens(bottom, 'height')
    left_min = left.minimumWidth()
    bottom_min = bottom.minimumHeight()
    left._updateMaxTextSize(left_min + 40)
    bottom._updateMaxTextSize(bottom_min + 40)
    QApplication.processEvents()
    assert left.minimumWidth() == left_min
    assert bottom.minimumHeight() == bottom_min
    held = [list(axis) for axis in view.viewRange()]
    for _ in range(12):
        QApplication.processEvents()
    assert [list(axis) for axis in view.viewRange()] == held

    ranges = []
    for width, height in ((700, 480), (701, 480), (700, 480), (701, 480)):
        widget.resize(width, height)
        QApplication.processEvents()
        ranges.append([list(axis) for axis in view.viewRange()])
    assert ranges[0] == ranges[2]
    assert ranges[1] == ranges[3]
    assert left.minimumWidth() == left_min
    assert bottom.minimumHeight() == bottom_min
    assert view.autoRangeEnabled() == [False, False]
    _close_plot(widget)


def test_fit_does_not_pump_the_event_loop():
    _ensure_qt()
    from enaml.qt.QtWidgets import QApplication

    pumped = []
    entered = []
    original = QApplication.processEvents

    def wrapped(*args, **kwargs):
        entered.append(1)
        if any(frame.filename.endswith('plot_view.py')
               for frame in traceback.extract_stack()):
            pumped.append(1)
        return original(*args, **kwargs)

    QApplication.processEvents = wrapped
    try:
        _proxy, widget = _shown_plot(True)
    finally:
        QApplication.processEvents = original
    assert entered
    assert pumped == []
    _close_plot(widget)


def _rect_at(x):
    path = QPainterPath()
    path.addRect(x, -40, 80, 40)
    return path


def test_second_set_data_keeps_the_new_items():
    _ensure_qt()
    from enaml.qt.QtWidgets import QApplication
    from inkcut.preview.plot_view import PainterPathPlotItem

    proxy, widget = _shown_plot(True)
    first = PainterPathPlotItem(_rect_at(0), pen=_art_pen())
    second = PainterPathPlotItem(_rect_at(30), pen=_art_pen())
    proxy._set_graphic_items([first])
    proxy._set_graphic_items([second])
    for _ in range(6):
        QApplication.processEvents()
    assert widget.plotItem.listDataItems() == [second]
    (x0, x1), (y0, y1) = widget.getViewBox().viewRange()
    assert x0 <= 30.0 and x1 >= 110.0
    assert y0 <= 0.0 and y1 >= 40.0
    _close_plot(widget)


def test_zoom_is_not_restored_by_a_later_event():
    _ensure_qt()
    from enaml.qt.QtWidgets import QApplication

    _proxy, widget = _shown_plot(True)
    view = widget.getViewBox()
    fitted = view.viewRange()
    fitted_span = fitted[0][1] - fitted[0][0]
    view.scaleBy((0.5, 0.5))
    zoomed = [list(axis) for axis in view.viewRange()]
    zoomed_span = zoomed[0][1] - zoomed[0][0]
    assert zoomed_span < fitted_span * 0.75
    for _ in range(8):
        QApplication.processEvents()
    widget.resize(700, 500)
    QApplication.processEvents()
    later = view.viewRange()
    later_span = later[0][1] - later[0][0]
    assert later_span < fitted_span * 0.75
    _close_plot(widget)


def test_live_plot_axes_still_follow_the_labels():
    _ensure_qt()
    proxy, widget = _shown_plot(False)
    view = widget.getViewBox()
    left = widget.plotItem.getAxis('left')
    assert left.style['autoExpandTextSpace'] is True
    assert any(view.autoRangeEnabled())
    before = left.minimumWidth()
    left._updateMaxTextSize(max(before, left.textWidth) + 40)
    assert left.minimumWidth() > before
    _close_plot(widget)
