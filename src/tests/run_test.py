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

from run import Run
from ranking import (MassStartTimeScoreingStrategy,
                     SelfStartTimeScoreingStrategy,
                     RelayTimeScoreingStrategy,
                     UnscoreableException,
                     MassStartRelayTimeScoreingStrategy,
                     ValidationStrategy,
                     SequenceCourseValidationStrategy,
                     Ranking, EventRanking)

class RunTest(unittest.TestCase):

    # Create store as class variable so that every test uses the same
    # database connection
    _store = Store(create_database('postgres:24h_test'))
    
    def setUp(self):

        # Create start and finish control
        S = Control(u'S', SIStation(SIStation.START))
        F = Control(u'F', SIStation(SIStation.FINISH))

        # create control with 2 sistations
        c200 = Control(u'200', SIStation(200))
        c200.sistations.add(SIStation(201))
        self._c131 = self._store.add(Control(u'131', SIStation(131)))

        # create sistation without any control
        self._store.add(SIStation(133))
        
        # Create a Course
        self._course = self._store.add(Course(u'A', length = 1679, climb = 587))
        self._course.extend([S, u'131', u'132', c200, u'132', F])

        # Create categorys
        self._cat_ind = self._store.add(Category(u'HAM'))
        cat_team = Category(u'D135')
        
        # Create Runners
        self._runners = []
        
        self._runners.append(Runner(u'Muster', u'Hans', 655465, u'HAM', self._store))
        self._runners.append(Runner(u'Gerster', u'Trudi', 765477, u'HAM', self._store))
        self._runners.append(Runner(u'Mueller', u'Hans', 768765, u'HAM', self._store))
        self._runners.append(Runner(u'Missing', u'The', 113456, u'HAM', self._store))
        self._runners.append(Runner(u'Gugus', u'Dada', 56789, u'HAM', self._store))
        self._runners.append(Runner(u'Al', u'Missing', 12345, u'HAM', self._store))
        

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
                              self._store
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
                              self._store
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
                              self._store
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
                              self._store
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
                              self._store
                              ))
        self._runs[4].complete = True

        # empty run
        self._runs.append(Run(12345, u'A', [], self._store))
        self._runs[5].complete = True

        self._store.commit()

    def tearDown(self):
        # Clean up Database
        self._store.execute('TRUNCATE course CASCADE')
        self._store.execute('TRUNCATE sistation CASCADE')
        self._store.execute('TRUNCATE control CASCADE')
        self._store.execute('TRUNCATE run CASCADE')
        self._store.execute('TRUNCATE punch CASCADE')
        self._store.execute('TRUNCATE sicard CASCADE')
        self._store.execute('TRUNCATE runner CASCADE')
        self._store.execute('TRUNCATE category CASCADE')
        self._store.commit()
        
    def test_start_last(self):
        """Test that Run.start() returns the last punch on a start control."""
        self.assertEquals(self._runs[0].start(), datetime(2008,3,19,8,20,35)) 

    def test_finish_first(self):
        """Test that Run.finish() returns the first punch on a finish control."""
        self.assertEquals(self._runs[0].finish(), datetime(2008,3,19,8,25,35))

    def test_runtime_start_finish(self):
        """Test the run time for a run with start and finish controls."""
        strategy = SelfStartTimeScoreingStrategy()
        score = strategy.score(self._runs[0])
        self.assertEquals(score, timedelta(minutes=5))
        
    def test_runtime_massstart(self):
        """Test the run time for a run with mass start."""
        strategy = MassStartTimeScoreingStrategy(datetime(2008,3,19,8,15,15))
        score = strategy.score(self._runs[0])
        self.assertEquals(score, timedelta(minutes=10, seconds=20))

    def test_runtime_relay(self):
        """Test the run time for a relay leg wich starts with the finish time of the
           previous run."""
        strategy = RelayTimeScoreingStrategy(datetime(2008,3,19,8,20,0))
        score = strategy.score(self._runs[1])
        self.assertEquals(score, timedelta(minutes=5, seconds=48))

    def test_runtime_relay_first(self):
        """Test RelayTimeScoreingStrategy for the first runner (mass start)"""
        strategy = RelayTimeScoreingStrategy(datetime(2008,3,19,8,20,0))
        score = strategy.score(self._runs[0])
        self.assertEquals(score, timedelta(minutes=5, seconds=35))

    def test_runtime_relay_massstart(self):
        """Test the run time for a relay leg which was started with a mass start if
        the finish time of the previous runner is after the mass start time."""
        strategy = MassStartRelayTimeScoreingStrategy(datetime(2008,3,19,8,30,23))
        score = strategy.score(self._runs[1])
        self.assertEquals(score, timedelta(minutes=5, seconds=48))
        score = strategy.score(self._runs[2])
        self.assertEquals(score, timedelta(minutes=6, seconds=2))

    def test_validation_missing(self):
        """Test validation of a run with missing controls."""
        validator = SequenceCourseValidationStrategy(self._course)
        (valid, info) = validator.validate(self._runs[3])
        self.assertEquals(valid, ValidationStrategy.MISSING_CONTROLS)
        self.assertEquals(info['missing'], [self._c131])

    def test_validation_all_missing(self):
        """Test that all controls of a run are missing if the validated run is empty."""
        validator = SequenceCourseValidationStrategy(self._course)
        (valid, info) = validator.validate(self._runs[5])
        self.assertEquals(valid, ValidationStrategy.DID_NOT_FINISH)
        self.assertEquals([ c.code for c in info['missing']],
                          [u'S',  u'131', u'132', u'200', u'132', u'F'])
        
    def test_ranking_course(self):
        """Test the correct ranking of runs in a course."""

        ranking = list(EventRanking().ranking(self._course))
        self.assertEquals(ranking[0]['rank'], 1)
        self.assertEquals(ranking[0]['validation'], ValidationStrategy.OK)
        self.assertTrue(ranking[0]['item'] == self._runs[0] or ranking[0]['item'] == self._runs[2])
        
        self.assertEquals(ranking[1]['rank'], 1)
        self.assertEquals(ranking[1]['validation'], ValidationStrategy.OK)
        self.assertTrue(ranking[1]['item'] == self._runs[0] or ranking[1]['item'] == self._runs[2])

        self.assertEquals(ranking[2]['rank'], 3)
        self.assertEquals(ranking[2]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[2]['item'], self._runs[4])

        self.assertEquals(ranking[3]['rank'], 4)
        self.assertEquals(ranking[3]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[3]['item'], self._runs[1])

        self.assertEquals(ranking[4]['rank'], None)
        self.assertEquals(ranking[4]['validation'], ValidationStrategy.MISSING_CONTROLS)
        self.assertEquals(ranking[4]['item'], self._runs[3])

    def test_ranking_category(self):
        """Test the correct ranking of runs in a category."""

        ranking = list(EventRanking().ranking(self._cat_ind))
        self.assertEquals(ranking[0]['rank'], 1)
        self.assertEquals(ranking[0]['validation'], ValidationStrategy.OK)
        self.assertTrue(ranking[0]['item'] == self._runners[0] or ranking[0]['item'] == self._runners[2])

        self.assertEquals(ranking[1]['rank'], 1)
        self.assertEquals(ranking[1]['validation'], ValidationStrategy.OK)
        self.assertTrue(ranking[1]['item'] == self._runners[0] or ranking[1]['item'] == self._runners[2])

        self.assertEquals(ranking[2]['rank'], 3)
        self.assertEquals(ranking[2]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[2]['item'], self._runners[4])

        self.assertEquals(ranking[3]['rank'], 4)
        self.assertEquals(ranking[3]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[3]['item'], self._runners[1])

        self.assertEquals(ranking[4]['rank'], None)
        self.assertEquals(ranking[4]['validation'], ValidationStrategy.MISSING_CONTROLS)
        self.assertEquals(ranking[4]['item'], self._runners[3])
        
    def test_overrride_control(self):
        """Test override for a control."""
        validator = SequenceCourseValidationStrategy(self._course)

        # Add override for control 131
        self._c131.override = True
        self.assertEquals(validator.validate(self._runs[3])[0], ValidationStrategy.OK)
        
    def test_overrride_run(self):
        """Test overrride for a run."""
        validator = SequenceCourseValidationStrategy(self._course)
        self._runs[3].override = True
        self.assertEquals(validator.validate(self._runs[3])[0], ValidationStrategy.OK)
        
if __name__ == '__main__':
    unittest.main()
