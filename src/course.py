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

from datetime import timedelta

from ranking import Rankable
from base import MyStorm

class SIStation(Storm):
    """SI Control Station. Each si station bleongs to a control, but each
       control can have more than one si station (eg. if a station fails
       during the event)."""

    START       = 1
    FINISH      = 2
    CLEAR       = 3
    CHECK       = 4
    SPECIAL_MAX = 4
    
    __storm_table__ = 'sistation'

    id = Int(primary=True)
    _control_id = Int(name='control')
    control = Reference(_control_id, 'Control.id')

    def __init__(self, id):
        self.id = id

class Control(MyStorm):
    """A control point. Control points are part of one or several courses.
       The possible orders of the control points in a course is defined
       with the ControlSequence relation."""
       
    __storm_table__ = 'control'

    id = Int(primary=True)
    code = Unicode()
    override = Bool()
    sistations = ReferenceSet(id, 'SIStation._control_id')

    def __init__(self, code, sistation = None, store = None):
        """
        @param code:      Code for this control.
        @type code:       unicode
        @param sistation: SI-Station for this control. If this is an integer,
                          a corresponding SIStation object is created if necessary.
                          If sistation is None a SIStation with id int(code) ist added
                          if possible.
        @type sistation:  SIStation object or int
        @param store:     Storm store for the sistation. A store is needed if
                          sistation is given as int. The newly created object is
                          automatically added to this store.
        """
        
        self.code = code
        if store is not None:
            self._store = store

        if sistation is None:
            try:
                sistation = int(code)
            except ValueError:
                pass

        if sistation is not None:
            self.add_sistation(sistation)

    def add_sistation(self, sistation):
        """Add an SIStation to this Control.

        @param sistation: SI-Station for this control. If this is an integer,
                          a corresponding SIStation object is created if necessary.
        @type sistation:  SIStation object or int
        """
        
        if type(sistation) == int:
            station_nr = sistation
            sistation = self._store.get(SIStation, sistation)
            if sistation is None:
                sistation = SIStation(station_nr)
                
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
        
class Course(MyStorm, Rankable):
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
                            ControlSequence._control_id, 
                            Control.id, 
                            order_by=ControlSequence.sequence_number)
    sequence = ReferenceSet(id, 'ControlSequence._course_id',
                            order_by=ControlSequence.sequence_number)

    def __init__(self, code, length = None, climb = None):
        """
        @param code:          Descriptive code for this course. Usually 3 characters long. For
                              'normal' events this corresponds to the category name.
        @type code:           unicode
        @param length:        Length of the course in meters
        @type length:         int
        @param climb:         Altitude differences in meters
        @type climb:          int
        """
        
        self.code = code
        self.length = length
        self.climb = climb

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
        """Append a single control to the course.

        @param control: next control. The control is automatically created
                        if it does not yet exist.
        @type control:  Control object or unicode
        """
        if type(control) is unicode:
            controlcode = control
            control = self._store.find(Control, Control.code == controlcode).one()
            if control is None:
                control = Control(controlcode, store = self._store)
            
                
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

    def lkm(self):
        """
        @return: 'Leistungskilometer': length/1000.0+climb/100.0
        """
        return self.length/1000.0 + self.climb/100.0
    
    def expected_time(self, speed):
        """Returns the expected time for this course.
        @param speed: expected speed in minutes per kilometer
        """
        try:
            return timedelta(minutes=self.lkm()*speed)
        except TypeError:
            return None

    def controlcount(self):
        return self.controls.count()

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.code

class CombinedCourse(Rankable):
    """
    This class combines several courses to generate a joint ranking of all runns of
    all the combined courses. This is primarily usefull for rankings of relay legs with
    different variants. This class is not derived from Course and this is not a Storm object
    and not stored in the database.
    """

    def __init__(self, course_list, code, store=None):
        """
        @param course_list: List of courses to combine
        @type course_list:  list of either instances of Course or unicode course codes
        @param code:        Code of this course. This is only for display purposes.
        @type code:         Unicode
        @param store:       Storm store which contains the courses referenced by course
                            codes in the course list. May be None if the course list only
                            contains Course objects.
        """
        self._code = code
        self._course_list = []
        for c in course_list:
            if type(c) == Course:
                self._course_list.append(c)
            else:
                if store is None:
                    raise CombinedCourseException("Can't add course '%s' without a store." % c)
                
                course = store.find(Course, Course.code == c).one()
                if course is None:
                    raise CombinedCourseException("Can't find course with code '%s'." % c)
                self._course_list.append(course)

        self.length = self._course_list[0].length
        self.climb = self._course_list[0].climb
        self._controlcount = self._course_list[0].controls.count()

    def _get_members(self):
        """Get all runs of all the courses in self._course_list."""

        runs = []
        for c in self._course_list:
            runs.extend([r for r in c.members])
        return runs
    members = property(_get_members)

    def controlcount(self):
        return self._controlcount

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self._code

class CombinedCourseException(Exception):
    pass
