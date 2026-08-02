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
    Callable, Tuple, Float, List, ContainerList, Bool, FloatRange, Str,
    Dict, Typed, ForwardTyped, observe
)
from enaml.core.declarative import d_
from enaml.qt.qt_application import QtApplication
from enaml.qt.qt_control import QtControl
from enaml.qt import QtGui
from enaml.widgets.control import Control, ProxyControl
from pyqtgraph.widgets.PlotWidget import PlotWidget
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyqtgraph.graphicsItems.ViewBox.ViewBox import ViewBox
from pyqtgraph.graphicsItems.AxisItem import AxisItem
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject


class PainterPathPlotItem(PlotCurveItem):
    """Plot item backed by a QPainterPath (not x/y arrays).

    Construction: ``PainterPathPlotItem(path, pen=..., name=..., skip_autorange=...)``.
    Path is not passed to PlotCurveItem.setData (arrays only).
    """

    def __init__(self, path=None, **kargs):
        # Parent init with no data args (never QPainterPath into setData).
        pen = kargs.pop('pen', None)
        name = kargs.pop('name', None)
        skip = kargs.pop('skip_autorange', None)
        shadow = kargs.pop('shadowPen', None)
        self.path = QtGui.QPainterPath()
        PlotCurveItem.__init__(self)
        if pen is not None:
            self.setPen(pen)
        if shadow is not None:
            self.setShadowPen(shadow)
        if name is not None:
            self.opts['name'] = name
        if path is not None:
            opts = dict(kargs)
            if pen is not None:
                opts['pen'] = pen
            if name is not None:
                opts['name'] = name
            if skip is not None:
                opts['skip_autorange'] = skip
            if shadow is not None:
                opts['shadowPen'] = shadow
            self.updateData(path, **opts)

    def updateData(self, *args, **kargs):
        """Load a QPainterPath, or accept empty parent setData() during init."""
        if not args:
            # PlotCurveItem.__init__ → setData() → updateData() with no geometry
            if 'name' in kargs:
                self.opts['name'] = kargs['name']
            if 'pen' in kargs:
                self.setPen(kargs['pen'])
            return
        path = args[0]
        if not isinstance(path, QtGui.QPainterPath):
            return

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
        if not hasattr(self, 'path') or self.path is None:
            return QtGui.QPainterPath().boundingRect()
        return self.path.boundingRect()

    def getPath(self):
        if not hasattr(self, 'path') or self.path is None:
            return QtGui.QPainterPath()
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

    grid = d_(Tuple(item=Bool(), default=(False, False)))
    grid_alpha = d_(FloatRange(low=0.0, high=1.0, value=0.5))

    #: pyqtgraph corner legend for named plot items
    show_legend = d_(Bool(True))

    multi_axis = d_(Bool(True))

    @observe('data', 'title', 'labels', 'multi_axis', 'antialiasing',
             'axis_scales', 'grid', 'grid_alpha', 'show_legend')
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

    def create_widget(self):
        self.widget = PlotWidget(self.parent_widget(), background='w')

    def init_widget(self):
        super(QtPlotView, self).init_widget()
        d = self.declaration
        #self.widget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.set_show_legend(d.show_legend)
        self.set_data(d.data)
        self.set_antialiasing(d.antialiasing)
        self.set_aspect_locked(d.aspect_locked)
        self.set_axis_scales(d.axis_scales)
        self.set_labels(d.labels)
        self.widget.showGrid(d.grid[0], d.grid[1], d.grid_alpha)

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

    def set_show_legend(self, show):
        """Create or hide the plot legend. Named items auto-register on add."""
        plot_item = self.widget.plotItem
        if show:
            if plot_item.legend is None:
                plot_item.addLegend(offset=(10, 10))
            else:
                plot_item.legend.show()
        elif plot_item.legend is not None:
            plot_item.legend.hide()

    def set_data(self, data):
        legend = getattr(self.widget.plotItem, 'legend', None)
        if legend is not None:
            legend.clear()
        self.widget.clear()
        # clear() keeps the LegendItem; restore visibility from declaration
        self.set_show_legend(self.declaration.show_legend)
        if not data:
            return

        if isinstance(data, (list, tuple)) and \
                isinstance(data[0], GraphicsObject):
            self._set_graphic_items(data)
        else:
            self._set_numeric_data(data)

    def _set_graphic_items(self, items):
        for item in items:
            self.widget.addItem(item)

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


def _register_plot_view_factory():
    app = QtApplication.instance()
    if app is not None and getattr(app, 'resolver', None) is not None:
        app.resolver.factories.update({'PlotView': plot_view_factory})


_register_plot_view_factory()
