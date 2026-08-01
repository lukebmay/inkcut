# -*- coding: utf-8 -*-
"""ToolpathPlan: epilogue stays in machine space after design transforms."""
from __future__ import division

import pytest
from enaml.qt.QtCore import QPointF, QRectF
from enaml.qt.QtGui import QPainterPath

from inkcut.core.svg import QtSvgDoc
from inkcut.device.frame import (
    DEFAULT_FEED_SENSE, design_to_machine_transform, feed_end_point,
    feed_vector, material_rect, origin_shift,
)
from inkcut.job.models import Job
from inkcut.job.toolpath import PathSegment, ToolpathPlan


SIMPLE_SVG = '''<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">
  <rect x="10" y="10" width="80" height="30" fill="none" stroke="black"/>
</svg>'''


def _job_with_doc(**kwargs):
    doc = QtSvgDoc(SIMPLE_SVG)
    job = Job()
    job.doc = doc
    job.path = doc
    job.optimized_path = doc
    for k, v in kwargs.items():
        setattr(job, k, v)
    return job


def _last_point(path):
    assert path is not None and path.elementCount() > 0
    e = path.elementAt(path.elementCount() - 1)
    return e.x, e.y


def _epilogue_end(plan):
    segs = [s for s in plan.segments if s.kind == 'epilogue']
    assert segs, "expected an epilogue segment"
    meta_end = segs[-1].meta.get('end')
    if meta_end is not None:
        return meta_end.x(), meta_end.y()
    return _last_point(segs[-1].path)


def test_path_segment_rejects_bad_kind():
    with pytest.raises(ValueError):
        PathSegment(kind='nope', path=QPainterPath())


def test_toolpath_plan_filters_and_stream():
    cut = QPainterPath()
    cut.moveTo(0, 0)
    cut.lineTo(10, 0)
    cut.lineTo(10, 10)

    epi = QPainterPath()
    epi.moveTo(0, 0)

    plan = ToolpathPlan(segments=[
        PathSegment('cut', cut),
        PathSegment('epilogue', epi, meta={'mode': 'return', 'end': QPointF(0, 0)}),
    ])
    assert plan.cuts().elementCount() == 3
    stream = plan.to_device_stream()
    assert _last_point(stream) == (0.0, 0.0)


def test_create_returns_concatenated_stream():
    job = _job_with_doc(feed_to_end=False)
    plan = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y')
    created = job.create(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y')
    assert plan is not None
    assert created is not None
    assert created.elementCount() == plan.to_device_stream().elementCount()
    assert _last_point(created) == _last_point(plan.to_device_stream())


def test_return_epilogue_stays_at_origin_despite_scale_mirror_swap():
    """Design/device transforms must not move return epilogue off (0,0)."""
    job = _job_with_doc(
        feed_to_end=False,
        scale=[2.5, 1.5],
        mirror=[True, True],
        rotation=15,
    )
    plan = job.build_plan(
        swap_xy=True,
        scale=[-2, 3],
        origin_position='bottom_left',
        feed_axis='y',
        epilogue='return',
    )
    assert plan is not None
    assert any(s.kind == 'cut' for s in plan.segments)
    ex, ey = _epilogue_end(plan)
    assert ex == pytest.approx(0.0)
    assert ey == pytest.approx(0.0)

    stream = plan.to_device_stream()
    sx, sy = _last_point(stream)
    assert sx == pytest.approx(0.0)
    assert sy == pytest.approx(0.0)

    # Cuts themselves are non-trivial after transforms
    cut_bb = plan.cuts().boundingRect()
    assert cut_bb.width() > 0 and cut_bb.height() > 0


def test_stock_return_mode_has_no_epilogue_segment():
    """feed_to_end=False matches stock: no return path segment."""
    job = _job_with_doc(feed_to_end=False)
    plan = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y')
    assert all(s.kind != 'epilogue' for s in plan.segments)


def test_feed_after_bottom_left_y():
    """Default feed_sense=negative preserves stock bottom_left + y baseline."""
    job = _job_with_doc(feed_to_end=True, feed_after=50)
    plan = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y')
    ex, ey = _epilogue_end(plan)
    assert ex == pytest.approx(0.0)
    # bottom + y + negative: feed toward more-negative y (bbox.top() - feed_after)
    assert ey < 0
    cut_top = plan.bounds.top()
    assert ey == pytest.approx(cut_top - 50)

    stream = plan.to_device_stream()
    assert _last_point(stream) == pytest.approx((ex, ey))
    assert plan.feed_vector.x() == pytest.approx(0.0)
    assert plan.feed_vector.y() == pytest.approx(-1.0)
    assert DEFAULT_FEED_SENSE == 'negative'


def test_feed_after_bottom_right_x():
    job = _job_with_doc(feed_to_end=True, feed_after=40)
    plan = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_right', feed_axis='x',
        feed_sense='negative')
    ex, ey = _epilogue_end(plan)
    assert ey == pytest.approx(0.0)
    assert ex < 0
    assert ex == pytest.approx(plan.bounds.left() - 40)


