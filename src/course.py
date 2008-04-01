#/usr/bin/env python
#
#    Copyright (C) 2008  Gaudenz Steinlin <gaudenz@soziologie.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
course.py - Classes for orienteering courses. Everything here is
            static during an event. Dynamic data (e.g. runs) is
            handled by the classes in run.py
"""

from storm.locals import *
from ranking import Rankable

class SIStation(Storm):
    """SI Control Station. Each si station bleongs to a control, but each
       control can have more than one si station (eg. if a station fails
       during the event)."""

    START  = 1
    FINISH = 2
    CLEAR  = 3
    CHECK  = 4
    
    __storm_table__ = 'sistation'

    id = Int(primary=True)
    _control_id = Int(name='control')
    control = Reference(_control_id, 'Control.id')

    def __init__(self, id):
        self.id = id
    
class Control(Storm):
    """A control point. Control points are part of one or several courses.
       The possible orders of the control points in a course is defined
       with the ControlSequence relation."""
       
    __storm_table__ = 'control'

    id = Int(primary=True)
    code = Unicode()
    sistations = ReferenceSet(id, 'SIStation._control_id')

    def __init__(self, code, sistation = None):
        self.code = code
        if sistation:
            self.sistations.add(sistation)

class ControlSequence(Storm):
    """Connects controls and courses. The sequence_number defines the
       correct sequence of the controls. It's possible the have several
       controls with the same sequence_number on the same course. The
       interpretation of the sequence number is up to the validate method
       of the course. The sequence number may be None."""
       
    __storm_table__ = 'controlsequence'

    id = Int(primary=True)
    length = Int()
    climb = Int()
    _course_id = Int(name='course')
    course = Reference(_course_id, 'Course.id')
    _control_id = Int(name='control')
    control = Reference(_control_id, 'Control.id')
    sequence_number = Int()

    def __init__(self, control, sequence_number = None,
                 length = None, climb = None):
        self.control = control
        self.sequence_number = sequence_number
        self.length = length
        self.climb = climb
        
class Course(Storm, Rankable):
    """Base class for all kinds of courses. Special kinds of courses should
       be derived from this class. Derived class must at least override the
       append or validate methods. This class implements an unordered set
       of controls as a course without any validation.

       The distance and altitude attributes are in meters and may be None."""
    
    __storm_table__ = 'course'

    id = Int(primary=True)
    code = Unicode()
    length = Int()
    climb = Int()
    members = ReferenceSet(id, 'Run._course_id')
    controls = ReferenceSet(id, ControlSequence._course_id,
                            ControlSequence._control_id, Control.id)
    sequence = ReferenceSet(id, 'ControlSequence._course_id')

    def __init__(self, code, length = None, climb = None, expected_speed = None):
        self.code = code
        self.length = length
        self.climb = climb
        self.expected_speed = expected_speed
        self._validators = {}
        
    def __max_index(self):
        max = 0
        for control in self.sequence:
            # increase max if sequence_number is bigger
            max = max > control.sequence_number and max or control.sequence_number
        return max

    def __has_index(self, index):
        for control in self.sequence:
            if control.sequence_number == index:
                return True
        return False

    def append(self, control, length = None, climb = None):
        """Append a single control to the course."""
        self.sequence.add(ControlSequence(control, self.__max_index() + 1,
                                          length, climb))

    def insert(self, control, index, length = None, climb = None):
        """Insert an additional control into the course at an arbitrary
           postition."""
        raise Exception('Not yet implemented')

    def extend(self, control_list):
        """Extend the course with the controls from control_list."""
        for c in control_list:
            self.append(c)

    def expected_time(self):
        """Returns the expected time for this course."""
        try:
            return timedelta(minutes=(self.length + self.climb/100)*self.expected_speed)
        except TypeError:
            return None

    def validator(self, validator_class):
        """Returns a validator object for this run of the specified class. Validator
        objects are cached."""
        if validator_class not in self._validators:
            # create validator instance
            self._validators[validator_class] = validator_class(self)
        return self._validators[validator_class]
    
    
