# -*- coding: utf-8 -*-
"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jan 16, 2015

@author: jrm
"""

from atom.api import (
    ContainerList, Bool, Str, Int, Float, Enum, observe
)
from inkcut.core.api import Model
from inkcut.core.utils import parse_unit, to_unit


def _origin_from_legacy(state):
    # swap_xy and feed_direction are not stored. Illegal pairs become left.
    state = dict(state)
    has_origin = 'origin_side' in state
    has_feed = 'feed_direction' in state
    origin = state.get('origin_side')
    feed = state.pop('feed_direction', None)
    swap_xy = state.pop('swap_xy', False)
    if has_origin and has_feed:
        if (origin, feed) not in (('left', 'down'), ('right', 'left')):
            state['origin_side'] = 'left'
    elif has_feed:
        state['origin_side'] = 'right' if feed == 'left' else 'left'
    elif not has_origin and swap_xy:
        state['origin_side'] = 'right'
    return state


class DeviceConfig(Model):
    """ The default device configuration. Custom devices may want to subclass
    this.

    """
    #: Time between each path command
    #: Time to wait between each step so we don't get
    #: way ahead of the cutter and fill up it's buffer
    step_time = Float(strict=False).tag(config=True)
    custom_rate = Float(-1, strict=False).tag(config=True)

    #: Distance between each command in user units
    #: this is effectively the resolution the software supplies
    step_size = Float(parse_unit('1mm'), strict=False).tag(config=True)

    #: Interpolate paths breaking them into small sections that
    #: can be sent. This allows pausing mid plot as many devices do not have
    #: a cancel command.
    interpolate = Bool(False).tag(config=True)

    #: How often the position will be updated in ms. Low power devices should
    #: set this to a high number like 2000 or 3000
    sample_rate = Int(100).tag(config=True)

    #: Final output rotation
    rotation = Enum(0, 90, -90).tag(config=True)

    #: Origin left feeds down. Origin right feeds left.
    origin_side = Enum('left', 'right').tag(config=True)
    mirror_y = Bool().tag(config=True)
    mirror_x = Bool().tag(config=True)

    #: Final out scaling
    scale = ContainerList(Float(strict=False), default=[1, 1]).tag(config=True)

    #: Defines prescaling before conversion to a polygon
    quality_factor = Float(1, strict=False).tag(config=True)

    #: In cm/s
    speed = Float(4, strict=False).tag(config=True)
    speed_units = Enum('in/s', 'cm/s').tag(config=True)
    speed_enabled = Bool().tag(config=True)

    #: Force in g
    force = Float(40, strict=False).tag(config=True)
    force_units = Enum('g').tag(config=True)
    force_enabled = Bool().tag(config=True)

    #: Use absolute coordinates
    absolute = Bool().tag(config=True)

    #: Device output is spooled by an external service
    #: this will cause the job to run with no delays between commands
    spooled = Bool().tag(config=True)

    #: Use a virtual connection
    test_mode = Bool().tag(config=True)

    #: Init commands
    commands_before = Str().tag(config=True)
    commands_after = Str().tag(config=True)
    commands_connect = Str().tag(config=True)
    commands_disconnect = Str().tag(config=True)

    def __init__(self, *args, **kwargs):
        super(DeviceConfig, self).__init__(
            *args, **_origin_from_legacy(kwargs))

    def __setstate__(self, state):
        super(DeviceConfig, self).__setstate__(_origin_from_legacy(state))

    def __getstate__(self):
        state = super(DeviceConfig, self).__getstate__()
        state.pop('swap_xy', None)
        state.pop('feed_direction', None)
        return state

    def _default_step_time(self):
        """ Determine the step time based on the device speed setting


        """
        #: Convert speed to px/s then to mm/s
        units = self.speed_units.split("/")[0]
        speed = parse_unit('%s%s' % (self.speed, units))
        speed = to_unit(speed, 'mm')
        if speed == 0:
            return 0

        #: No determine the time and convert to ms
        return max(0, round(1000*self.step_size/speed))

    @observe('speed', 'speed_units', 'step_size')
    def _update_step_time(self, change):
        if change['type'] == 'update':
            self.step_time = self._default_step_time()
