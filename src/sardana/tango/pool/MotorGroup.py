#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

""" """

__all__ = ["MotorGroup", "MotorGroupClass"]

__docformat__ = 'restructuredtext'

import time

from PyTango import Util, DevFailed
from PyTango import DevVoid, DevLong, DevLong64, DevDouble, DevBoolean, DevString
from PyTango import DispLevel, DevState, AttrQuality
from PyTango import READ, READ_WRITE, SCALAR, SPECTRUM

from taurus.core.util.log import InfoIt, DebugIt

from PoolDevice import PoolGroupDevice, PoolGroupDeviceClass
from sardana.tango.core import to_tango_state

class MotorGroup(PoolGroupDevice):
    
    def __init__(self, dclass, name):
        PoolGroupDevice.__init__(self, dclass, name)
        MotorGroup.init_device(self)

    def init(self, name):
        PoolGroupDevice.init(self, name)

    def _is_allowed(self, req_type):
        return PoolGroupDevice._is_allowed(self, req_type)
    
    def get_motor_group(self):
        return self.element
    
    def set_motor_group(self, motor_group):
        self.element = motor_group
    
    motor_group = property(get_motor_group, set_motor_group)
    
    @DebugIt()
    def delete_device(self):
        self.pool.delete_element(self.motor_group.get_name())
        self.motor_group = None
    
    @DebugIt()
    def init_device(self):
        PoolGroupDevice.init_device(self)
    
        detect_evts = "state", "status", "position"
        non_detect_evts = "elementlist",
        self.set_change_events(detect_evts, non_detect_evts)

        self.Elements = map(int, self.Elements)
        if self.motor_group is None:
            motor_group = self.pool.create_motor_group(name=self.alias, 
                full_name=self.get_name(), id=self.Id,
                user_elements=self.Elements)
            motor_group.add_listener(self.on_motor_group_changed)
            self.motor_group = motor_group
        # force a state read to initialize the state attribute
        #state = self.motor_group.state
        #self.set_state(to_tango_state(state))
        self.set_state(DevState.ON)

    def on_motor_group_changed(self, event_source, event_type, event_value):
        t = time.time()
        name = event_type.name
        
        multi_attr = self.get_device_attr()
        attr = multi_attr.get_attr_by_name(name)
        quality = AttrQuality.ATTR_VALID
        
        recover = False
        if event_type.priority:
            attr.set_change_event(True, False)
            recover = True
        
        try:
            if name == "state":
                event_value = to_tango_state(event_value)
                self.set_state(event_value)
                self.push_change_event(name, event_value)
            elif name == "status":
                self.set_status(event_value)
                self.push_change_event(name, event_value)
            else:
                state = to_tango_state(self.motor_group.get_state())
                #state = self.get_state()
                if name == "position":
                    if state == DevState.MOVING:
                        quality = AttrQuality.ATTR_CHANGING
                    positions = self._to_motor_positions(event_value)
                attr.set_value_date_quality(positions, t, quality)
                self.push_change_event(name, positions, t, quality)
        finally:
            if recover:
                attr.set_change_event(True, True)
    
    def always_executed_hook(self):
        pass 
        #state = to_tango_state(self.motor_group.get_state(cache=False))
    
    def read_attr_hardware(self,data):
        pass
    
    def _to_motor_positions(self, pos):
        return [ pos[elem] for elem in self.motor_group.get_user_elements() ]
    
    def read_Position(self, attr):
        # if motors are moving their position is already being updated with a
        # high frequency so don't bother overloading and just get the cached
        # values
        cache = self.get_state() == DevState.MOVING
        positions = self.motor_group.get_position(cache=cache)
        positions = self._to_motor_positions(positions)
        attr.set_value(positions)
    
    def write_Position(self, attr):
        self.motor_group.position = attr.get_write_value()
        
    is_Position_allowed = _is_allowed
    

class MotorGroupClass(PoolGroupDeviceClass):

    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
    }
    device_property_list.update(PoolGroupDeviceClass.device_property_list)

    #    Command definitions
    cmd_list = {
    }
    cmd_list.update(PoolGroupDeviceClass.cmd_list)

    #    Attribute definitions
    attr_list = {
        'Position'     : [ [ DevDouble, SPECTRUM, READ_WRITE, 4096 ] ],
    }
    attr_list.update(PoolGroupDeviceClass.attr_list)

    def __init__(self, name):
        PoolGroupDeviceClass.__init__(self, name)
        self.set_type(name)


