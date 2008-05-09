#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import unittest

from storm.locals import *
from datetime import datetime, timedelta
from course import Course, Control, SIStation
from runner import SICard, Runner, Category, Team

from run import Run, Punch
from ranking import (TimeScoreing,
                     MassstartStarttime,
                     SelfstartStarttime,
                     RelayStarttime,
                     RelayMassstartStarttime,
                     UnscoreableException,
                     Validator,
                     SequenceCourseValidator,
                     Ranking)
from event import Event

class RunTest(unittest.TestCase):

    # Create store as class variable so that every test uses the same
    # database connection
    _store = Store(create_database('postgres:24h_test'))
    
    def setUp(self):

        # Create start and finish control
        self._si_s = SIStation(SIStation.START)
        self._si_f = SIStation(SIStation.FINISH)
        S = self._store.add(Control(u'S', self._si_s))
        F = self._store.add(Control(u'F', self._si_f))

        # create control with 2 sistations
        c200 = Control(u'200', SIStation(200))
        c200.sistations.add(SIStation(201))
        self._c131 = self._store.add(Control(u'131', SIStation(131)))

        # create sistation without any control
        self._store.add(SIStation(133))
        
        # Create a Course
        self._course = self._store.add(Course(u'A', length = 1679, climb = 587))
        self._course.extend([u'131', u'132', c200, u'132'])

        # Create categorys
        self._cat_ind = self._store.add(Category(u'HAM'))
        cat_team = Category(u'D135')
        
        # Create Runners
        self._runners = []
        
        self._runners.append(Runner(u'Muster', u'Hans', 655465, u'HAM', u'101',
                                    store = self._store))
        self._runners.append(Runner(u'Gerster', u'Trudi', 765477, u'HAM', u'102',
                                    store = self._store))
        self._runners.append(Runner(u'Mueller', u'Hans', 768765, u'HAM', u'103',
                                    store = self._store))
        self._runners.append(Runner(u'Missing', u'The', 113456, u'HAM',
                                    store = self._store))
        self._runners.append(Runner(u'Gugus', u'Dada', 56789, u'HAM',
                                    store = self._store))
        self._runners.append(Runner(u'Al', u'Missing', 12345, u'HAM',
                                    store = self._store))
        

        # Create a team
        team = Team(u'1', u'The best team ever', category= cat_team)
        # Add team to store and flush to avoid cycles
        team.members.add(self._runners[0])
        team.members.add(self._runners[1])
        team.members.add(self._runners[2])
        
        # Create a runs
        self._runs = []

        # double start and finish punches, punch on sistation 201 for control 200
        self._runs.append(Run(655465,
                              u'A',
                              [(SIStation.START, datetime(2008,3,19,8,20,32)),
                               (SIStation.START, datetime(2008,3,19,8,20,35)),
                               (131,datetime(2008,3,19,8,22,39)),
                               (132,datetime(2008,3,19,8,23,35)),
                               (201,datetime(2008,3,19,8,24,35)),
                               (132,datetime(2008,3,19,8,25,0)),
                               (SIStation.FINISH,datetime(2008,3,19,8,25,35)),
                               (SIStation.FINISH,datetime(2008,3,19,8,25,37)),
                               ],
                              store = self._store
                              ))
        self._runs[0].complete = True

        # normal run
        self._runs.append(Run(765477,
                              u'A',
                              [ (SIStation.START, datetime(2008,3,19,8,25,50)),
                                (131,datetime(2008,3,19,8,27,39)),
                                (132,datetime(2008,3,19,8,28,35)),
                                (200,datetime(2008,3,19,8,29,35)),
                                (132,datetime(2008,3,19,8,30,0)),
                                (SIStation.FINISH,datetime(2008,3,19,8,31,23)),
                                ],
                              store = self._store
                              ))
        self._runs[1].complete = True

        # normal run, punching additional sistation not connected to any control
        self._runs.append(Run(768765,
                              u'A',
                              [ (SIStation.START, datetime(2008,3,19,8,31,25)),
                                (131,datetime(2008,3,19,8,33,39)),
                                (132,datetime(2008,3,19,8,34,35)),
                                (133,datetime(2008,3,19,8,34,50)),
                                (200,datetime(2008,3,19,8,35,35)),
                                (132,datetime(2008,3,19,8,36,0)),
                                (SIStation.FINISH,datetime(2008,3,19,8,36,25)),
                                ],
                              store = self._store
                              ))
        self._runs[2].complete = True

        # punch on control 131 missing
        self._runs.append(Run(113456,
                              u'A',
                              [ (SIStation.START, datetime(2008,3,19,8,31,25)),
                                (132,datetime(2008,3,19,8,33,39)),
                                (200,datetime(2008,3,19,8,35,35)),
                                (132,datetime(2008,3,19,8,36,0)),
                                (SIStation.FINISH,datetime(2008,3,19,8,36,25)),
                                ],
                              store = self._store
                              ))
        self._runs[3].complete = True

        # This run ends after run 0 but before the first punch of run 1
        self._runs.append(Run(56789,
                              u'A',
                              [(SIStation.START, datetime(2008,3,19,8,20,32)),
                               (131,datetime(2008,3,19,8,22,39)),
                               (132,datetime(2008,3,19,8,23,35)),
                               (201,datetime(2008,3,19,8,24,35)),
                               (132,datetime(2008,3,19,8,25,0)),
                               (SIStation.FINISH,datetime(2008,3,19,8,25,40)),
                               ],
                              store = self._store
                              ))
        self._runs[4].complete = True

        # empty run
        self._runs.append(Run(12345, u'A', [], store = self._store))
        self._runs[5].complete = True


    def tearDown(self):
        # Clean up Database
        self._store.rollback()
        
    def test_start_last(self):
        """Test that Run.start() returns the last punch on a start control."""
        self.assertEquals(self._runs[0].start(), datetime(2008,3,19,8,20,35)) 

    def test_finish_first(self):
        """Test that Run.finish() returns the first punch on a finish control."""
        self.assertEquals(self._runs[0].finish(), datetime(2008,3,19,8,25,35))

    def test_runtime_start_finish(self):
        """Test the run time for a run with start and finish controls."""
        strategy = TimeScoreing(SelfstartStarttime())
        score = strategy.score(self._runs[0])['score']
        self.assertEquals(score, timedelta(minutes=5))
        
    def test_runtime_massstart(self):
        """Test the run time for a run with mass start."""
        strategy = TimeScoreing(MassstartStarttime(datetime(2008,3,19,8,15,15)))
        score = strategy.score(self._runs[0])['score']
        self.assertEquals(score, timedelta(minutes=10, seconds=20))

    def test_runtime_relay(self):
        """Test the run time for a relay leg wich starts with the finish time of the
           previous run."""
        strategy = TimeScoreing(RelayStarttime(datetime(2008,3,19,8,15,15), ordered = True))
        score = strategy.score(self._runs[1])['score']
        self.assertEquals(score, timedelta(minutes=5, seconds=48))
        score = strategy.score(self._runs[2])['score']
        self.assertEquals(score, timedelta(minutes=5, seconds=2))

    def test_runtime_relay_first(self):
        """Test RelayTimeScoreing for the first runner (mass start)"""
        strategy = TimeScoreing(RelayStarttime(datetime(2008,3,19,8,20,0)))
        score = strategy.score(self._runs[0])['score']
        self.assertEquals(score, timedelta(minutes=5, seconds=35))

    def test_runtime_relay_massstart(self):
        """Test the run time for a relay leg which was started with a mass start if
        the finish time of the previous runner is after the mass start time."""
        strategy = TimeScoreing(RelayMassstartStarttime(datetime(2008,3,19,8,30,23)))
        score = strategy.score(self._runs[1])['score']
        self.assertEquals(score, timedelta(minutes=5, seconds=48))
        score = strategy.score(self._runs[2])['score']
        self.assertEquals(score, timedelta(minutes=6, seconds=2))

    @staticmethod
    def _convert_punchlist(punchlist):
        return [ (p[0], type(p[1]) == Punch and p[1].sistation.id or p[1].code) for
                      p in punchlist ]

    def test_validation_valid(self):
        """Test validation of a valid run."""
        validator = SequenceCourseValidator(self._course)
        valid = validator.validate(self._runs[1])
        self.assertEquals(valid['status'], Validator.OK)
        self.assertEquals(self._convert_punchlist(valid['punchlist']),
                          [('', SIStation.START),
                           ('ok', 131),
                           ('ok', 132),
                           ('ok', 200),
                           ('ok', 132),
                           ('', SIStation.FINISH)])
        
    def test_validation_additional(self):
        """Test validation of a valid run with additional punches."""
        validator = SequenceCourseValidator(self._course)
        valid = validator.validate(self._runs[2])
        self.assertEquals(valid['status'], Validator.OK)
        self.assertEquals(self._convert_punchlist(valid['punchlist']),
                          [('', SIStation.START),
                           ('ok', 131),
                           ('ok', 132),
                           ('additional', 133),
                           ('ok', 200),
                           ('ok', 132),
                           ('', SIStation.FINISH)])
        
    def test_validation_missing(self):
        """Test validation of a run with missing controls."""
        validator = SequenceCourseValidator(self._course)
        valid = validator.validate(self._runs[3])
        self.assertEquals(valid['status'], Validator.MISSING_CONTROLS)
        self.assertEquals(self._convert_punchlist(valid['punchlist']),
                          [('missing', u'131'),
                           ('', SIStation.START),
                           ('ok', 132),
                           ('ok', 200),
                           ('ok', 132),
                           ('', SIStation.FINISH)])

    def test_validation_all_missing(self):
        """Test that all controls of a run are missing if the validated run is empty."""
        validator = SequenceCourseValidator(self._course)
        valid  = validator.validate(self._runs[5])
        self.assertEquals(valid['status'], Validator.DID_NOT_FINISH)
        punchlist = [ (p[0], type(p[1]) == Punch and p[1].sistation.id or p[1].code) for
                      p in valid['punchlist'] ]
        self.assertEquals(punchlist,[('missing', u'131'),
                                     ('missing', u'132'),
                                     ('missing', u'200'),
                                     ('missing', u'132')])
        
    def test_ranking_course(self):
        """Test the correct ranking of runs in a course."""

        ranking = list(Event({}).ranking(self._course))
        self.assertEquals(ranking[0]['rank'], 1)
        self.assertEquals(ranking[0]['validation']['status'], Validator.OK)
        self.assertTrue(ranking[0]['item'] == self._runs[0] or ranking[0]['item'] == self._runs[2])
        
        self.assertEquals(ranking[1]['rank'], 1)
        self.assertEquals(ranking[1]['validation']['status'], Validator.OK)
        self.assertTrue(ranking[1]['item'] == self._runs[0] or ranking[1]['item'] == self._runs[2])

        self.assertEquals(ranking[2]['rank'], 3)
        self.assertEquals(ranking[2]['validation']['status'], Validator.OK)
        self.assertEquals(ranking[2]['item'], self._runs[4])

        self.assertEquals(ranking[3]['rank'], 4)
        self.assertEquals(ranking[3]['validation']['status'], Validator.OK)
        self.assertEquals(ranking[3]['item'], self._runs[1])

        self.assertEquals(ranking[4]['rank'], None)
        self.assertEquals(ranking[4]['validation']['status'], Validator.MISSING_CONTROLS)
        self.assertEquals(ranking[4]['item'], self._runs[3])

    def test_ranking_category(self):
        """Test the correct ranking of runs in a category."""

        ranking = list(Event({}).ranking(self._cat_ind))
        self.assertEquals(ranking[0]['rank'], 1)
        self.assertEquals(ranking[0]['validation']['status'], Validator.OK)
        self.assertTrue(ranking[0]['item'] == self._runners[0] or ranking[0]['item'] == self._runners[2])

        self.assertEquals(ranking[1]['rank'], 1)
        self.assertEquals(ranking[1]['validation']['status'], Validator.OK)
        self.assertTrue(ranking[1]['item'] == self._runners[0] or ranking[1]['item'] == self._runners[2])

        self.assertEquals(ranking[2]['rank'], 3)
        self.assertEquals(ranking[2]['validation']['status'], Validator.OK)
        self.assertEquals(ranking[2]['item'], self._runners[4])

        self.assertEquals(ranking[3]['rank'], 4)
        self.assertEquals(ranking[3]['validation']['status'], Validator.OK)
        self.assertEquals(ranking[3]['item'], self._runners[1])

        self.assertEquals(ranking[4]['rank'], None)
        self.assertEquals(ranking[4]['validation']['status'], Validator.MISSING_CONTROLS)
        self.assertEquals(ranking[4]['item'], self._runners[3])
        
    def test_overrride_control(self):
        """Test override for a control."""
        validator = SequenceCourseValidator(self._course)

        # Add override for control 131
        self._c131.override = True
        self.assertEquals(validator.validate(self._runs[3])['status'],
                          Validator.OK)
        
    def test_overrride_run(self):
        """Test overrride for a run."""
        validator = SequenceCourseValidator(self._course)
        self._runs[3].override = Validator.OK
        valid = validator.validate(self._runs[3])
        self.assertEquals(valid['status'], Validator.OK)
        self.assertEquals(valid['override'], True)

        self._runs[1].override = Validator.DISQUALIFIED
        valid = validator.validate(self._runs[1])
        self.assertEquals(valid['status'],Validator.DISQUALIFIED)
        self.assertEquals(valid['override'], True)

    def test_punchtime(self):
        """check for correct punchtime handling."""
        p = Punch(SIStation(10), card_punchtime = datetime(2008,5,3,12,02))
        self.assertEquals(p.punchtime, datetime(2008,5,3,12,02))
        p.manual_punchtime = datetime(2008,5,3,12,03)
        self.assertEquals(p.punchtime, datetime(2008,5,3,12,03))
        p.manual_punchtime = datetime(2008,5,3,12,01)
        self.assertEquals(p.punchtime, datetime(2008,5,3,12,01))
        
    def test_check_sequence(self):
        """Test punch sequence checking"""
        s10 = SIStation(10)
        c10 = Control(u'10', s10)
        s11 = SIStation(11)
        c11 = Control(u'11', s11)
        s12 = SIStation(12)
        c12 = Control(u'12',s12)
        s13 = SIStation(13)
        c13 = Control(u'13', s13)
        
        run = Run(SICard(1))
        run.punches.add(Punch(s10,
                              card_punchtime = datetime(2008,5,3,12,36), sequence=1))
        p2 = Punch(s11,
                   card_punchtime = datetime(2008,5,3,12,38), sequence=2)
        run.punches.add(p2)
        run.punches.add(Punch(s12,
                              manual_punchtime = datetime(2008,5,3,12,39)))
        run.punches.add(Punch(s13,
                              card_punchtime = datetime(2008,5,3,12,37), sequence=3))
        self._store.add(run)
        self.assertFalse(run.check_sequence())
        p2.ignore = True
        self.assertTrue(run.check_sequence())
        p2.ignore = False
        p2.manual_punchtime = datetime(2008,5,3,12,36,30)
        self.assertTrue(run.check_sequence())
        p2.manual_punchtime = None
        c11.override = True
        self.assertTrue(run.check_sequence())

    def test_punchlist(self):
        """check punchlist"""
        run = Run(SICard(2))
        p_1 = Punch(SIStation(9), card_punchtime = datetime(2008,5,3,11,58))
        p1 = Punch(SIStation(10), card_punchtime = datetime(2008,5,3,12,0))
        p2 = Punch(SIStation(11), card_punchtime = datetime(2008,5,3,12,1))
        p3 = Punch(SIStation(12), card_punchtime = datetime(2008,5,3,12,2))
        p5 = Punch(SIStation(13), card_punchtime = datetime(2008,5,3,12,5))

        run.punches.add(p_1)
        run.punches.add(p1)
        run.punches.add(p2)
        run.punches.add(p3)
        run.punches.add(p5)
        self._store.add(run)
        self.assertEquals(run.punchlist(), [p_1, p1,p2,p3,p5])
        p0 = Punch(self._si_s, card_punchtime = datetime(2008,5,3,11,59))
        run.punches.add(p0)
        self.assertEquals(run.punchlist(), [p1,p2,p3,p5])
        p4 = Punch(self._si_f, card_punchtime = datetime(2008,5,3,12,4))
        run.punches.add(p4)
        self.assertEquals(run.punchlist(), [p1, p2, p3])
        p3.manual_punchtime = datetime(2008,5,3,12,0,30)
        self.assertEquals(run.punchlist(), [p1, p3, p2])
                        
if __name__ == '__main__':
    unittest.main()
