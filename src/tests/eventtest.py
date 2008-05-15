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

"""
Test the correct ranking of the 24h Relay Event 2008
"""

import unittest

from subprocess import check_call,STDOUT
from cPickle import load
import sys

from course import Course

class EventTest(unittest.TestCase):
    """Test class which tests the ranking for a whole event against known reference data."""


    def import_sql(self, fname):

        # import event data
        check_call(['psql', '24h_test'], stdin=open(fname), stderr=STDOUT,
                   stdout=open('/dev/null', 'w'))

    def import_refdata(self, fname):
        # import reference data
        self.ref_ranking = load(open(fname))

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
            for i,r in enumerate(ranking_list):
                self.assertEquals(r,self.ref_ranking[key][i],
                                  ('Ranking error in ranking %s on index %s: %s != %s' %
                                   (key, i, r, self.ref_ranking[key][i])))

            print 'done.'
