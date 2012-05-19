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

from storm.locals import *
from datetime import datetime, timedelta
from bosco.course import Course, Control, SIStation
from bosco.runner import SICard

from bosco.run import Run, Punch
from bosco.ranking import (TimeScoreing,
                           RoundCountScoreing,
                           MassstartStarttime,
                           SelfstartStarttime,
                           RelayStarttime,
                           RelayMassstartStarttime,
                           UnscoreableException,
                           Validator,
                           SequenceCourseValidator)
from bosco.event import Event, RelayEvent

from bosco.test import BoscoTest

class RunTest(BoscoTest):

    def test_start_manual(self):
        """Test that Run.start_time returns the manual start time if present."""
        self.assertEquals(self._runs[0].start_time, datetime(2008,3,19,8,20,35)) 

    def test_finish_first(self):
        """Test that Run.finish_time returns the manual finish time if present."""
        self.assertEquals(self._runs[0].finish_time, datetime(2008,3,19,8,25,35))

    def test_runtime_start_finish(self):
        """Test the run time for a run with start and finish controls."""
        strategy = TimeScoreing(SelfstartStarttime())
        score = strategy.score(self._runs[0])['score']
        self.assertEquals(score, timedelta(minutes=5))
        
    def test_runtime_massstart(self):
        """Test the run time for a run with mass start."""
        strategy = TimeScoreing(MassstartStarttime(datetime(2008,3,19,8,15,15)))
        score = strategy.score(self._runs[1])['score']
        self.assertEquals(score, timedelta(minutes=16, seconds=8))

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

        # reset manual starttime
        self._runs[0].manual_start_time = None
        
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

    def test_score_relay_missing(self):
        """Test that scoreing a relay runner without a run for the previous runner
           throws an UnscoreableException."""

        # remove first run
        run = self._runners[0].sicards.one().runs.one()
        for p in run.punches:
            self._store.remove(p)
        self._store.remove(run)

        strategy = TimeScoreing(RelayMassstartStarttime(datetime(2008,3,19,8,30,23)))
        self.assertRaises(UnscoreableException, strategy.score, self._runs[1])

        # the third runner should still score as normal
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
                          [('ok', 131),
                           ('ok', 132),
                           ('ok', 200),
                           ('ok', 132),
                           ])
        
    def test_validation_additional(self):
        """Test validation of a valid run with additional punches."""
        validator = SequenceCourseValidator(self._course)
        valid = validator.validate(self._runs[2])
        self.assertEquals(valid['status'], Validator.OK)
        self.assertEquals(self._convert_punchlist(valid['punchlist']),
                          [('ok', 131),
                           ('ok', 132),
                           ('ignored', 133),
                           ('ok', 200),
                           ('additional', 134),
                           ('ok', 132),
                           ])
        
    def test_validation_missing(self):
        """Test validation of a run with missing controls."""
        validator = SequenceCourseValidator(self._course)
        valid = validator.validate(self._runs[3])
        self.assertEquals(valid['status'], Validator.MISSING_CONTROLS)
        self.assertEquals(self._convert_punchlist(valid['punchlist']),
                          [('missing', u'131'),
                           ('ok', 132),
                           ('ok', 200),
                           ('ok', 132),
                           ])

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
        # Add override for control 131
        self._c131.override = True

        validator = SequenceCourseValidator(self._course)

        self.assertEquals(validator.validate(self._runs[3])['status'],
                          Validator.OK)
        
    def test_overrride_run(self):
        """Test overrride for a run."""
        validator = SequenceCourseValidator(self._course)
        self._runs[3].override = Validator.OK
        valid = validator.validate(self._runs[3])
        self.assertEquals(valid['status'], Validator.OK)
        self.assertEquals(valid['override'], True)

        self._runs[3].complete = False
        valid = validator.validate(self._runs[3])
        self.assertEquals(valid['status'], Validator.NOT_COMPLETED)
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
        p4 = Punch(SIStation(13), card_punchtime = datetime(2008,5,3,12,5))
        p5 = Punch(SIStation(14), card_punchtime = datetime(2008,5,3,12,6))

        run.punches.add(p_1)
        run.punches.add(p1)
        run.punches.add(p2)
        run.punches.add(p3)
        run.punches.add(p4)
        run.punches.add(p5) # punch without control
        self._store.add(run)

        # add controls for sistations
        c_1 = Control(u'9', store = self._store)
        c1 = Control(u'10', store = self._store)
        c2 = Control(u'11', store = self._store)
        c3 = Control(u'12', store = self._store)
        c4 = Control(u'13', store = self._store)

        self.assertEquals(run.punchlist(), [(p_1, c_1),
                                            (p1,c1),
                                            (p2, c2),
                                            (p3,c3),
                                            (p4, c4)])
        self.assertEquals(run.punchlist(ignored=True), [(p5, None)])
        
        run.card_start_time = datetime(2008,5,3,11,59)
        self.assertEquals(run.punchlist(), [ (p1, c1),
                                             (p2, c2),
                                             (p3, c3),
                                             (p4, c4)])
        self.assertEquals(run.punchlist(ignored=True), [(p_1, c_1),
                                                        (p5, None)])
        
        run.card_finish_time = datetime(2008,5,3,12,4)
        self.assertEquals(run.punchlist(), [(p1, c1),
                                            (p2, c2),
                                            (p3, c3)])
        self.assertEquals(run.punchlist(ignored=True), [(p_1, c_1),
                                                        (p4, c4),
                                                        (p5, None)])
        
        p3.manual_punchtime = datetime(2008,5,3,12,0,30)
        self.assertEquals(run.punchlist(), [(p1, c1),
                                            (p3, c3),
                                            (p2, c2)])
        self.assertEquals(run.punchlist(ignored=True), [(p_1, c_1),
                                                        (p4, c4),
                                                        (p5, None)])

    def _prepare_relay_team(self):
        """Prepares the team for relay testing."""
        self._runs[0].manual_start_time = None
        self._runs[1].course = self._store.find(Course, Course.code == u'B').one()
        self._runs[2].course = self._store.find(Course, Course.code == u'C').one()
        
    def test_relay_team_validation(self):
        """Test correct validation of a team for a relay event."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': None},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None}])
        self._prepare_relay_team()

        self.assertEquals(Validator.OK, event.validate(self._team)['status'])

    def test_relay_team_invalid_run(self):
        """Test validation of a team for a relay event with an invalid run. This team should validate as Validator.MISSING_CONTROLS."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': None},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None}])
        self._prepare_relay_team()
        self._runs[1].override = Validator.MISSING_CONTROLS

        self.assertEquals(Validator.MISSING_CONTROLS, event.validate(self._team)['status'])

    def test_relay_team_run_non_mandatory(self):
        """Test validation of a team for a relay event with an invalid or missing run, which is not mandatory. This team should validate as Validator.OK."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': timedelta(minutes=5)},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None}])
        self._prepare_relay_team()

        self._runs[0].override = Validator.MISSING_CONTROLS
        self.assertEquals(Validator.OK, event.validate(self._team)['status'])

        self._team.members.remove(self._runners[0])
        self.assertEquals(Validator.OK, event.validate(self._team)['status'])
    
    def test_realy_team_unfinished(self):
        """Test validation of a team for a relay event which has not yet finished all legs. This team should validate as Validator.NOT_COMPLETED."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': None},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None}])
        self._prepare_relay_team()
        self._runs[2].complete = False
        self._runs[2].card_finish_time = None
        
        self.assertEquals(Validator.NOT_COMPLETED, event.validate(self._team)['status'])
    
    def test_relay_team_wrong_order(self):
        """Test validation of a team for a relay event which has run in the wrong order. This team should validate as Validator.DISQUALIFIED."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': None},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None}])
        self._prepare_relay_team()
        self._runs[0].course = self._store.find(Course, Course.code == u'B').one()
        self._runs[1].course = self._store.find(Course, Course.code == u'A').one()
        
        self.assertEquals(Validator.DISQUALIFIED, event.validate(self._team)['status'])
    
    def test_relay_team_dnf(self):
        """Test validation of a team for a relay event which did not finish the relay. This team should validate as Validator.DID_NOT_FINISH."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': None},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None}])
        self._prepare_relay_team()
        self._runs[2].card_finish_time = None
        
        self.assertEquals(Validator.DID_NOT_FINISH, event.validate(self._team)['status'])

    def test_relay_team_score(self):
        """Test correct scoreing of a relay team."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': None},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None}])
        self._prepare_relay_team()
        
        self.assertEquals(event.score(self._team)['score'], datetime(2008,3,19,8,36,25)-starttime)

    def test_relay_team_starttime(self):
        """Test correct scoreing of a relay team with finish time of first runner after starttime of second leg, finish time of second runner before starttime of third leg."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': None},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,24,00), 'defaulttime': None},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,31,24), 'defaulttime': None}])
        self._prepare_relay_team()

        self.assertEquals(event.score(self._team)['score'], datetime(2008,3,19,8,36,25)-starttime + timedelta(minutes=1, seconds=35))
        
    def test_relay_team_defaulttime(self):
        """Test correct scoreing of a relay team with defaulttime for a missing, invalid or very long run."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': timedelta(minutes=5)},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,19,00), 'defaulttime': timedelta(minutes=13)},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': timedelta(minutes=13)}])
        self._prepare_relay_team()

        # runner 1 runs longer than the default time
        self.assertEquals(event.score(self._team)['score'], datetime(2008,3,19,8,36,25)-starttime + timedelta(minutes=1))

        # runner 2 has an invalid run
        self._runs[1].override = Validator.MISSING_CONTROLS
        self.assertEquals(event.score(self._team)['score'], datetime(2008,3,19,8,36,25)-starttime + timedelta(minutes=1, seconds=37))
        self._runs[1].override = None
        
        # remove runner 1
        self._team.members.remove(self._runners[0])
        self.assertEquals(event.score(self._team)['score'], datetime(2008,3,19,8,36,25)-starttime + timedelta(minutes=1))
        

    def test_relay_team_unscoreable(self):
        """Test that a relay team with missing runs is not scoreable if there is no defaulttime."""
        starttime = datetime(2008,3,19,8,15,00)
        event = RelayEvent([{'variants': ('A', ), 'starttime': starttime, 'defaulttime': timedelta(minutes=5)},
                            {'variants': ('B', ), 'starttime': datetime(2008,3,19,8,19,00), 'defaulttime': timedelta(minutes=13)},
                            {'variants': ('C', ), 'starttime': datetime(2008,3,19,8,40,00), 'defaulttime': None}])
        self._prepare_relay_team()

        self._team.members.remove(self._runners[2])
        self.assertRaises(UnscoreableException, event.score, self._team)

    def test_roundcount_2controls(self):
        """Test RunCountScoreing for a Course with 2 controls"""
        scoreing = RoundCountScoreing(self._store.find(Course, Course.code == u'D').one())
        self.assertEquals(scoreing.score(self._runs[7])['score'], 3)

    def test_roundcount_mindiff(self):
        """Test that the time between valid punches is more than mindiff"""
        scoreing = RoundCountScoreing(self._store.find(Course, Course.code == u'E').one(),
                                      mindiff = timedelta(seconds=30))
        self.assertEquals(scoreing.score(self._runs[8])['score'], 3)

    def test_roundcount_missing(self):
        """Test that rounds with missing punches are not counted"""
        scoreing = RoundCountScoreing(self._store.find(Course, Course.code == u'D').one())
        self.assertEquals(scoreing.score(self._runs[9])['score'], 2)

if __name__ == '__main__':
    unittest.main()
