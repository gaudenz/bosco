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

from tests import BoscoTest

from editor import RunFinder

class RunFinderTest(BoscoTest):

    def setUp(self):
        super(RunFinderTest, self).setUp()
        self._finder = RunFinder(self._store)

    def test_run(self):
        """Search in runs."""
        self._finder.set_search_domain('run')
        for r in self._runs:
            self._finder.set_search_term(r.id)
            self.assertEquals([self._run_tuple(self._runs.index(r))], 
                              self._finder.get_results()
                              )

    def test_sicard(self):
        """Search in sicards."""
        self._finder.set_search_domain('sicard')

        for r in self._runs:
            self._finder.set_search_term(r.sicard.id)
            self.assertEquals([self._run_tuple(self._runs.index(r))], 
                              self._finder.get_results()
                              )

        self._finder.set_search_term('abc')
        self.assertEquals([], self._finder.get_results())

        self._finder.set_search_term(u'xyz')
        self.assertEquals([], self._finder.get_results())

        self._finder.set_search_term(0)
        self.assertEquals([], self._finder.get_results())

        self._finder.set_search_term([])
        self.assertEquals([], self._finder.get_results())

    def test_runner(self):
        """Search in runners."""
        self._finder.set_search_domain('runner')

        # Search for full given name
        hanses = [self._run_tuple(0),
                  self._run_tuple(2),
                  ]
        self._finder.set_search_term("Hans")
        self.assertEquals(hanses,
                          self._finder.get_results()
                          )
        self._finder.set_search_term("hans")
        self.assertEquals(hanses,
                          self._finder.get_results()
                          )

        # Search for number
        self._finder.set_search_term("102")
        self.assertEquals([(self._runs[1].id,
                            "A",
                            "unknown",
                            "102",
                            "Trudi Gerster",
                            "The best team ever",
                            "D135",
                            )],
                          self._finder.get_results()
                          )

        # Search for runner by given and surname
        result = [(self._runs[4].id,
                   "A",
                   "unknown",
                   "unknown",
                   "Dada Gugus",
                   "unknown",
                   "HAM",
                   )]
        self._finder.set_search_term("Gugus Dada")
        self.assertEquals(result,
                          self._finder.get_results()
                          )
        self._finder.set_search_term("Dada Gugus")
        self.assertEquals(result,
                          self._finder.get_results()
                          )
        self._finder.set_search_term("Da Gu")
        self.assertEquals(result, self._finder.get_results())

    def test_team(self):
        """Search in teams."""
        self._finder.set_search_domain('team')

        team_runs = [ self._run_tuple(i) 
                      for i in range(3)
                      ]

        self._finder.set_search_term('1')
        self.assertEquals(team_runs, self._finder.get_results())
        self._finder.set_search_term('best')
        self.assertEquals(team_runs, self._finder.get_results())

    def test_category(self):
        """Search in categories."""
        self._finder.set_search_domain('category')
        HAM = [self._run_tuple(i)
               for i in range(6)]
        self._finder.set_search_term('HAM')
        self.assertEquals(HAM, self._finder.get_results())
        self._finder.set_search_term('HA')
        self.assertEquals([], self._finder.get_results())
        self._finder.set_search_term('D135')
        self.assertEquals([self._run_tuple(i) for i in range(3)],
                          self._finder.get_results())

    def test_course(self):
        """Search in courses."""
        self._finder.set_search_domain('course')
        self._finder.set_search_term('A')
        self.assertEquals([self._run_tuple(i) for i in range(6)],
                          self._finder.get_results())

    def _run_tuple(self, run_id):
        """
        @param run_id Index of the run in self._runs
        @return       Tuple formatted like RunFinder.get_results()"""

        r = self._runs[run_id]
        number = r.sicard.runner.number
        team = r.sicard.runner.team
        runner = r.sicard.runner
        return (r.id,
                unicode(r.course.code),
                "unknown",
                number and unicode(number) or "unknown",
                unicode(runner),
                team and unicode(team) or "unknown",
                team and unicode(team.category) or unicode(runner.category))
