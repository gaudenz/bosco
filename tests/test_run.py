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

import pytest

from datetime import datetime
from datetime import timedelta

from storm.locals import *

from bosco.course import Control
from bosco.course import Course
from bosco.course import SIStation
from bosco.run import Punch
from bosco.run import Run
from bosco.runner import SICard
from bosco.ranking import MassstartStarttime
from bosco.ranking import RelayMassstartStarttime
from bosco.ranking import RelayStarttime
from bosco.ranking import RoundCountScoreing
from bosco.ranking import SelfstartStarttime
from bosco.ranking import SequenceCourseValidator
from bosco.ranking import TimeScoreing
from bosco.ranking import UnscoreableException
from bosco.ranking import Validator
from bosco.event import Event
from bosco.event import RelayEvent

def test_start_manual(testevent):
    """Test that Run.start_time returns the manual start time if present."""
    assert testevent._runs[0].start_time == datetime(2008, 3, 19, 8, 20, 35)

def test_finish_first(testevent):
    """Test that Run.finish_time returns the manual finish time if present."""
    assert testevent._runs[0].finish_time == datetime(2008, 3, 19, 8, 25, 35)

def test_runtime_start_finish(testevent):
    """Test the run time for a run with start and finish controls."""
    strategy = TimeScoreing(SelfstartStarttime())
    score = strategy.score(testevent._runs[0])['score']
    assert score == timedelta(minutes=5)

def test_runtime_massstart(testevent):
    """Test the run time for a run with mass start."""
    strategy = TimeScoreing(MassstartStarttime(datetime(2008, 3, 19, 8, 15, 15)))
    score = strategy.score(testevent._runs[1])['score']
    assert score == timedelta(minutes=16, seconds=8)

def test_runtime_relay(testevent):
    """Test the run time for a relay leg wich starts with the finish time of the
       previous run."""
    strategy = TimeScoreing(RelayStarttime(datetime(2008, 3, 19, 8, 15, 15),
                                           ordered = True))

    score = strategy.score(testevent._runs[1])['score']
    assert score == timedelta(minutes=5, seconds=48)

    score = strategy.score(testevent._runs[2])['score']
    assert score == timedelta(minutes=5, seconds=2)

def test_runtime_relay_first(testevent):
    """Test RelayTimeScoreing for the first runner (mass start)"""
    strategy = TimeScoreing(RelayStarttime(datetime(2008, 3, 19, 8, 20, 0)))

    # reset manual starttime
    testevent._runs[0].manual_start_time = None

    score = strategy.score(testevent._runs[0])['score']
    assert score == timedelta(minutes=5, seconds=35)

def test_runtime_relay_massstart(testevent):
    """Test the run time for a relay leg which was started with a mass start if
       the finish time of the previous runner is after the mass start time."""
    strategy = TimeScoreing(
        RelayMassstartStarttime(datetime(2008, 3, 19, 8, 30, 23))
    )

    score = strategy.score(testevent._runs[1])['score']
    assert score == timedelta(minutes=5, seconds=48)

    score = strategy.score(testevent._runs[2])['score']
    assert score == timedelta(minutes=6, seconds=2)

def test_score_relay_missing(testevent):
    """Test that scoreing a relay runner without a run for the previous runner
       throws an UnscoreableException."""

    # remove first run
    run = testevent._runners[0].sicards.one().runs.one()
    for p in run.punches:
        testevent._store.remove(p)
    testevent._store.remove(run)

    strategy = TimeScoreing(RelayMassstartStarttime(datetime(2008, 3, 19, 8, 30, 23)))

    with pytest.raises(UnscoreableException):
        strategy.score(testevent._runs[1])

    # the third runner should still score as normal
    score = strategy.score(testevent._runs[2])['score']
    assert score == timedelta(minutes=6, seconds=2)

def test_validation_valid(testevent):
    """Test validation of a valid run."""
    validator = SequenceCourseValidator(testevent._course)
    valid = validator.validate(testevent._runs[1])
    assert valid['status'] == Validator.OK
    assert testevent._convert_punchlist(valid['punchlist']) == [('ok', 131),
                                                                ('ok', 132),
                                                                ('ok', 200),
                                                                ('ok', 132),
                                                                ]

