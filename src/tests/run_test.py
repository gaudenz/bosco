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
from ranking import MassStartTimeScoreingStrategy, SelfStartTimeScoreingStrategy, RelayTimeScoreingStrategy, UnscoreableException, MassStartRelayTimeScoreingStrategy, ValidationStrategy, SequenceCourseValidationStrategy

class RunTest(unittest.TestCase):

    # Create store as class variable so that every test uses the same
    # database connection
    _store = Store(create_database('postgres:24h_test'))
    
    def setUp(self):

        # Create some controls
        S = Control(u'S', SIStation(SIStation.START))
        F = Control(u'F', SIStation(SIStation.FINISH))
        a = Control(u'131', SIStation(131))
        b = Control(u'132', SIStation(132))
        c = Control(u'200', SIStation(200))
        c.sistations.add(SIStation(201))

        # Create a Course
        self._course = Course(u'A')
        self._store.add(self._course)
        self._course.append(S)
        self._course.append(a)
        self._course.append(b)
        self._course.append(c)
        self._course.append(F)

        # Create categorys
        self._cat_ind = Category(u'HAM')
        cat_team = Category(u'D135')
        
        # Create an SICards
        cards = []
        self._runners = []
        
        cards.append(SICard(655465))
        self._runners.append(Runner(u'Hans', u'Muster', cards[0]))

        cards.append(SICard(765477))
        self._runners.append(Runner(u'Trudi', u'Gerster', cards[1]))
                              
        cards.append(SICard(768765))
        self._runners.append(Runner(u'Hans', u'Müller', cards[2]))
                              
        for r in self._runners:
            r.category = self._cat_ind
            self._store.add(r)

        # Create a team
        team = Team(u'1', u'The best team ever', self._runners[0], cat_team)
        # Add team to store and flush to avoid cycles
        self._store.add(team)
        self._store.flush()
        team.members.add(self._runners[0])
        team.members.add(self._runners[1])
        team.members.add(self._runners[2])
        
        # Create a runs
        self._runs = []
        self._runs.append(Run(cards[0], self._course))
        self._store.add(self._runs[0])
        punches = [ (SIStation.START, datetime(2008,3,19,8,20,32)),
                    (SIStation.START, datetime(2008,3,19,8,20,35)),
                    (131,datetime(2008,3,19,8,22,39)),
                    (132,datetime(2008,3,19,8,23,35)),
                    (201,datetime(2008,3,19,8,24,35)),
                    (SIStation.FINISH,datetime(2008,3,19,8,25,35)),
                    (SIStation.FINISH,datetime(2008,3,19,8,25,37)),
                  ]
        self._runs[0].add_punchlist(punches)
        self._runs[0].complete = True

        self._runs.append(Run(cards[1], self._course))
        self._store.add(self._runs[1])
        punches = [ (SIStation.START, datetime(2008,3,19,8,25,50)),
                    (131,datetime(2008,3,19,8,27,39)),
                    (132,datetime(2008,3,19,8,28,35)),
                    (200,datetime(2008,3,19,8,29,35)),
                    (SIStation.FINISH,datetime(2008,3,19,8,31,23)),
                  ]
        self._runs[1].add_punchlist(punches)
        self._runs[1].complete = True

        self._runs.append(Run(cards[2], self._course))
        self._store.add(self._runs[2])
        punches = [ (SIStation.START, datetime(2008,3,19,8,31,25)),
                    (131,datetime(2008,3,19,8,33,39)),
                    (132,datetime(2008,3,19,8,34,35)),
                    (200,datetime(2008,3,19,8,35,35)),
                    (SIStation.FINISH,datetime(2008,3,19,8,36,25)),
                  ]
        self._runs[2].add_punchlist(punches)
        self._runs[2].complete = True

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
        strategy = RelayTimeScoreingStrategy()
        score = strategy.score(self._runs[1])
        self.assertEquals(score, timedelta(minutes=5, seconds=48))

    def test_runtime_unscorealbe_first(self):
        """Test that it is impossible to score the first runner of a team with the
        RelayTimeScoreingStrategy."""
        strategy = RelayTimeScoreingStrategy()
        self.assertRaises(UnscoreableException, strategy.score, self._runs[0])

    def test_runtime_relay_massstart(self):
        """Test the run time for a relay leg which was started with a mass start if
        the finish time of the previous runner is after the mass start time."""
        strategy = MassStartRelayTimeScoreingStrategy(datetime(2008,3,19,8,30,23))
        score = strategy.score(self._runs[1])
        self.assertEquals(score, timedelta(minutes=5, seconds=48))
        score = strategy.score(self._runs[2])
        self.assertEquals(score, timedelta(minutes=6, seconds=2))
        
    def test_ranking_course(self):
        """Test the correct ranking of runs in a course."""
        score = SelfStartTimeScoreingStrategy()
        validator = self._course.validator(SequenceCourseValidationStrategy)
        ranking = [ r for r in self._course.ranking(score, validator) ]
        self.assertEquals(ranking[0]['rank'], 1)
        self.assertEquals(ranking[0]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[0]['item'], self._runs[0])
        self.assertEquals(ranking[1]['rank'], 1)
        self.assertEquals(ranking[1]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[1]['item'], self._runs[2])
        self.assertEquals(ranking[2]['rank'], 3)
        self.assertEquals(ranking[2]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[2]['item'], self._runs[1])

    def test_ranking_category(self):
        """Test the correct ranking of runs in a category."""
        score = SelfStartTimeScoreingStrategy()
        validator = self._course.validator(SequenceCourseValidationStrategy)
        ranking = [ r for r in self._cat_ind.ranking(score, validator) ]
        self.assertEquals(ranking[0]['rank'], 1)
        self.assertEquals(ranking[0]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[0]['item'], self._runners[0])
        self.assertEquals(ranking[1]['rank'], 1)
        self.assertEquals(ranking[2]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[1]['item'], self._runners[2])
        self.assertEquals(ranking[2]['rank'], 3)
        self.assertEquals(ranking[2]['validation'], ValidationStrategy.OK)
        self.assertEquals(ranking[2]['item'], self._runners[1])
        
    
if __name__ == '__main__':
    unittest.main()
