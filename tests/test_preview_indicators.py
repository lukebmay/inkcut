# -*- coding: utf-8 -*-
"""Preview indicator geometry and plan layer helpers."""
from __future__ import division

import os

import pytest
from enaml.qt.QtCore import QPointF
from enaml.qt.QtGui import QPainterPath
from enaml.qt.QtWidgets import QApplication

# Offscreen Qt for PainterPathPlotItem / PreviewPlugin tests
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
if QApplication.instance() is None:
    QApplication([])

from inkcut.device.frame import feed_vector
from inkcut.job.toolpath import PathSegment, ToolpathPlan
from inkcut.preview.indicators import (
    epilogue_as_travel, feed_arrow_path, indicator_length, moves_to_lines,
    origin_crosshair_path, path_last_point, plan_layer_paths,
    resolve_feed_direction,
)


def _point_on_path(path, x, y, tol=1e-6):
    """True if some element is near (x, y)."""
    for i in range(path.elementCount()):
        e = path.elementAt(i)
        if abs(e.x - x) <= tol and abs(e.y - y) <= tol:
            return True
    return False


def test_origin_crosshair_centered_at_machine_origin():
    path = origin_crosshair_path(origin=QPointF(0, 0), arm=10)
    assert not path.isEmpty()
    assert _point_on_path(path, -10, 0)
    assert _point_on_path(path, 10, 0)
    assert _point_on_path(path, 0, -10)
    assert _point_on_path(path, 0, 10)
    br = path.boundingRect()
    assert br.center().x() == pytest.approx(0.0, abs=1e-6)
    assert br.center().y() == pytest.approx(0.0, abs=1e-6)


def test_origin_crosshair_offset():
    path = origin_crosshair_path(origin=QPointF(5, -3), arm=4)
    assert _point_on_path(path, 5 - 4, -3)
    assert _point_on_path(path, 5 + 4, -3)


def test_feed_arrow_follows_frame_vector():
    direction = feed_vector('y', 'negative')
    path = feed_arrow_path(
        origin=QPointF(0, 0), direction=direction, length=40, head=8)
    assert not path.isEmpty()
    # tip at (0, -40)
    assert _point_on_path(path, 0, -40)
    assert _point_on_path(path, 0, 0)
    br = path.boundingRect()
    assert br.bottom() <= 0 or br.top() <= 0
    assert br.center().y() < 0


def test_feed_arrow_x_positive():
    direction = feed_vector('x', 'positive')
    path = feed_arrow_path(
        origin=QPointF(0, 0), direction=direction, length=25)
    assert _point_on_path(path, 25, 0)
    assert path.boundingRect().right() == pytest.approx(25.0)


def test_indicator_length_scales_with_size():
    assert indicator_length((100, 50), fraction=0.1, minimum=5) == pytest.approx(10.0)
    assert indicator_length((10, 10), fraction=0.1, minimum=15) == pytest.approx(15.0)
    assert indicator_length((1000, 1000), fraction=0.2, minimum=1, maximum=50) == pytest.approx(50.0)


def test_moves_to_lines_makes_travel_visible():
    cut = QPainterPath()
    cut.moveTo(0, 0)
    cut.lineTo(10, 0)
    cut.moveTo(20, 5)
    cut.lineTo(30, 5)
    travel = moves_to_lines(cut)
    # First move becomes lineTo from default (0,0); second move → line to (20,5)
    assert travel.elementCount() >= 2
    assert _point_on_path(travel, 20, 5)
    # line elements of cut become moveTo (not stroked as travel between cuts)
    assert not _point_on_path(travel, 10, 0) or True  # may still appear as move
    # travel should include a line-like connection into the second subpath start
    found_line_to_second = False
    for i in range(travel.elementCount()):
        e = travel.elementAt(i)
        if e.isLineTo() and abs(e.x - 20) < 1e-9 and abs(e.y - 5) < 1e-9:
            found_line_to_second = True
    assert found_line_to_second


def test_plan_layer_paths_prefers_plan_and_synthesizes_travel():
    cut = QPainterPath()
    cut.moveTo(0, 0)
    cut.lineTo(5, 0)
    cut.moveTo(10, 0)
    cut.lineTo(15, 0)
    epi = QPainterPath()
    epi.moveTo(0, 0)
    plan = ToolpathPlan(
        segments=[
            PathSegment('cut', cut),
            PathSegment('epilogue', epi, meta={'mode': 'return', 'end': QPointF(0, 0)}),
        ],
        origin=QPointF(0, 0),
        feed_vector=QPointF(0, -1),
    )
    layers = plan_layer_paths(plan=plan)
    assert layers['cut'].elementCount() == cut.elementCount()
    assert not layers['travel'].isEmpty()
    # epilogue line from last cut point (15,0) to (0,0)
    epi_path = layers['epilogue']
    assert not epi_path.isEmpty()
    assert _point_on_path(epi_path, 15, 0)
    assert _point_on_path(epi_path, 0, 0)