def test_validation_additional(testevent):
    """Test validation of a valid run with additional punches."""
    validator = SequenceCourseValidator(testevent._course)
    valid = validator.validate(testevent._runs[2])
    assert valid['status'] == Validator.OK
    assert (testevent._convert_punchlist(valid['punchlist'])
            == [('ok', 131),
                ('ok', 132),
                ('ignored', 133),
                ('ok', 200),
                ('additional', 134),
                ('ok', 132),
            ])

def test_validation_missing(testevent):
    """Test validation of a run with missing controls."""
    validator = SequenceCourseValidator(testevent._course)
    valid = validator.validate(testevent._runs[3])
    assert valid['status'] == Validator.MISSING_CONTROLS
    assert (testevent._convert_punchlist(valid['punchlist'])
            == [('missing', '131'),
                ('ok', 132),
                ('ok', 200),
                ('ok', 132),
            ])

def test_validation_all_missing(testevent):
    """Test that all controls of a run are missing if the validated run is
       empty.
    """
    validator = SequenceCourseValidator(testevent._course)
    valid  = validator.validate(testevent._runs[5])
    assert valid['status'] == Validator.DID_NOT_FINISH
    punchlist = [(p[0], isinstance(p[1], Punch)
                  and p[1].sistation.id or p[1].code)
                 for p in valid['punchlist']]
    assert punchlist == [('missing', '131'),
                         ('missing', '132'),
                         ('missing', '200'),
                         ('missing', '132')]

def test_ranking_course(testevent):
    """Test the correct ranking of runs in a course."""

    ranking = list(Event({}, store=testevent._store).ranking(testevent._course))
    assert ranking[0]['rank'] == 1
    assert ranking[0]['validation']['status'] == Validator.OK
    assert (ranking[0]['item'] == testevent._runs[0]
            or ranking[0]['item'] == testevent._runs[2])

    assert ranking[1]['rank'] == 1
    assert ranking[1]['validation']['status'] == Validator.OK
    assert (ranking[1]['item'] == testevent._runs[0]
            or ranking[1]['item'] == testevent._runs[2])

    assert ranking[2]['rank'] == 3
    assert ranking[2]['validation']['status'] == Validator.OK
    assert ranking[2]['item'] == testevent._runs[4]

    assert ranking[3]['rank'] == 4
    assert ranking[3]['validation']['status'] == Validator.OK
    assert ranking[3]['item'] == testevent._runs[1]

    assert ranking[4]['rank'] == None
    assert ranking[4]['validation']['status'] == Validator.MISSING_CONTROLS
    assert ranking[4]['item'] == testevent._runs[3]

def test_ranking_category(testevent):
    """Test the correct ranking of runs in a category."""

    event = Event({}, store=testevent._store)
    ranking = list(event.ranking(testevent._cat_ind))

    assert ranking[0]['rank'] == 1
    assert ranking[0]['validation']['status'] == Validator.OK
    assert (ranking[0]['item'] == testevent._runners[0]
            or ranking[0]['item'] == testevent._runners[2])

    assert ranking[1]['rank'] == 1
    assert ranking[1]['validation']['status'] == Validator.OK
    assert (ranking[1]['item'] == testevent._runners[0]
            or ranking[1]['item'] == testevent._runners[2])

    assert ranking[2]['rank'] == 3
    assert ranking[2]['validation']['status'] == Validator.OK
    assert ranking[2]['item'] == testevent._runners[4]

    assert ranking[3]['rank'] == 4
    assert ranking[3]['validation']['status'] == Validator.OK
    assert ranking[3]['item'] == testevent._runners[1]

    assert ranking[4]['rank'] == None
    assert ranking[4]['validation']['status'] == Validator.MISSING_CONTROLS
    assert ranking[4]['item'] == testevent._runners[3]