def test_feed_sense_flips_feed_after_direction():
    job = _job_with_doc(feed_to_end=True, feed_after=30)
    neg = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_corner='bottom_left', feed_axis='y',
        feed_sense='negative')
    pos = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_corner='bottom_left', feed_axis='y',
        feed_sense='positive')
    nx, ny = _epilogue_end(neg)
    px, py = _epilogue_end(pos)
    assert nx == pytest.approx(0.0) and px == pytest.approx(0.0)
    assert ny == pytest.approx(neg.bounds.top() - 30)
    assert py == pytest.approx(pos.bounds.bottom() + 30)
    assert ny < 0 < py
    assert neg.feed_vector.y() == pytest.approx(-1.0)
    assert pos.feed_vector.y() == pytest.approx(1.0)


def test_feed_sense_flips_along_x():
    job = _job_with_doc(feed_to_end=True, feed_after=15)
    neg = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_corner='bottom_left', feed_axis='x',
        feed_sense='negative')
    pos = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_corner='bottom_left', feed_axis='x',
        feed_sense='positive')
    nx, ny = _epilogue_end(neg)
    px, py = _epilogue_end(pos)
    assert ny == pytest.approx(0.0) and py == pytest.approx(0.0)
    assert nx == pytest.approx(neg.bounds.left() - 15)
    assert px == pytest.approx(pos.bounds.right() + 15)
    assert nx < 0 < px


def test_origin_corner_maps_work_bbox_corner_to_origin():
    """With zero padding, chosen corner of cut bbox is at machine origin."""
    job = _job_with_doc(feed_to_end=False)
    job.material.padding = [0.0, 0.0, 0.0, 0.0]

    bl = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_corner='bottom_left', feed_axis='y')
    assert bl.bounds.left() == pytest.approx(0.0)
    assert bl.bounds.bottom() == pytest.approx(0.0)

    br = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_corner='bottom_right', feed_axis='y')
    assert br.bounds.right() == pytest.approx(0.0)
    assert br.bounds.bottom() == pytest.approx(0.0)

    tl = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_corner='top_left', feed_axis='y')
    assert tl.bounds.left() == pytest.approx(0.0)
    assert tl.bounds.top() == pytest.approx(0.0)


def test_feed_epilogue_not_warped_by_job_scale_mirror():
    """Job design scale/mirror must not rescale the machine feed endpoint."""
    job = _job_with_doc(
        feed_to_end=True,
        feed_after=25,
        scale=[3, 3],
        mirror=[True, False],
    )
    plan = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y',
        feed_sense='negative')
    ex, ey = _epilogue_end(plan)
    assert ex == pytest.approx(0.0)
    assert ey == pytest.approx(plan.bounds.top() - 25)

    # Endpoint sits on machine origin's complementary axis only
    stream_end = _last_point(plan.to_device_stream())
    assert stream_end[0] == pytest.approx(0.0)


def test_feed_epilogue_with_device_scale_uses_post_map_bbox():
    """Device scale changes cut bbox; feed offset is relative to that bbox."""
    job = _job_with_doc(feed_to_end=True, feed_after=10)
    plan_1 = job.build_plan(
        swap_xy=False, scale=[1, 1],
        origin_position='bottom_left', feed_axis='y')
    plan_2 = job.build_plan(
        swap_xy=False, scale=[2, 2],
        origin_position='bottom_left', feed_axis='y')
    e1 = _epilogue_end(plan_1)
    e2 = _epilogue_end(plan_2)
    assert e1[0] == pytest.approx(0.0) and e2[0] == pytest.approx(0.0)
    # Scaled cuts extend further; feed is still bbox.top - feed_after
    assert e2[1] == pytest.approx(plan_2.bounds.top() - 10)
    assert abs(e2[1]) > abs(e1[1])


