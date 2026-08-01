"""
Copyright (c) 2022, Karlis Senko

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Nov 3, 2022

@author: karliss
"""
import pytest
from pytest import approx
from enaml.qt.QtGui import QVector2D
from glob import glob

from inkcut.core.svg import QtSvgDoc
from inkcut.core.api import to_unit, from_unit
import inkcut.device.filters.blade_offset as blade_offset
import inkcut.device.filters.min_line as min_line
import inkcut.core.utils as utils
import inkcut.job.models

from inkcut.device.plugin import DeviceConfig, Device
from inkcut.device.extensions import DeviceDriver


DATA_PREFIX = "tests/data/filters"


@pytest.fixture(scope="module")
def test_device():
    config = DeviceConfig()
    config.test_mode = True
    return Device(config=config, declaration=DeviceDriver())


@pytest.mark.parametrize("path", glob("tests/data/*.svg"))
def test_blade_offset_basic(test_device, path):
    """Just check that the filter runs and there are no API incompatibilities with current qt version"""
    job = inkcut.job.models.Job()
    doc = QtSvgDoc(path)
    config = blade_offset.BladeOffsetConfig()
    config.offset = from_unit(1, "mm")
    offset_filter = blade_offset.BladeOffsetFilter(config=config)
    filtered_path = offset_filter.apply_to_model(doc, test_device)
    assert filtered_path


mingap_testdata = [
    (0, 6),  # disable at 0, event when there are points with matching position
    (0.01, 5),
    (0.025, 4),
    (0.06, 3),
    (0.11, 2),
    (0.22, 1),
]


@pytest.fixture(scope="module")
def mingap_doc():
    return QtSvgDoc(DATA_PREFIX + "/mingap.svg")


@pytest.mark.parametrize("setting,expected_count", mingap_testdata)
def test_minline_gap(mingap_doc, setting, expected_count):
    config = min_line.MinLineConfig()
    config.min_jump = from_unit(setting, "mm")
    minline_filter = min_line.MinLineFilter(config=config)
    result = minline_filter.apply_to_model(mingap_doc, None)
    parts = utils.split_painter_path(result)
    assert len(parts) == expected_count


min_shift_expected_result = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0]


@pytest.fixture(scope="module")
def min_shift_fixture():
    doc = QtSvgDoc(DATA_PREFIX + "/min_shift_1.svg")
    input_parts = utils.split_painter_path(doc)
    assert len(min_shift_expected_result) == len(input_parts)

    config = min_line.MinLineConfig()

    minline_filter = min_line.MinLineFilter(config=config)

    config.min_shift = from_unit(0.001, "mm")
    filtered = minline_filter.apply_to_model(doc, None)
    parts = utils.split_painter_path(filtered)
    assert len(parts) == len(min_shift_expected_result)
    # shouldn't simplify anything with min_shift 0.001
    for part in parts:
        assert part.elementCount() == 4

    config.min_shift = from_unit(0.01, "mm")
    filtered = minline_filter.apply_to_model(doc, None)
    parts = utils.split_painter_path(filtered)
    assert len(parts) == len(min_shift_expected_result)
    return parts, input_parts


@pytest.mark.parametrize("i, expected", enumerate(min_shift_expected_result))
def test_minline_shift(i, expected, min_shift_fixture):
    parts = min_shift_fixture[0]
    input_parts = min_shift_fixture[1]

    part = parts[i]
    input_part = input_parts[i]
    if expected:
        assert part.elementCount() == 3
    else:
        assert part.elementCount() == 4

    start = part.elementAt(0)
    start_expected = input_part.elementAt(0)
    assert (start.x, start.y) == approx((start_expected.x, start_expected.y))

    end = part.elementAt(part.elementCount() - 1)
    end_expected = input_part.elementAt(input_part.elementCount() - 1)
    assert (end.x, end.y) == approx((end_expected.x, end_expected.y))


@pytest.mark.parametrize("path", glob("tests/data/*.svg"))
def test_minlineshift_basic(path):
    """Just check that the filter runs and there are no API incompatibilities with current qt version"""
    doc = QtSvgDoc(path)
    config = min_line.MinLineConfig()
    config.min_shift = from_unit(0.1, "mm")
    minline_filter = min_line.MinLineFilter(config=config)
    result = minline_filter.apply_to_model(doc, None)
    assert result