def test_ranking_random_access(testevent):
    """Test "random access" functions of Ranking"""

    ranking = Event({}, store=testevent._store).ranking(testevent._course)

    assert ranking.rank(testevent._runs[0]) == 1
    assert ranking.rank(testevent._runs[2]) == 1
    assert ranking.rank(testevent._runs[4]) == 3
    assert ranking.rank(testevent._runs[1]) == 4
    assert ranking.rank(testevent._runs[3]) == None

    assert ranking.score(testevent._runs[0]) == timedelta(minutes=5)

    with pytest.raises(KeyError):
        ranking.rank(testevent._runs[6])

def test_overrride_control(testevent):
    """Test override for a control."""
    # Add override for control 131
    testevent._c131.override = True

    validator = SequenceCourseValidator(testevent._course)

    assert (validator.validate(testevent._runs[3])['status']
            == Validator.OK)

def test_overrride_run(testevent):
    """Test overrride for a run."""
    validator = SequenceCourseValidator(testevent._course)
    testevent._runs[3].override = Validator.OK
    valid = validator.validate(testevent._runs[3])
    assert valid['status'] == Validator.OK
    assert valid['override'] == True

    testevent._runs[3].complete = False
    valid = validator.validate(testevent._runs[3])
    assert valid['status'] == Validator.NOT_COMPLETED
    assert valid['override'] == True

    testevent._runs[1].override = Validator.DISQUALIFIED
    valid = validator.validate(testevent._runs[1])
    assert valid['status'] == Validator.DISQUALIFIED
    assert valid['override'] == True

def test_punchtime(testevent):
    """check for correct punchtime handling."""
    p = Punch(SIStation(10), card_punchtime = datetime(2008, 5, 3, 12, 0o2))
    assert p.punchtime == datetime(2008, 5, 3, 12, 0o2)
    p.manual_punchtime = datetime(2008, 5, 3, 12, 0o3)
    assert p.punchtime == datetime(2008, 5, 3, 12, 0o3)
    p.manual_punchtime = datetime(2008, 5, 3, 12, 0o1)
    assert p.punchtime == datetime(2008, 5, 3, 12, 0o1)

def test_check_sequence(testevent):
    """Test punch sequence checking"""
    s10 = SIStation(10)
    c10 = Control('10', s10)
    s11 = SIStation(11)
    c11 = Control('11', s11)
    s12 = SIStation(12)
    c12 = Control('12', s12)
    s13 = SIStation(13)
    c13 = Control('13', s13)

    run = Run(SICard(1))
    run.punches.add(Punch(s10,
                          card_punchtime = datetime(2008, 5, 3, 12, 36),
                          sequence=1))
    p2 = Punch(s11,
               card_punchtime = datetime(2008, 5, 3, 12, 38), sequence=2)
    run.punches.add(p2)
    run.punches.add(Punch(s12,
                          manual_punchtime = datetime(2008, 5, 3, 12, 39)))
    run.punches.add(Punch(s13,
                          card_punchtime = datetime(2008, 5, 3, 12, 37),
                          sequence=3))
    testevent._store.add(run)
    assert not run.check_sequence()
    p2.ignore = True
    assert run.check_sequence()
    p2.ignore = False
    p2.manual_punchtime = datetime(2008, 5, 3, 12, 36, 30)
    assert run.check_sequence()
    p2.manual_punchtime = None
    c11.override = True
    assert run.check_sequence()

