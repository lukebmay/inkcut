# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jun 11, 2015

@author: jrm
"""
from atom.atom import set_default
from atom.api import (
    Callable, Tuple, Float, Int, List, ContainerList, Bool, FloatRange, Str,
    Dict, Typed, ForwardTyped, observe
)
from enaml.core.declarative import d_
from enaml.qt.qt_application import QtApplication
from enaml.qt.qt_control import QtControl
from enaml.qt import QtGui
from enaml.qt.QtCore import QTimer
from enaml.widgets.control import Control, ProxyControl
from pyqtgraph.widgets.PlotWidget import PlotWidget
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyqtgraph.graphicsItems.ViewBox.ViewBox import ViewBox
from pyqtgraph.graphicsItems.AxisItem import AxisItem
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject


class PainterPathPlotItem(PlotCurveItem):

    def updateData(self, path, **kargs):
        # Invert for display
        self.path = QtGui.QTransform.fromScale(1, -1).map(path)

        # Trick the checks so it still paints
        bbox = self.path.boundingRect()
        self.xData = [bbox.left(), bbox.right()]
        self.yData = [bbox.bottom(), bbox.top()]

        if 'skip_autorange' in kargs:
            skip = (True, True)
            if isinstance(kargs['skip_autorange'], (list, tuple)):
                skip = kargs['skip_autorange']
            if skip[0]:
                if isinstance(skip[0], (list, tuple)):
                    self.xData = skip[0]
                else:
                    self.xData = [0]
            if skip[1]:
                if isinstance(skip[1], (list, tuple)):
                    self.yData = skip[1]
                else:
                    self.yData = [0]

        ##    Test this bug with test_PlotWidget and zoom in on the animated plot
        self.invalidateBounds()
        self.prepareGeometryChange()
        self.informViewBoundsChanged()

        self.fillPath = None
        self._mouseShape = None

        if 'name' in kargs:
            self.opts['name'] = kargs['name']
        if 'connect' in kargs:
            self.opts['connect'] = kargs['connect']
        if 'pen' in kargs:
            self.setPen(kargs['pen'])
        if 'shadowPen' in kargs:
            self.setShadowPen(kargs['shadowPen'])
        if 'fillLevel' in kargs:
            self.setFillLevel(kargs['fillLevel'])
        if 'brush' in kargs:
            self.setBrush(kargs['brush'])
        if 'antialias' in kargs:
            self.opts['antialias'] = kargs['antialias']

        self.update()
        self.sigPlotChanged.emit(self)

    def boundingRect(self):
        return self.path.boundingRect()

    def getPath(self):
        return self.path


class ProxyPlotView(ProxyControl):
    declaration = ForwardTyped(lambda: PlotView)

    def set_data(self, data):
        raise NotImplementedError

    def set_antialiasing(self, enabled):
        raise NotImplementedError


class PlotView(Control):
    hug_width = set_default('ignore')
    hug_height = set_default('ignore')
    proxy = Typed(ProxyPlotView)
    data = d_(ContainerList())
    setup = d_(Callable(lambda graph: None))

    title = d_(Str())
    labels = d_(Dict(Str(), Str()))

    axis_scales = d_(Dict(Str(), Float()))

    #background_color = d_(Str())
    #foreground = d_(Str())

    antialiasing = d_(Bool(True))
    aspect_locked = d_(Bool(True))
    range_padding = d_(Float(0.02))
    # Fit when the picture is replaced, then leave the zoom alone.
    fit_once = d_(Bool(False))

    grid = d_(Tuple(item=Bool(), default=(False, False)))
    grid_alpha = d_(FloatRange(low=0.0, high=1.0, value=0.5))

    multi_axis = d_(Bool(True))

    @observe('data', 'title', 'labels', 'multi_axis', 'antialiasing',
             'axis_scales', 'grid', 'grid_alpha')
    def _update_proxy(self, change):
        """ An observer which sends state change to the proxy.
        """
        # The superclass handler implementation is sufficient.
        super(PlotView, self)._update_proxy(change)


class QtPlotView(QtControl, ProxyPlotView):
    __weakref__ = None
    widget = Typed(PlotWidget)
    _views = List()
    _colors = List(default=['r', 'g', 'b'])
    # Bumps when the picture is replaced so a stale fit cannot clear it.
    _fit_token = Int(0)
    _fit_waiter = Callable()
    _fit_callback = Callable()

    def create_widget(self):
        self.widget = PlotWidget(self.parent_widget(), background='w')

    def init_widget(self):
        super(QtPlotView, self).init_widget()
        d = self.declaration
        #self.widget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        # Scale and aspect before the picture, so the one fit is final.
        self.set_antialiasing(d.antialiasing)
        self.set_aspect_locked(d.aspect_locked)
        self.widget.getViewBox().setDefaultPadding(d.range_padding)
        self.set_axis_scales(d.axis_scales)
        self.set_labels(d.labels)
        self.widget.showGrid(d.grid[0], d.grid[1], d.grid_alpha)
        self.set_data(d.data)

        d.setup(self.widget)

    def set_title(self, title):
        self.set_labels(self.declaration.labels)

    def set_labels(self, labels):
        if self.declaration.title:
            labels['title'] = self.declaration.title
        self.widget.setLabels(**labels)

    def set_antialiasing(self, enabled):
        self.widget.setAntialiasing(enabled)

    def set_aspect_locked(self, locked):
        self.widget.setAspectLocked(locked)

    def set_axis_scales(self, scales):
        if not scales:
            return
        for k, v in scales.items():
            if k in self.widget.plotItem.axes:
                self.widget.plotItem.axes[k]['item'].setScale(v)

    def set_grid(self, grid):
        d = self.declaration
        self.widget.showGrid(grid[0], grid[1], d.grid_alpha)

    def set_grid_alpha(self, alpha):
        d = self.declaration
        self.widget.showGrid(d.grid[0], d.grid[1], alpha)

    def set_data(self, data):
        self.widget.clear()
        if not data:
            self._cancel_fit()
            return

        if isinstance(data, (list, tuple)) and \
                isinstance(data[0], GraphicsObject):
            self._set_graphic_items(data)
        else:
            self._cancel_fit()
            self._set_numeric_data(data)

    def _cancel_fit(self):
        self._fit_token += 1
        self._drop_fit_waiter()
        self._fit_callback = None

    def _drop_fit_waiter(self):
        waiter = self._fit_waiter
        self._fit_waiter = None
        if waiter is None or self.widget is None:
            return
        try:
            self.widget.getViewBox().sigResized.disconnect(waiter)
        except TypeError:
            pass

    def _arm_fit(self):
        # After this replace returns. Fitting here re-enters set_data.
        self._drop_fit_waiter()
        self._fit_token += 1
        token = self._fit_token

        def _fire():
            self._finish_fit(token)

        self._fit_callback = _fire
        QTimer.singleShot(0, _fire)

    def _finish_fit(self, token):
        if token != self._fit_token or self.widget is None:
            return
        view = self.widget.getViewBox()
        if view.width() <= 1 or view.height() <= 1:
            self._wait_for_pixels(view)
            return
        self._reserve_tick_space()
        if token != self._fit_token:
            return
        view.autoRange()

    def _wait_for_pixels(self, view):
        def _resized(*_args):
            self._drop_fit_waiter()
            self._arm_fit()

        self._fit_waiter = _resized
        view.sigResized.connect(_resized)

    def _reserve_tick_space(self):
        # Fixed tick columns. A measured width of 0 would reserve QWIDGETSIZE_MAX.
        plot = self.widget.plotItem
        left = plot.getAxis('left')
        bottom = plot.getAxis('bottom')
        for axis in (left, bottom):
            if axis is None:
                continue
            axis.setStyle(
                autoExpandTextSpace=False,
                autoReduceTextSpace=False,
                tickTextWidth=30,
                tickTextHeight=18,
            )
        if left is not None:
            left.setWidth(None)
        if bottom is not None:
            bottom.setHeight(None)

    def _set_graphic_items(self, items):
        self.widget.clear()
        for item in items:
            self.widget.addItem(item)
        if self.declaration.fit_once and items:
            self._arm_fit()
            return
        if self.declaration.fit_once:
            self._cancel_fit()

    def _set_numeric_data(self, data):
        self.widget.plotItem.clear()
        if self._views:
            for view in self._views:
                view.clear()

        views = []
        i = 0
        if self.declaration.multi_axis:
            for i, plot in enumerate(data):
                if i > 3:
                    break
                if 'pen' not in plot:
                    plot['pen'] = self._colors[i]
                if i > 0:
                    view = ViewBox()
                    views.append(view)
                    self.widget.plotItem.scene().addItem(view)
                    if i == 1:
                        axis = self.widget.plotItem.getAxis('right')
                    elif i > 1:
                        axis = AxisItem('right')
                        axis.setZValue(-10000)
                        self.widget.plotItem.layout.addItem(axis, 2, 3)
                    axis.linkToView(view)
                    view.setXLink(self.widget.plotItem)
                    view.addItem(PlotCurveItem(**plot))
                else:
                    self.widget.plot(**plot)
        if i > 0:
            def syncViews():
                for v in views:
                    v.setGeometry(self.widget.plotItem.vb.sceneBoundingRect())
                    v.linkedViewChanged(self.widget.plotItem.vb, v.XAxis)
            syncViews()
            self.widget.plotItem.vb.sigResized.connect(syncViews)
        self._views = views


def plot_view_factory():
    return QtPlotView


# Inject the factory
QtApplication.instance().resolver.factories.update({
    'PlotView': plot_view_factory
})