def test_frame_helpers_feed_and_origin():
    bbox = QRectF(10, -40, 80, 50)
    assert feed_vector('y', 'negative') == QPointF(0.0, -1.0)
    assert feed_vector('x', 'positive') == QPointF(1.0, 0.0)
    end = feed_end_point(bbox, 'y', 'negative', 12)
    assert end.x() == pytest.approx(0.0)
    assert end.y() == pytest.approx(bbox.top() - 12)

    ox, oy = origin_shift(bbox, 'bottom_left')
    t = design_to_machine_transform(bbox, 'bottom_left')
    p = t.map(bbox.bottomLeft())
    assert p.x() == pytest.approx(0.0)
    assert p.y() == pytest.approx(0.0)
    assert ox == pytest.approx(-bbox.bottomLeft().x())
    assert oy == pytest.approx(-bbox.bottomLeft().y())

    mat = material_rect((100, 200), 'bottom_right')
    assert mat.right() == pytest.approx(0.0)
    assert mat.bottom() == pytest.approx(0.0)
    assert mat.width() == pytest.approx(100.0)


def test_default_build_plan_is_physical_no_implicit_protocol():
    """Without explicit scale/swap, plan stays physical (identity protocol)."""
    job = _job_with_doc(feed_to_end=False)
    plan = job.build_plan(
        origin_corner='bottom_left', feed_axis='y', feed_sense='negative')
    assert plan is not None
    assert plan.origin.x() == pytest.approx(0.0)
    assert plan.origin.y() == pytest.approx(0.0)


def test_return_epilogue_at_machine_origin_pre_protocol():
    """Return epilogue endpoint is machine (0,0) in the plan (pre-protocol)."""
    job = _job_with_doc(feed_to_end=False)
    plan = job.build_plan(
        origin_corner='bottom_right', feed_axis='x',
        feed_sense='positive', epilogue='return')
    ex, ey = _epilogue_end(plan)
    assert ex == pytest.approx(0.0)
    assert ey == pytest.approx(0.0)


def test_device_protocol_applied_after_physical_plan():
    """Device.init maps physical plan → protocol; return stays at origin."""
    from inkcut.device.plugin import Device, DeviceConfig
    from inkcut.device.extensions import DeviceDriver

    job = _job_with_doc(feed_to_end=False)
    config = DeviceConfig(
        scale=[2.0, 2.0], swap_xy=False, mirror_x=False, mirror_y=False,
        origin_position='bottom_left', feed_axis='y', feed_sense='negative',
        test_mode=True,
    )
    device = Device(config=config, declaration=DeviceDriver())
    physical = job.build_plan(
        origin_corner='bottom_left', feed_axis='y', epilogue='return')
    assert _epilogue_end(physical) == pytest.approx((0.0, 0.0))

    protocol = device._apply_protocol_to_plan(physical, job)
    assert protocol is not None
    # Scaled cuts are larger
    assert protocol.bounds.width() == pytest.approx(
        physical.bounds.width() * 2.0, rel=1e-6)
    assert protocol.bounds.height() == pytest.approx(
        physical.bounds.height() * 2.0, rel=1e-6)
    # Return epilogue still machine origin after protocol
    ex, ey = _epilogue_end(protocol)
    assert ex == pytest.approx(0.0)
    assert ey == pytest.approx(0.0)


def test_device_protocol_feed_uses_post_map_bbox():
    """After protocol scale, feed-after is relative to mapped cut bbox."""
    from inkcut.device.plugin import Device, DeviceConfig
    from inkcut.device.extensions import DeviceDriver

    job = _job_with_doc(feed_to_end=True, feed_after=10)
    config = DeviceConfig(
        scale=[2.0, 2.0], origin_position='bottom_left',
        feed_axis='y', feed_sense='negative', test_mode=True,
    )
    device = Device(config=config, declaration=DeviceDriver())
    physical = job.build_plan(
        origin_corner='bottom_left', feed_axis='y', feed_sense='negative')
    protocol = device._apply_protocol_to_plan(physical, job)
    ex, ey = _epilogue_end(protocol)
    assert ex == pytest.approx(0.0)
    assert ey == pytest.approx(protocol.bounds.top() - 10)
    assert abs(ey) > abs(_epilogue_end(physical)[1])