def test_punchlist(testevent):
    """check punchlist"""

    run = Run(SICard(2))
    p_1 = Punch(SIStation(9), card_punchtime = datetime(2008, 5, 3, 11, 58))
    p1 = Punch(SIStation(10), card_punchtime = datetime(2008, 5, 3, 12, 0))
    p2 = Punch(SIStation(11), card_punchtime = datetime(2008, 5, 3, 12, 1))
    p3 = Punch(SIStation(12), card_punchtime = datetime(2008, 5, 3, 12, 2))
    p4 = Punch(SIStation(13), card_punchtime = datetime(2008, 5, 3, 12, 5))
    p5 = Punch(SIStation(14), card_punchtime = datetime(2008, 5, 3, 12, 6))

    run.punches.add(p_1)
    run.punches.add(p1)
    run.punches.add(p2)
    run.punches.add(p3)
    run.punches.add(p4)
    run.punches.add(p5) # punch without control
    testevent._store.add(run)

    # add controls for sistations
    c_1 = Control('9', store = testevent._store)
    c1 = Control('10', store = testevent._store)
    c2 = Control('11', store = testevent._store)
    c3 = Control('12', store = testevent._store)
    c4 = Control('13', store = testevent._store)

    assert run.punchlist() == [(p_1, c_1),
                               (p1, c1),
                               (p2, c2),
                               (p3, c3),
                               (p4, c4)]
    assert run.punchlist(ignored=True) == [(p5, None)]

    run.card_start_time = datetime(2008, 5, 3, 11, 59)
    assert run.punchlist() == [ (p1, c1),
                                (p2, c2),
                                (p3, c3),
                                (p4, c4)]
    assert run.punchlist(ignored=True) == [(p_1, c_1),
                                           (p5, None)]

    run.card_finish_time = datetime(2008, 5, 3, 12, 4)
    assert run.punchlist() == [(p1, c1),
                               (p2, c2),
                               (p3, c3)]
    assert run.punchlist(ignored=True) == [(p_1, c_1),
                                           (p4, c4),
                                           (p5, None)]

    p3.manual_punchtime = datetime(2008, 5, 3, 12, 0, 30)
    assert run.punchlist() == [(p1, c1),
                               (p3, c3),
                               (p2, c2)]
    assert run.punchlist(ignored=True) == [(p_1, c_1),
                                           (p4, c4),
                                           (p5, None)]

def test_relay_team_validation(testevent):
    """Test correct validation of a team for a relay event."""
    event = testevent._prepare_relay()

    assert Validator.OK == event.validate(testevent._team)['status']

def test_relay_team_invalid_run(testevent):
    """
    Test validation of a team for a relay event with an invalid run. This team
    should validate as Validator.MISSING_CONTROLS.
    """
    event = testevent._prepare_relay()
    testevent._runs[1].override = Validator.MISSING_CONTROLS

    assert (Validator.MISSING_CONTROLS
            == event.validate(testevent._team)['status'])

def test_relay_team_run_non_mandatory(testevent):
    """
    Test validation of a team for a relay event with an invalid or missing run,
    which is not mandatory. This team should validate as Validator.OK.
    """
    testevent._prepare_relay_team()

    # modified event setup, can't change legs after init
    event = RelayEvent(
        {'D135': [{'name': '1',
                   'variants': ('A', ),
                   'starttime': testevent._team_start_time,
                   'defaulttime': timedelta(minutes=5)},
                  {'name': '2',
                   'variants': ('B', ),
                   'starttime': datetime(2008, 3, 19, 8, 40, 00),
                   'defaulttime': None},
                  {'name': '3', 'variants': ('C', ),
                   'starttime': datetime(2008, 3, 19, 8, 40, 00),
                   'defaulttime': None},
                  ],
        },
        store = testevent._store,
    )

    testevent._runs[0].override = Validator.MISSING_CONTROLS
    assert Validator.OK == event.validate(testevent._team)['status']

    testevent._team.members.remove(testevent._runners[0])
    assert Validator.OK == event.validate(testevent._team)['status']

def test_realy_team_unfinished(testevent):
    """
    Test validation of a team for a relay event which has not yet finished all
    legs. This team should validate as Validator.NOT_COMPLETED.
    """
    event = testevent._prepare_relay()
    testevent._runs[2].complete = False
    testevent._runs[2].card_finish_time = None

    assert Validator.NOT_COMPLETED == event.validate(testevent._team)['status']

def test_relay_team_wrong_order(testevent):
    """
    Test validation of a team for a relay event which has run in the wrong
    order. This team should validate as Validator.DISQUALIFIED.
    """
    event = testevent._prepare_relay()
    course_A = testevent._store.find(Course, Course.code == 'A').one()
    course_B = testevent._store.find(Course, Course.code == 'B').one()
    testevent._runs[0].course = course_B
    testevent._runs[1].course = course_A

    assert Validator.DISQUALIFIED == event.validate(testevent._team)['status']

