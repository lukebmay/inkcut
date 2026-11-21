# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 16, 2015

@author: jrm
"""

from io import BytesIO
from atom.api import (
    Typed, Instance, ForwardInstance, Bool, Bytes
)
from inkcut.core.api import Model
from inkcut.core.utils import log
from . import extensions


def _protocol_type():
    from .device_protocol import DeviceProtocol
    return DeviceProtocol


class DeviceTransport(Model):

    #: The declaration that defined this transport
    declaration = Typed(extensions.DeviceTransport).tag(config=True)

    #: The transport specific config
    config = Instance(Model, ()).tag(config=True)

    #: The active protocol
    protocol = ForwardInstance(lambda: _protocol_type()).tag(config=True)

    #: Connection state. Subclasses must implement and properly update this
    connected = Bool()

    #: Distinguish between transports that always spool (e.g. Printer, File I/O)
    #: or are dependent on the 'spooling' configuration option (e.g. Serial)
    always_spools = Bool()

    #: Most recent input/output. These can be observed to update the UI
    last_read = Bytes()
    last_write = Bytes()

    def __init__(self, *args, **kwargs):
        super(DeviceTransport, self).__init__(*args, **kwargs)
        if self.protocol:
            self.protocol.transport = self

    def _observe_protocol(self, change):
        """ Whenever the protocol changes update the transport reference

        """
        if change['type'] in ('update', 'create') and change['value']:
            self.protocol.transport = self

    def connect(self):
        """ Connect using whatever implementation necessary

        """
        raise NotImplementedError

    def write(self, data):
        """ Write using whatever implementation necessary

        """
        raise NotImplementedError

    def read(self, size=None):
        """ Read using whatever implementation necessary and
        invoke `protocol.data_received` with the output.

        """
        raise NotImplementedError

    def disconnect(self):
        """ Disconnect using whatever implementation necessary

        """
        raise NotImplementedError


class TestTransport(DeviceTransport):
    """ A transport that captures protocol output """

    #: The output buffer
    buffer = Instance(BytesIO, ())

    def connect(self):
        self.connected = True
        #: Save a reference
        self.protocol.transport = self
        self.protocol.connection_made()

    def write(self, data):
        log.debug("-> Test | {}".format(data))

        #: Python 3 is annoying
        if hasattr(data, 'encode'):
            data = data.encode()

        self.buffer.write(data)

    def read(self, size=None):
        return ""

    def disconnect(self):
        self.connected = False
        self.protocol.connection_lost()