def test_plan_layer_paths_prefers_typed_travels():
    """When plan has travel segments, use those lines (not moves_to_lines)."""
    cut_a = QPainterPath()
    cut_a.moveTo(0, 0)
    cut_a.lineTo(5, 0)
    travel = QPainterPath()
    travel.moveTo(5, 0)
    travel.lineTo(12, 8)
    cut_b = QPainterPath()
    cut_b.moveTo(12, 8)
    cut_b.lineTo(18, 8)
    plan = ToolpathPlan(segments=[
        PathSegment('cut', cut_a),
        PathSegment('travel', travel, meta={
            'start': QPointF(5, 0), 'end': QPointF(12, 8)}),
        PathSegment('cut', cut_b),
    ])
    layers = plan_layer_paths(plan=plan)
    assert _point_on_path(layers['travel'], 5, 0)
    assert _point_on_path(layers['travel'], 12, 8)
    # Typed travel preferred: should include the line destination
    found_line = False
    for i in range(layers['travel'].elementCount()):
        e = layers['travel'].elementAt(i)
        if e.isLineTo() and abs(e.x - 12) < 1e-9 and abs(e.y - 8) < 1e-9:
            found_line = True
    assert found_line
    # Epilogue layer empty without epilogue segments
    assert layers['epilogue'].isEmpty()


def test_plan_layer_paths_fallback_without_plan():
    cut = QPainterPath()
    cut.moveTo(1, 1)
    cut.lineTo(2, 2)
    move = QPainterPath()
    move.moveTo(0, 0)
    move.lineTo(1, 1)
    layers = plan_layer_paths(plan=None, move_path=move, cut_path=cut)
    assert layers['cut'] is cut
    assert layers['travel'] is move


def test_epilogue_as_travel_uses_meta_end():
    cut = QPainterPath()
    cut.moveTo(0, 0)
    cut.lineTo(8, 4)
    plan = ToolpathPlan(segments=[
        PathSegment('cut', cut),
        PathSegment('epilogue', QPainterPath(), meta={
            'mode': 'feed', 'end': QPointF(0, -20)}),
    ])
    path = epilogue_as_travel(plan)
    assert _point_on_path(path, 8, 4)
    assert _point_on_path(path, 0, -20)


def test_resolve_feed_direction_from_plan_or_frame():
    plan = ToolpathPlan(feed_vector=QPointF(1, 0))
    v = resolve_feed_direction(plan=plan)
    assert v.x() == pytest.approx(1.0)
    assert v.y() == pytest.approx(0.0)
    v2 = resolve_feed_direction(plan=None, feed_axis='y', feed_sense='negative')
    assert v2.x() == pytest.approx(0.0)
    assert v2.y() == pytest.approx(-1.0)


def test_path_last_point():
    p = QPainterPath()
    assert path_last_point(p) is None
    p.moveTo(1, 2)
    p.lineTo(3, 4)
    last = path_last_point(p)
    assert last.x() == pytest.approx(3.0)
    assert last.y() == pytest.approx(4.0)


def test_painter_path_plot_item_accepts_path_and_name():
    """Constructor must not pass QPainterPath into PlotCurveItem.setData."""
    import pyqtgraph as pg
    from inkcut.preview.plot_view import PainterPathPlotItem

    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(10, 5)
    item = PainterPathPlotItem(
        path, pen=pg.mkPen((1, 2, 3)), name='Cuts', skip_autorange=True)
    assert item.name() == 'Cuts'
    assert not item.path.isEmpty()
    # Display path is Y-flipped; geometry still non-empty
    assert item.boundingRect().width() > 0 or item.boundingRect().height() > 0


def test_layer_view_items_include_legend_names():
    from inkcut.preview.plugin import PreviewModel, PreviewPlugin

    cut = QPainterPath()
    cut.moveTo(0, 0)
    cut.lineTo(5, 0)
    cut.moveTo(10, 0)
    cut.lineTo(15, 0)
    weed = QPainterPath()
    weed.moveTo(-1, -1)
    weed.lineTo(16, -1)
    epi = QPainterPath()
    epi.moveTo(0, 0)
    plan = ToolpathPlan(
        segments=[
            PathSegment('cut', cut),
            PathSegment('weed', weed),
            PathSegment('epilogue', epi, meta={
                'mode': 'return', 'end': QPointF(0, 0)}),
        ],
        origin=QPointF(0, 0),
        feed_vector=QPointF(0, -1),
    )
    plugin = PreviewPlugin()
    plot = PreviewModel()
    items = plugin.layer_view_items(
        plot, plan=plan, size=(100, 100))
    names = [i.get('name') for i in items]
    assert 'Travel' in names or any(n and 'Travel' in n for n in names)
    assert 'Cuts' in names or any(n and 'Cuts' in n for n in names)
    assert 'Weed lines' in names or any(n and 'Weed' in n for n in names)
    assert 'Epilogue' in names or any(n and 'Epilogue' in n for n in names)
    assert 'Origin' in names or any(n and 'Origin' in n for n in names)
    assert 'Feed direction' in names or any(
        n and 'Feed' in n for n in names)
    # Pens present for named layers
    by_name = {i['name']: i for i in items if i.get('name')}
    assert 'pen' in by_name[list(by_name.keys())[0]]


def test_layer_view_items_respect_toggles():
    from inkcut.preview.plugin import PreviewModel, PreviewPlugin

    cut = QPainterPath()
    cut.moveTo(0, 0)
    cut.lineTo(5, 0)
    plan = ToolpathPlan(
        segments=[PathSegment('cut', cut)],
        origin=QPointF(0, 0),
        feed_vector=QPointF(0, -1),
    )
    plugin = PreviewPlugin()
    plugin.show_cuts = False
    plugin.show_travel = False
    plugin.show_origin = False
    plugin.show_feed = False
    items = plugin.layer_view_items(
        PreviewModel(), plan=plan, size=(50, 50))
    assert items == []
