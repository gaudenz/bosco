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

from subprocess import check_call,STDOUT
from cPickle import load
from datetime import datetime
from os.path import join, dirname
import sys

from storm.locals import *

from bosco.course import Course, Control, SIStation
from bosco.runner import Runner, Category, Team, SICard
from bosco.run import Run, Punch


class BoscoTest(unittest.TestCase):

    # Create store as class variable so that every test uses the same
    # database connection
    _store = Store(create_database('postgres:bosco_test'))
    
    def setUp(self):

        # create control with 2 sistations
        c200 = Control(u'200', SIStation(200))
        c200.sistations.add(SIStation(201))
        self._c131 = self._store.add(Control(u'131', SIStation(131)))

        # create sistation without any control
        self._store.add(SIStation(133))

        # create sistation and control not in course
        self._store.add(Control(u'134', store = self._store))
        
        # Create a Course
        self._course = self._store.add(Course(u'A', length = 1679, climb = 587))
        self._course.extend([u'131', u'132', c200, u'132'])

        # Add additional course for RelayEvent testing, they have the same controls
        c = self._store.add(Course(u'B', length = 1679, climb = 587))
        c.extend([u'131', u'132', c200, u'132'])
        c = self._store.add(Course(u'C', length = 1679, climb = 587))
        c.extend([u'131', u'132', c200, u'132'])

        # Add additional course for RoundCountScoreing
        c = self._store.add(Course(u'D', length = 0, climb = 0))
        c.extend([u'131', c200])
        c = self._store.add(Course(u'E', length = 0, climb = 0))
        c.extend([c200])
        
        # Create categorys
        self._cat_ind = self._store.add(Category(u'HAM'))
        cat_team = Category(u'D135')
        
        # Create Runners
        self._runners = []
        
        self._runners.append(Runner(u'Muster', u'Hans', SICard(655465), 
                                    self._cat_ind, u'101'))
        self._runners.append(Runner(u'Gerster', u'Trudi', SICard(765477), 
                                    self._cat_ind, u'102'))
        self._runners.append(Runner(u'Mueller', u'Hans', SICard(768765), 
                                    self._cat_ind, u'103'))
        self._runners.append(Runner(u'Missing', u'The', SICard(113456),
                                    self._cat_ind))
        self._runners.append(Runner(u'Gugus', u'Dada', SICard(56789), 
                                    self._cat_ind))
        self._runners.append(Runner(u'Al', u'Missing', SICard(12345), 
                                    self._cat_ind))
        

        # Create a team
        self._team = Team(u'1', u'The best team ever', category= cat_team)
        self._team.members.add(self._runners[0])
        self._team.members.add(self._runners[1])
        self._team.members.add(self._runners[2])
        
        # Create a runs
        self._runs = []

        # double start and finish punches, punch on sistation 201 for control 200
        self._runs.append(Run(655465,
                              u'A',
                              [(131,datetime(2008,3,19,8,22,39)),
                               (132,datetime(2008,3,19,8,23,35)),
                               (201,datetime(2008,3,19,8,24,35)),
                               (132,datetime(2008,3,19,8,25,0)),
                               ],
                              card_start_time = datetime(2008,3,19,8,20,32),
                              card_finish_time = datetime(2008,3,19,8,25,37),
                              store = self._store
                              ))
        self._runs[0].manual_start_time = datetime(2008,3,19,8,20,35)
        self._runs[0].manual_finish_time = datetime(2008,3,19,8,25,35)
        self._runs[0].complete = True

        # normal run
        self._runs.append(Run(765477,
                              u'A',
                              [(131,datetime(2008,3,19,8,27,39)),
                               (132,datetime(2008,3,19,8,28,35)),
                               (200,datetime(2008,3,19,8,29,35)),
                               (132,datetime(2008,3,19,8,30,0)),
                               ],
                              card_start_time = datetime(2008,3,19,8,25,50),
                              card_finish_time = datetime(2008,3,19,8,31,23),
                              store = self._store
                              ))
        self._runs[1].complete = True

        # normal run, punching additional sistation not connected to any control (133)
        # and additional control (134)
        self._runs.append(Run(768765,
                              u'A',
                              [ (131,datetime(2008,3,19,8,33,39)),
                                (132,datetime(2008,3,19,8,34,35)),
                                (133,datetime(2008,3,19,8,34,50)),
                                (200,datetime(2008,3,19,8,35,35)),
                                (134,datetime(2008,3,19,8,35,50)),
                                (132,datetime(2008,3,19,8,36,0)),
                                 ],
                              card_start_time = datetime(2008,3,19,8,31,25),
                              card_finish_time = datetime(2008,3,19,8,36,25),
                              store = self._store
                              ))
        self._runs[2].complete = True

        # punch on control 131 missing
        self._runs.append(Run(113456,
                              u'A',
                              [ (132,datetime(2008,3,19,8,33,39)),
                                (200,datetime(2008,3,19,8,35,35)),
                                (132,datetime(2008,3,19,8,36,0)),
                                ],
                              card_start_time = datetime(2008,3,19,8,31,25),
                              card_finish_time = datetime(2008,3,19,8,36,25),
                              store = self._store
                              ))
        self._runs[3].complete = True

        # This run ends after run 0 but before the first punch of run 1
        self._runs.append(Run(56789,
                              u'A',
                              [(131,datetime(2008,3,19,8,22,39)),
                               (132,datetime(2008,3,19,8,23,35)),
                               (201,datetime(2008,3,19,8,24,35)),
                               (132,datetime(2008,3,19,8,25,0)),
                               ],
                              card_start_time = datetime(2008,3,19,8,20,32),
                              card_finish_time = datetime(2008,3,19,8,25,40),
                              store = self._store
                              ))
        self._runs[4].complete = True

        # empty run
        self._runs.append(Run(12345, u'A', [], store = self._store))
        self._runs[5].complete = True

        # run without runner and course
        self._runs.append(Run(SICard(9999), 
                              None, 
                              [(131,datetime(2008,3,19,8,22,39)),
                               (132,datetime(2008,3,19,8,23,35)),
                               (201,datetime(2008,3,19,8,24,35)),
                               (132,datetime(2008,3,19,8,25,0)),
                               ],
                              card_start_time = datetime(2008,3,19,8,20,32),
                              card_finish_time = datetime(2008,3,19,8,25,40),
                              store = self._store
                              ))
        self._runs[6].complete = True

        # runs for RoundCountScoreing tests, sistation 200 and 201 are at the 
        # same control!

        # course with 2 controls, 3 rounds
        self._runs.append(Run(SICard(10),
                              None,
                              [(131, datetime(2008,3,19,8,22,29)),
                               (200, datetime(2008,3,19,8,23,30)),
                               (131, datetime(2008,3,19,8,24,29)),
                               (201, datetime(2008,3,19,8,25,30)),
                               (131, datetime(2008,3,19,8,25,50)),
                               (200, datetime(2008,3,19,8,26,30)),
                               (131, datetime(2008,3,19,8,27,29))],
                              store = self._store
                              ))
        self._runs[7].complete = True

        # course with 1 control, 3 rounds, time between punch 2 and 3 is < mindiff
        self._runs.append(Run(SICard(11),
                              None,
                              [(200, datetime(2008,3,19,8,22,29)),
                               (201, datetime(2008,3,19,8,24,29)),
                               (200, datetime(2008,3,19,8,24,39)),
                               (200, datetime(2008,3,19,8,27,29))],
                              store = self._store
                              ))
        self._runs[8].complete = True

        # course with 2 controls, 2 rounds, control 200 not punched one time
        self._runs.append(Run(SICard(12),
                              None,
                              [(131, datetime(2008,3,19,8,22,29)),
                               (200, datetime(2008,3,19,8,23,30)),
                               (131, datetime(2008,3,19,8,24,29)),
                               (131, datetime(2008,3,19,8,23,30)),
                               (131, datetime(2008,3,19,8,25,29)),
                               (201, datetime(2008,3,19,8,26,30)),
                               (131, datetime(2008,3,19,8,27,29))],
                              store = self._store
                              ))
        self._runs[9].complete = True

    def tearDown(self):
        # Clean up Database
        self._store.rollback()
        

