# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 16, 2015

@author: jrm
"""

from atom.api import Typed, Instance
from inkcut.core.api import Model
from . import extensions


class DeviceFilter(Model):
    """ A device filter is applied to apply either the QPainterPath or to the
    list of polygons generated when the path is converted to simple move
    and line segments.

    """

    #: The declaration that defined this filter
    declaration = Typed(extensions.DeviceFilter).tag(config=True)

    #: The protocol specific config
    config = Instance(Model, ()).tag(config=True)

    def apply_to_model(self, model, job):
        """ Apply the filter to the model

        Parameters
        ----------
        model: QPainterPath
            The path model to process
        job: inkcut.device.Job
            The job this is coming from

        Returns
        -------
        model: QPainterPath
            The path model with the filter applied

        """
        return model

    def apply_to_polypath(self, polypath):
        """ Apply the filter to the model

        Parameters
        ----------
        polypath: List of QPolygon
            List of polygons to process

        Returns
        -------
        polypath: List of QPolygon
            List of polygons with the filter applied

        """
        return polypath
