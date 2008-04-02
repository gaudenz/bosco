#!/usr/bin/env python
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
    run.py - Classes for runs. This is the data generated during
             an event. Opposed to classes in course.py which model
             static data.
"""

from storm.locals import *
from storm.exceptions import NoStoreError
import re

from course import SIStation, Course
from runner import SICard
from ranking import RankableItem

class Punch(Storm):
    __storm_table__ = 'punch'

    id = Int(primary=True)
    _run_id = Int(name='run')
    run = Reference(_run_id, 'Run.id')
    _sistation_id = Int(name='sistation')
    sistation = Reference(_sistation_id, 'SIStation.id')
    punchtime = DateTime()

    def __init__(self, sistation, punchtime):
        """Creates a new punch object. This object needs to be added to a
           run. It can not "live" on its own."""
        self.sistation = sistation
        self.punchtime = punchtime


class Run(Storm, RankableItem):
    """A run is directly connected to a single readout of an SI-Card.
       Competitors can have multiple runs during an event, but one
       run can not be associated to several SI-Card readouts. You have
       to create multiple runs in this case and an appropriate validator
       class which checks for the correct sequence of runs (e.g. for a
       relay)."""
    
    __storm_table__ = 'run'

    id = Int(primary=True)
    _sicard_id = Int(name='sicard')
    sicard = Reference(_sicard_id, 'SICard.id')
    _course_id = Int(name='course')
    course = Reference(_course_id, 'Course.id')
    complete = Bool(name='complete')
    punches = ReferenceSet(id, 'Punch._run_id')

    
    def __init__(self, card, course=None, punches = [], store = None):
        """Creates a new Run object.

        @param card:    SICard
        @type  card:    Object of class L{SICard} or card number as integer.
                        If the card number is given the store parameter is
                        mandatory.
        @param course:  Course
        @type  course:  Object of class L{Course} or course code as string.
        @param punches: Punches to add to the run.
        @type  punches: List of (stationcode, punchtime) tuples.
        @param store:   Storm store for the objects referenced by this run.
                        A store is needed if card or course are given as int/string
                        or if punches is non empty.
        """
        if type(card) == int:
            cardnr = card
            card = store.get(SICard, card)
            if not card:
                raise RunException("Could not find SI-Card Nr. '%s'" % cardnr)

        self.sicard = card

        if type(course) == unicode:
            self.set_coursecode(course)
        else:
            self.course = course
            
        self.add_punchlist(punches)

    def __storm_pre_flush__(self):
        """Do some consistency checks before flushing the object to the database.
        @todo: Better implement this on the db layer (triggers)? Or even better
        subclass boolean to check this when accessing the property.
        """
        if self.complete and self.course is None:
            raise RunException("Can't complete a run without a Course.")
        
    def _get_store(self):
        store = Store.of(self)
        if store is None:
            raise NoStoreError("Can't add punches without a store")
        return store

    def add_punch(self, punch):
        """Adds a (stationnumber, punchtime) tuple to the run."""

        (number, punchtime) = punch
        
        store = self._get_store()
        
        station = store.get(SIStation, number)
        if station is None:
            raise RunException('si-station number \'%s\' not found' % number)

        self.punches.add(Punch(station, punchtime))

    def add_punchlist(self, punchlist):
        """Adds a list of (stationnumber, punchtime) tupeles to the run."""
        for p in punchlist:
            self.add_punch(p)

    def set_coursecode(self, code):
        """Sets the course for this run.
        @param coursecode: The code of the course.
        @type coursecode:  unicode
        """
        store = self._get_store()
        course = store.find(Course,
                            Course.code == code).one()
        if course is None:
            raise RunException("course '%s' not found" % code)

        self.course = course

    def punchtime(self, control, first = False, sistation=False):
        """Gets the time a specific control was last (first) punched. Returns None if
        the control was never punched. If sistation is True the control argument is 
        intrpreted as an SI station number or object."""
            
        if sistation:
            result = self.punches.find(Punch.sistation == control).order_by('punchtime')
        else:
            # The search term here is far from optimal from an encapsulation viewpoint, but 
            # I couldn't find anything better...
            sistation_ids = [i.id for i in control.sistations]
            result = self.punches.find(Punch._sistation_id.is_in(sistation_ids)).order_by('punchtime')
            
        if result.count() > 0:
            if first:
                return result.first().punchtime
            else:
                return result.last().punchtime
        else:
            return None
        
    def start(self):
        """Returns the time the start control was punched or None."""
        return self.punchtime(SIStation.START, sistation=True)
    
    def finish(self):
        """Returns the time the finish control was punched or None."""
        return self.punchtime(SIStation.FINISH, first=True, sistation=True)
    
        
        
class RunException(Exception):
    pass