def test_min_path():
    """Test that paths of corresponding lengths get removed. Test case contains both squares and circles."""
    doc = QtSvgDoc(DATA_PREFIX + "/min_path.svg")
    config = min_line.MinLineConfig()

    config.min_path = from_unit(0.0, "mm")
    minline_filter = min_line.MinLineFilter(config=config)
    result = minline_filter.apply_to_model(doc, None)

    assert (
        len(utils.split_painter_path(result)) == 6
    )  # nothing should be removed with min_path 0

    config.min_path = from_unit(0.3, "mm")
    result = minline_filter.apply_to_model(doc, None)

    assert (
        len(utils.split_painter_path(result)) == 6
    )  # everything in testcase should still be longer than this

    config.min_path = from_unit(0.41, "mm")
    result = minline_filter.apply_to_model(doc, None)

    assert len(utils.split_painter_path(result)) == 4

    config.min_path = from_unit(0.6, "mm")
    result = minline_filter.apply_to_model(doc, None)

    assert len(utils.split_painter_path(result)) == 2

    config.min_path = from_unit(5, "mm")
    result = minline_filter.apply_to_model(doc, None)

    assert len(utils.split_painter_path(result)) == 0


def test_process_filters_skip_epilogue():
    """Device.process must not filter return-to-origin / feed epilogue."""
    from enaml.qt.QtCore import QPointF
    from enaml.qt.QtGui import QPainterPath, QTransform
    from inkcut.device.extensions import DeviceDriver
    from inkcut.device.plugin import Device, DeviceConfig, DeviceFilter
    from inkcut.job.toolpath import PathSegment, ToolpathPlan

    class ShiftFilter(DeviceFilter):
        def apply_to_model(self, model, job=None):
            return QTransform.fromTranslate(50, 0).map(model)

    config = DeviceConfig(test_mode=True, interpolate=False, spooled=True)
    device = Device(config=config, declaration=DeviceDriver())
    device.filters = [ShiftFilter()]
    device.origin = [0, 0, 0]

    cut = QPainterPath()
    cut.moveTo(0, 0)
    cut.lineTo(10, 0)
    cut.lineTo(10, 10)
    cut.lineTo(0, 10)
    cut.closeSubpath()

    epi = QPainterPath()
    epi.moveTo(0, 0)

    plan = ToolpathPlan(segments=[
        PathSegment('cut', cut),
        PathSegment('epilogue', epi, meta={'mode': 'return', 'end': QPointF(0, 0)}),
    ])
    device._process_plan = plan
    device._stream_offset = (0.0, 0.0)
    stream = plan.to_device_stream()

    moves = []
    for dist, cmd, args, kwargs in device.process(stream):
        pos = args[0]
        moves.append(tuple(pos))

    # Final absolute position must remain machine origin (unfiltered)
    assert moves[-1][0] == approx(0.0)
    assert moves[-1][1] == approx(0.0)

    # Cut geometry was shifted by the filter (+50 in pre-Y-flip x → device x)
    xs = [m[0] for m in moves[:-1]]
    assert max(xs) >= 50.0


def test_process_filters_skip_epilogue_with_typed_travel():
    """Filters shift cuts; travel is pen-up; epilogue stays at origin."""
    from enaml.qt.QtCore import QPointF
    from enaml.qt.QtGui import QPainterPath, QTransform
    from inkcut.device.extensions import DeviceDriver
    from inkcut.device.plugin import Device, DeviceConfig, DeviceFilter
    from inkcut.job.toolpath import PathSegment, ToolpathPlan

    class ShiftFilter(DeviceFilter):
        def apply_to_model(self, model, job=None):
            return QTransform.fromTranslate(50, 0).map(model)

    config = DeviceConfig(test_mode=True, interpolate=False, spooled=True)
    device = Device(config=config, declaration=DeviceDriver())
    device.filters = [ShiftFilter()]
    device.origin = [0, 0, 0]

    cut_a = QPainterPath()
    cut_a.moveTo(0, 0)
    cut_a.lineTo(10, 0)
    cut_a.lineTo(10, 10)
    cut_a.lineTo(0, 10)
    cut_a.closeSubpath()

    travel = QPainterPath()
    travel.moveTo(0, 10)
    travel.lineTo(30, 0)

    cut_b = QPainterPath()
    cut_b.moveTo(30, 0)
    cut_b.lineTo(40, 0)
    cut_b.lineTo(40, 10)
    cut_b.lineTo(30, 10)
    cut_b.closeSubpath()

    epi = QPainterPath()
    epi.moveTo(0, 0)

    plan = ToolpathPlan(segments=[
        PathSegment('cut', cut_a),
        PathSegment('travel', travel, meta={
            'start': QPointF(0, 10), 'end': QPointF(30, 0)}),
        PathSegment('cut', cut_b),
        PathSegment('epilogue', epi, meta={'mode': 'return', 'end': QPointF(0, 0)}),
    ])
    device._process_plan = plan
    device._stream_offset = (0.0, 0.0)
    stream = plan.to_device_stream()

    moves = []
    for dist, cmd, args, kwargs in device.process(stream):
        pos = args[0]
        moves.append(tuple(pos))

    assert moves[-1][0] == approx(0.0)
    assert moves[-1][1] == approx(0.0)
    # Cuts were filtered (shifted); epilogue was not
    xs = [m[0] for m in moves[:-1]]
    assert max(xs) >= 50.0
