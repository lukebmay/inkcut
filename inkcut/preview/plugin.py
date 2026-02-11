"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jun 11, 2015

@author: jrm
"""
import pyqtgraph as pg
from atom.api import List, Instance, Enum, Bool, Range
from enaml.qt import QtCore, QtGui
from inkcut.core.api import Plugin, Model, unit_conversions, log
from .plot_view import PainterPathPlotItem
from .indicators import OriginIndicator, FeedDirectionIndicator
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject

QPen = QtGui.QPen


class PreviewModel(Model):
    #: List of plot items to display
    plot = List()

    #: Internal paths for drawing
    paths = List(QtGui.QPainterPath)

    #: Colors
    pen_media = Instance(QPen)
    pen_media_padding = Instance(QPen)
    pen_up = Instance(QPen)
    pen_offset = Instance(QPen)
    pen_down = Instance(QPen)
    pen_device = Instance(QPen)
    pen_origin = Instance(QPen)

    def _default_pen_media(self):
        return pg.mkPen((128, 128, 128))

    def _default_pen_media_padding(self):
        return pg.mkPen((128, 128, 128), style=QtCore.Qt.DashLine)

    def _default_pen_device(self):
        return pg.mkPen((235, 194, 194), style=QtCore.Qt.DashLine)

    def _default_pen_up(self):
        return pg.mkPen(hsv=(0.53, 1, 0.5, 0.5))

    def _default_pen_offset(self):
        return pg.mkPen(hsv=(0.43, 1, 0.5, 0.5))

    def _default_pen_down(self):
        return pg.mkPen((128, 128, 128))

    def _default_pen_origin(self):
        return pg.mkPen((0, 0, 0), width=2)

    def init(self, view_items):
        default_items = []
        self.paths = [QtGui.QPainterPath(), QtGui.QPainterPath()]

        default_items.append(
            PainterPathPlotItem(self.paths[0], pen=self.pen_down))
        default_items.append(
            PainterPathPlotItem(self.paths[1], pen=self.pen_up))
        self.plot = default_items + view_items

    def update(self, position):
        """ Watch the position of the device as it changes. """
        if not self.paths:
            return
        x, y, z = position
        if z:
            self.paths[0].lineTo(x, -y)
            self.paths[1].moveTo(x, -y)
            self.plot[0].updateData(self.paths[0])
        else:
            self.paths[0].moveTo(x, -y)
            self.paths[1].lineTo(x, -y)
            self.plot[1].updateData(self.paths[1])


class PreviewPlugin(Plugin):

    #: Set's the plot that is drawn in the preview
    preview = Instance(PreviewModel, ())

    #: Plot for showing live status
    live_preview = Instance(PreviewModel, ())

    #: Transform applied to all view items
    transform = Instance(QtGui.QTransform)

    show_grid_x = Bool().tag(config=True)
    show_grid_y = Bool().tag(config=True)
    grid_alpha = Range(value=30, low=1, high=100).tag(config=True)

    def _default_transform(self):
        """ Qt displays top to bottom so this can be used to flip it.

        """
        return QtGui.QTransform.fromScale(1, -1)

    def set_preview(self, *items, device=None):
        """ Sets the items that will be displayed in the plot

        Parameters
        ----------
        items: list of kwargs or GraphicsObject
            A list of kwargs to pass to each plot item, or GraphicsObject items
        device: Device instance (optional)
            Device configuration for adding origin and feed direction indicators

        """
        t = self.transform
        view_items = []
        for item in items:
            # If it's a dict with 'path', convert to PainterPathPlotItem
            if isinstance(item, dict) and 'path' in item:
                kwargs = item.copy()
                view_items.append(
                    PainterPathPlotItem(kwargs.pop('path'), **kwargs))
            # If it's already a GraphicsObject, add it directly
            elif isinstance(item, GraphicsObject):
                view_items.append(item)

        # Add origin and feed direction indicators if device is provided
        if device:
            origin_indicator = OriginIndicator(
                x=0, y=0, origin_position=device.config.origin_position)
            view_items.append(origin_indicator)

            # Calculate material dimensions for feed indicator
            if device.area:
                material_width = device.area.size[0]
                material_height = device.area.size[1]
            else:
                material_width = 100
                material_height = 100

            feed_indicator = FeedDirectionIndicator(
                x=0,
                y=0,
                feed_axis=device.config.feed_axis,
                origin_position=device.config.origin_position,
                material_width=material_width,
                material_height=material_height)
            view_items.append(feed_indicator)

        self.preview.plot = view_items

    def set_live_preview(self, *items, device=None):
        """ Set the items that will be displayed in the live plot preview.
        After set, use live_preview.update(position) to update it.

        Parameters
        ----------
        items: list of kwargs or GraphicsObject
            A list of kwargs to pass to each plot item, or GraphicsObject items
        device: Device instance (optional)
            Device configuration for adding origin and feed direction indicators


        """
        view_items = []
        for item in items:
            # If it's a dict with 'path', convert to PainterPathPlotItem
            if isinstance(item, dict) and 'path' in item:
                kwargs = item.copy()
                view_items.append(
                    PainterPathPlotItem(kwargs.pop('path'), **kwargs))
            # If it's already a GraphicsObject, add it directly
            elif isinstance(item, GraphicsObject):
                view_items.append(item)

        # Add origin and feed direction indicators if device is provided
        if device:
            origin_indicator = OriginIndicator(
                x=0, y=0, origin_position=device.config.origin_position)
            view_items.append(origin_indicator)

            # Calculate material dimensions for feed indicator
            if device.area:
                material_width = device.area.size[0]
                material_height = device.area.size[1]
            else:
                material_width = 100
                material_height = 100

            feed_indicator = FeedDirectionIndicator(
                x=0,
                y=0,
                feed_axis=device.config.feed_axis,
                origin_position=device.config.origin_position,
                material_width=material_width,
                material_height=material_height)
            view_items.append(feed_indicator)

        self.live_preview.init(view_items)
