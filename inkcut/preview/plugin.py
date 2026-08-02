"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import pyqtgraph as pg
from atom.api import List, Instance, Enum, Bool, Range, observe
from enaml.qt import QtCore, QtGui
from enaml.qt.QtWidgets import QApplication
from inkcut.core.api import Plugin, Model, unit_conversions, log
from .plot_view import PainterPathPlotItem
from . import indicators


QPen = QtGui.QPen


def _tr(text):
    return QApplication.translate("preview", text)


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
    pen_weed = Instance(QPen)
    pen_epilogue = Instance(QPen)
    pen_origin = Instance(QPen)
    pen_feed = Instance(QPen)

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

    def _default_pen_weed(self):
        return pg.mkPen(hsv=(0.08, 0.9, 0.85, 0.9))

    def _default_pen_epilogue(self):
        return pg.mkPen(hsv=(0.53, 1, 0.5, 0.7), style=QtCore.Qt.DashLine)

    def _default_pen_origin(self):
        return pg.mkPen((200, 40, 40), width=2)

    def _default_pen_feed(self):
        return pg.mkPen((40, 90, 200), width=2)

    def init(self, view_items):
        default_items = []
        self.paths = [QtGui.QPainterPath(), QtGui.QPainterPath()]

        default_items.append(PainterPathPlotItem(
            self.paths[0], pen=self.pen_down))
        default_items.append(PainterPathPlotItem(
            self.paths[1], pen=self.pen_up))
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

    #: Layer visibility (precut + live static layers)
    show_cuts = Bool(True).tag(config=True)
    show_travel = Bool(True).tag(config=True)
    show_weeds = Bool(True).tag(config=True)
    show_origin = Bool(True).tag(config=True)
    show_feed = Bool(True).tag(config=True)
    #: Corner legend of named pens on precut + live plots
    show_legend = Bool(True).tag(config=True)

    def _default_transform(self):
        """ Qt displays top to bottom so this can be used to flip it.

        """
        return QtGui.QTransform.fromScale(1, -1)

    def set_preview(self, *items):
        """ Sets the items that will be displayed in the plot

        Parameters
        ----------
        items: list of kwargs
            A list of kwargs to to pass to each plot item

        """
        t = self.transform
        view_items = [
            PainterPathPlotItem(kwargs.pop('path'), **kwargs)
            for kwargs in items
        ]
        self.preview.plot = view_items

    def set_live_preview(self, *items):
        """ Set the items that will be displayed in the live plot preview.
        After set, use live_preview.update(position) to update it.

        Parameters
        ----------
        items: list of kwargs
            A list of kwargs to to pass to each plot item


        """
        view_items = [
            PainterPathPlotItem(kwargs.pop('path'), **kwargs)
            for kwargs in items
        ]
        self.live_preview.init(view_items)

    def layer_view_items(self, plot, plan=None, move_path=None, cut_path=None,
                         origin=None, feed_direction=None, size=None,
                         map_path=None):
        """Build cut/travel/weed/epilogue + origin/feed items from toggles.

        map_path: optional callable(path) -> path applied to every layer path.
        Each item may include ``name`` for the plot legend.
        """
        map_path = map_path or (lambda p: p)
        layers = indicators.plan_layer_paths(
            plan=plan, move_path=move_path, cut_path=cut_path)
        items = []

        if self.show_travel and not layers['travel'].isEmpty():
            items.append(dict(
                path=map_path(layers['travel']),
                pen=plot.pen_up,
                name=_tr("Travel"),
            ))
        if self.show_cuts and not layers['cut'].isEmpty():
            items.append(dict(
                path=map_path(layers['cut']),
                pen=plot.pen_down,
                name=_tr("Cuts"),
            ))
        if self.show_weeds and not layers['weed'].isEmpty():
            items.append(dict(
                path=map_path(layers['weed']),
                pen=plot.pen_weed,
                name=_tr("Weed lines"),
            ))
        if self.show_travel and not layers['epilogue'].isEmpty():
            items.append(dict(
                path=map_path(layers['epilogue']),
                pen=plot.pen_epilogue,
                name=_tr("Epilogue"),
            ))

        arm = indicators.indicator_length(size)
        if origin is None and plan is not None:
            origin = plan.origin
        if feed_direction is None:
            feed_direction = indicators.resolve_feed_direction(plan=plan)

        if self.show_origin:
            o_path = indicators.origin_crosshair_path(origin=origin, arm=arm * 0.35)
            items.append(dict(
                path=map_path(o_path),
                pen=plot.pen_origin,
                skip_autorange=True,
                name=_tr("Origin"),
            ))
        if self.show_feed and feed_direction is not None:
            f_path = indicators.feed_arrow_path(
                origin=origin, direction=feed_direction, length=arm)
            items.append(dict(
                path=map_path(f_path),
                pen=plot.pen_feed,
                skip_autorange=True,
                name=_tr("Feed direction"),
            ))
        return items

    @observe('show_cuts', 'show_travel', 'show_weeds', 'show_origin',
             'show_feed')
    def _on_layer_toggle(self, change):
        if change.get('type') != 'update':
            return
        wb = self.workbench
        if wb is None:
            return
        try:
            wb.get_plugin('inkcut.job').refresh_preview()
        except Exception as e:
            log.debug("preview toggle job refresh: %s" % e)
        try:
            wb.get_plugin('inkcut.device').reset_preview()
        except Exception as e:
            log.debug("preview toggle live refresh: %s" % e)
