#/usr/bin/env python
#    run.py - Classes for runs. This is the data generated during
#             an event. Opposed to classes in course.py which model
#             static data.
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

from storm.locals import *
import re

from course import SIStation

def punchlist(punches, stationstore):
    """Creates a list of punch objects from a list of (timestamp, controlnumber)
    tuples. Controlstore is the Store where Control objects are stored."""
    
    plist = []
    for (number, timestamp) in punches:
        station = stationstore.get(SIStation, number)
        if not station:
            raise SIStationNotFoundException('si-station number \'%s\' not found' % number)

        # Create list of control object, timestamp tuples, don't create punch objects
        # because Store.find flushes the store and we don't have a valid run yet
        plist.append((station, timestamp))

    # return list of punch objects
    return [ Punch(c, t) for (c,t) in plist ]
    

class Punch(Storm):
    __storm_table__ = 'punch'

    id = Int(primary=True)
    run_id = Int()
    run = Reference(run_id, 'Run.id')
    sistation_id = Int()
    sistation = Reference(sistation_id, 'SIStation.id')
    punchtime = DateTime()

    def __init__(self, sistation, punchtime):
        """Creates a new punch object. This object needs to be added to a
           run. It can not "live" on its own."""
        self.sistation = sistation
        self.punchtime = punchtime


class Run(Storm):
    """A run is directly connected to a single readout of an SI-Card.
       Competitors can have multiple runs during an event, but one
       run can not be associated to several SI-Card readouts. You have
       to create multiple runs in this case and an appropriate validator
       class which checks for the correct sequence of runs (e.g. for a
       relay)."""
    
    __storm_table__ = 'run'

    id = Int(primary=True)
    sicard_id = Int()
    sicard = Reference(sicard_id, 'SICard.id')
    course_id = Int()
    course = Reference(course_id, 'Course.id')
    complete = Bool()
    punches = ReferenceSet(id, 'Punch.run_id')

    
    def __init__(self, course, card):
        """Course object associated with this run. Punches is a list
           of punch objects."""

        self.sicard = card
        self.course = course

    def add_punch(self, punch):
        self.punches.add(punch)

    def add_punchlist(self, punchlist):
        for p in punchlist:
            self.add_punch(p)

    def complete_run(self):
        self.complete = True
            
        
class SIStationNotFoundException(Exception):
    pass
