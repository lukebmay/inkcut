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
from inkcut.core.utils import log
from . import extensions
from .device_transport import DeviceTransport


class DeviceProtocol(Model):

    #: The declaration that defined this protocol
    declaration = Typed(extensions.DeviceProtocol).tag(config=True)

    #: The active protocol
    transport = Instance(DeviceTransport)

    #: The protocol specific config
    config = Instance(Model, ()).tag(config=True)

    def connection_made(self):
        """ This is called when a connection is made to the device.

        Use this to send any initialization commands before the job starts.

        """
        raise NotImplementedError

    def set_pen(self, p):
        """ Set the pen or tool that should be used.

         Parameters
        ----------
        p: int
            The pen or tool number to use.

        """

    def set_force(self, f):
        """ Set the force the device should use.

        Parameters
        ----------
        f: int
            The force setting value to send to the device

        """

    def set_velocity(self, v):
        """ Set the force the device should use.

        Parameters
        ----------
        v: int
            The force setting value to send to the device

        """

    def move(self, x, y, z, absolute=True):
        """ Called when the device position is updated.

        """
        raise NotImplementedError

    def write(self, data):
        """ Call this to write data using the underlying transport.

        This should typically not be overridden.

        """
        if self.transport is not None:
            self.transport.write(data)

    def data_received(self, data):
        """ Called when the device replies back with data. This can occur
        at any time as communication is asynchronous. The protocol should
        handle as needed.

        Parameters
        ----------
        data


        """
        log.debug("data received: {}".format(data))

    def finish(self):
        """ Called when processing all of the paths of the job are complete.

        Use this to send any finalization commands.

        """
        pass

    def connection_lost(self):
        """ Called the connection to the device is dropped or
        failed to connect.  No more data can be written when this is called.

        """
        pass
