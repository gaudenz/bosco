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

from copy import copy
from datetime import datetime
from storm.locals import *
from storm.exceptions import NoStoreError
from storm.expr import Column, Func, LeftJoin
import re

from .base import MyStorm
from .course import SIStation, Course, Control
from .runner import SICard
from .ranking import RankableItem, ValidationError, UnscoreableException

class Punch(Storm):
    __storm_table__ = 'punch'

    id = Int(primary=True)
    _run_id = Int(name='run')
    run = Reference(_run_id, 'Run.id')
    _sistation_id = Int(name='sistation')
    sistation = Reference(_sistation_id, 'SIStation.id')
    card_punchtime = DateTime(name = 'card_punchtime')
    manual_punchtime = DateTime()
    ignore = Bool()
    sequence = Int()

    def __init__(self, sistation, card_punchtime=None, manual_punchtime = None,
                 sequence = None):
        """Creates a new punch object. This object needs to be added to a
           run. It can not "live" on its own."""
        self.sistation = sistation
        self.card_punchtime = card_punchtime
        self.manual_punchtime = manual_punchtime
        self.sequence = sequence

    def _get_punchtime(self):
        if self.manual_punchtime is not None:
            return self.manual_punchtime
        else:
            return self.card_punchtime
    punchtime = property(_get_punchtime)
        
class ShiftedPunch:
    """
    Wraps a punch object which has it's punchtime shifted because it's
    part of a course wrapped by a ReorderedCourseWrapper.
    """

    def __init__(self, punch, timeshift):
        self._punch = punch
        self._shift = timeshift

    def __getattr__(self, attr):
        if attr == 'punchtime':
            return self._punch.punchtime + self._shift
        else:
            return getattr(self._punch, attr)