def test_relay_team_dnf(testevent):
    """
    Test validation of a team for a relay event which did not finish the relay.
    This team should validate as Validator.DID_NOT_FINISH.
    """
    event = testevent._prepare_relay()
    testevent._runs[2].card_finish_time = None

    assert (Validator.DID_NOT_FINISH
            == event.validate(testevent._team)['status'])

def test_relay_team_score(testevent):
    """Test correct scoreing of a relay team."""
    event = testevent._prepare_relay()

    assert event.score(testevent._team)['score'] == testevent._team_time

def test_relay_team_starttime(testevent):
    """
    Test correct scoreing of a relay team with finish time of first runner
    after starttime of second leg, finish time of second runner before
    starttime of third leg.
    """
    testevent._prepare_relay_team()

    # modified event setup, can't change legs after init
    event = RelayEvent(
        {'D135': [{'name': '1',
                   'variants': ('A', ),
                   'starttime': testevent._team_start_time,
                   'defaulttime': None},
                  {'name': '2',
                   'variants': ('B', ),
                   'starttime': datetime(2008, 3, 19, 8, 24, 00),
                   'defaulttime': None},
                  {'name': '3',
                   'variants': ('C', ),
                   'starttime': datetime(2008, 3, 19, 8, 31, 24),
                   'defaulttime': None},
                  ],
        },
        store = testevent._store,
    )

    assert (event.score(testevent._team)['score']
            == testevent._team_time + timedelta(minutes=1, seconds=35))

def test_relay_team_defaulttime(testevent):
    """
    Test correct scoreing of a relay team with defaulttime for a missing,
    invalid or very long run.
    """
    testevent._prepare_relay_team()

    # modified event setup, can't change legs after init
    event = RelayEvent(
        {'D135': [{'name': '1',
                   'variants': ('A', ),
                   'starttime': testevent._team_start_time,
                   'defaulttime': timedelta(minutes=5)},
                  {'name': '2',
                   'variants': ('B', ),
                   'starttime': datetime(2008, 3, 19, 8, 19, 00),
                   'defaulttime': timedelta(minutes=13)},
                  {'name': '3',
                   'variants': ('C', ),
                   'starttime': datetime(2008, 3, 19, 8, 40, 00),
                   'defaulttime': timedelta(minutes=13)},
                  ],
        },
        store = testevent._store,
    )

    # runner 1 runs longer than the default time
    assert (event.score(testevent._team)['score']
            == testevent._team_time + timedelta(minutes=1))

    # runner 2 has an invalid run
    testevent._runs[1].override = Validator.MISSING_CONTROLS
    assert (event.score(testevent._team)['score']
            == testevent._team_time + timedelta(minutes=1, seconds=37))
    testevent._runs[1].override = None

    # remove runner 1
    testevent._team.members.remove(testevent._runners[0])
    assert (event.score(testevent._team)['score']
            == testevent._team_time + timedelta(minutes=1))


def test_relay_team_unscoreable(testevent):
    """
    Test that a relay team with missing runs is not scoreable (score = 0) if
    there is no defaulttime.
    """
    event = testevent._prepare_relay()

    testevent._team.members.remove(testevent._runners[2])
    assert event.score(testevent._team)['score'] == timedelta(0)

def test_roundcount_2controls(testevent):
    """Test RunCountScoreing for a Course with 2 controls"""
    course = testevent._store.find(Course, Course.code == 'D').one()
    scoreing = RoundCountScoreing(course)
    assert scoreing.score(testevent._runs[7])['score'] == 3

def test_roundcount_mindiff(testevent):
    """Test that the time between valid punches is more than mindiff"""
    course = testevent._store.find(Course, Course.code == 'E').one()
    scoreing = RoundCountScoreing(course, mindiff = timedelta(seconds=30))
    assert scoreing.score(testevent._runs[8])['score'] == 3

def test_roundcount_missing(testevent):
    """Test that rounds with missing punches are not counted"""
    course = testevent._store.find(Course, Course.code == 'D').one()
    scoreing = RoundCountScoreing(course)
    assert scoreing.score(testevent._runs[9])['score'] == 2