class EventTest(unittest.TestCase):
    """Test class which tests the ranking for a whole event against known reference data."""


    def import_sql(self, fname):

        # import event data
        check_call(['psql', 'bosco_test'], stdin=open(fname), stderr=STDOUT,
                   stdout=open('/dev/null', 'w'))

    def import_refdata(self, fname):
        # import reference data
        self.ref_ranking = load(open(fname))

    def check_result(self, result, reference, ranking, index):
        for key in ['item', 'scoreing', 'validation', 'rank']:
            self.assertEquals(result[key], reference[key],
                              ('Ranking error in ranking %s on index %s for value %s: %s != %s' %
                               (ranking, index, key, result[key], reference[key])))

    def tearDown(self):
        self.store.rollback()
        self.import_sql(join(dirname(__file__), '../../docs/bosco_db.sql'))
        
    def doTestRanking(self):
        """Test the correct ranking of all courses and runs."""

        for key, ranking in self.event.list_rankings():

            print "Computing and testing ranking for %s..." % key,
            sys.stdout.flush()
            ranking_list = list(ranking)
            for r in ranking_list:
                # replace item object by it's id
                r['item'] = r['item'].id

            if type(ranking.rankable) == Course:
                for r in ranking_list:
                    # replace punch and control objects in punchlist by their ids
                    r['validation']['punchlist'] = [(p[0], p[1].id)
                                                    for p in
                                                    r['validation']['punchlist']]


            # check correctness rank by rank
            ref_ranking = self.ref_ranking[key]
            for i,r in enumerate(ranking_list):
                if i < len(ref_ranking)-1 and ref_ranking[i]['rank'] == ref_ranking[i+1]['rank']:
                    try:
                        self.check_result(r, ref_ranking[i], key, i)
                    except AssertionError:
                        # also check next reference result
                        self.check_result(r, ref_ranking[i+1], key, '%s (=%s)' % (i, i+1))
                elif i > 0 and ref_ranking[i]['rank'] == ref_ranking[i-1]['rank']:
                    try:
                        self.check_result(r, ref_ranking[i], key, i)
                    except AssertionError:
                        # also check previous reference result
                        self.check_result(r, ref_ranking[i-1], key, '%s (=%s)' % (i, i-1))
                else:
                    self.check_result(r, ref_ranking[i], key, i)
                    
            print 'done.'