class Run(MyStorm, RankableItem):
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
    complete = Bool()
    override = Int()
    card_start_time = DateTime()
    manual_start_time = DateTime()
    start_time = property(lambda obj: obj.manual_start_time or obj.card_start_time)
    card_finish_time = DateTime()
    manual_finish_time = DateTime()
    finish_time = property(lambda obj: obj.manual_finish_time or obj.card_finish_time)
    check_time = DateTime()
    clear_time = DateTime()
    readout_time = DateTime()
    punches = ReferenceSet(id, 'Punch._run_id')

    
    def __init__(self, card, course=None, punches = [], card_start_time = None,
                 card_finish_time = None, check_time = None, clear_time = None,
                 readout_time = None,
                 store = None):
        """Creates a new Run object.

        @param card:    SICard
        @type  card:    Object of class L{SICard} or card number as integer.
                        If the card number is given the store parameter is
                        mandatory.
        @param course:  Course
        @type  course:  Object of class L{Course} or course code as string.
        @param punches: Punches to add to the run.
        @type  punches: List of (stationcode, punchtime) tuples.
        @param card_start_time: Time the SI-Card last punched a start control
        @type  card_start_time: datetime or None if unknown
        @param card_finish_time: Time the SI-Card last punched a finish control
        @type  card_finish_time: datetime or None if unknown
        @param check_time: Time the SI-Card was checked
        @type  check_time: datetime or None if unknown
        @param clear_time: Time the SI-Card was cleared
        @type  clear_time: datetime or None if unknown
        @param readout_time: Time the run was read from the SI-Card
        @type  readout_time: datetime or None if unknown
        @param store:   Storm store for the objects referenced by this run.
                        A store is needed if card or course are given as int/string
                        or if punches is non empty.
        """
        
        if isinstance(card, int):
            cardnr = card
            card = store.get(SICard, card)
            if not card:
                card = SICard(cardnr)

        self.sicard = card

        if store is not None:
            self._store = store

        if isinstance(course, str):
            self.set_coursecode(course)
        else:
            self.course = course

        self.readout_time = readout_time
        self.card_start_time = card_start_time
        self.card_finish_time = card_finish_time
        self.check_time = check_time
        self.clear_time = clear_time
        
        self.add_punchlist(punches)

    def __str__(self):
        runner = self.sicard.runner
        if runner is not None:
            return '%s %s' % (runner.given_name, runner.surname)
        else:
            return 'SI-Card: %s' % self.sicard.id

    @property
    def start_time(self):
        return self.manual_start_time or self.card_start_time

    @property
    def finish_time(self):
        return self.manual_finish_time or self.card_finish_time

    def add_punch(self, punch, sequence_nr=None):
        """Adds a (stationnumber, punchtime) tuple to the run."""

        (number, punchtime) = punch

        # Only add punch if it does not yet exist on this run
        if self._store.find(Punch, And(Punch.run == self.id,
                                       Punch.sistation == number,
                                       Punch.card_punchtime == punchtime)).count() == 0:
            
            station = self._store.get(SIStation, number)
            if station is None:
                station = SIStation(number)
        
            self.punches.add(Punch(station, punchtime, sequence=sequence_nr))

    def add_punchlist(self, punchlist):
        """Adds a list of (stationnumber, punchtime) tupeles to the run."""
        errors = ''
        for i, p in enumerate(punchlist):
            try:
                self.add_punch(p, i+1)
            except RunException as msg:
                errors = '%s%s\n' % (errors, msg)
                
        if not errors == '':
            raise RunException(errors)
        
    def set_coursecode(self, code):
        """Sets the course for this run.
        @param coursecode: The code of the course or None to clear the code.
        @type coursecode:  unicode or None
        """
        if code is None:
            self.course = None
            return
        
        course = self._store.find(Course,
                            Course.code == code).one()
        if course is None:
            raise RunException("course '%s' not found" % code)

        self.course = course

    def punchlist(self, ignored = False):
        """
        Return all valid 'normal' punches ordered by punchtime
        @param ignored: Return punches normally ignored
        @rtype: (Punch, Control) tuples
        """

        # Do a direct search in the store for Punch, Control tuples. This is much faster
        # than first fetching punches from self.punches and then getting their controls via
        # punch.sistation.control
        punch_cond = And(Punch.ignore != True,
                         Func('COALESCE', Punch.manual_punchtime, Punch.card_punchtime)
                         > (self.start_time or datetime.min),
                         Func('COALESCE', Punch.manual_punchtime, Punch.card_punchtime)
                         < (self.finish_time or datetime.max),
                         Not(SIStation.control == None),
                         )
        
        if ignored is True:
            punch_cond = Not(punch_cond)

        return list(self._store.using(Join(Punch, SIStation, Punch.sistation == SIStation.id),
                                      LeftJoin(Control, SIStation.control == Control.id)
                                      ).find((Punch, Control),
                                             punch_cond,
                                             Punch.run == self.id,
                                             ).order_by(Func('COALESCE',
                                                             Punch.manual_punchtime,
                                                             Punch.card_punchtime))
                    )

    def check_sequence(self):
        """Check if punchtimes match punch sequence numbers."""
        punchsequence = list(self.punches.find(Not(Punch.card_punchtime == None),
                                               Not(Punch.ignore == True),
                                               Punch.sistation == SIStation.id,
                                               SIStation.control == Control.id,
                                               Not(Control.override == True)).order_by('COALESCE(manual_punchtime, card_punchtime)').values(Column('sequence')))

        return punchsequence == sorted(copy(punchsequence))

    def validate(self, validator_class=None, args=None):
        """Validate this run. Validation of runs is normally refered to the course, but
        passing a special validator class is supported.
        @param validator_class: Class to use as a validation strategy. This must be a subclass
                                of bosco.ranking.Validator
        @param args:            Arguments to pass to the validation strategy.
        @type args:             dict of keyword arguments
        @return:                validation result from validation_class.validate(obj)
        @see:                   bosco.ranking.Validator for more information about validation strategies
        """
        if validator_class is not None:
            return validator_class(**args).validate(self)
        elif self.course is None:
            raise ValidationError("Can't validate a run without a course.")
        else:
            return self.course.validate(self)

    def score(self, scoreing_class=None, args=None):
        """Score this run. Scoreing of runs is normally refered to the course, but
        passing a special scoreing class is supported.
        @param scoreing_class: Class to use a scoreing stratey. This must be a subclass
                               of bosco.ranking.AbstracScoreing.
        @type args:            dict of keyword arguments
        @return:               scoreing result from scoreing_class.score(obj)
        @see:                  bosco.ranking.AbstractScoreing for more information about scoreing strategies
        """
        if scoreing_class is not None:
            return scoreing_class(**args).score(self)
        elif self.course is None:
            raise UnscoreableException("Can't score a run without a course")
        else:
            return self.course.score(self)

class RunException(Exception):
    pass
