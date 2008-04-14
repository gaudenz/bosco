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

"""
Tests for runner classes
"""

import unittest

from storm.locals import *

from runner import Runner, RunnerException, SICard

class RunnerTest(unittest.TestCase):

    # Create store as class variable so that every test uses the same
    # database connection
    _store = Store(create_database('postgres:24h_test'))

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

    def testStoreAdd(self):
        """
        Test that a runner is added to the store if a store is given to the
        constructor.
        """
        r1 = Runner(u'Muster', u'Hans', store = self._store)
        self.assertEquals(Store.of(r1), self._store)

        r2 = Runner(u'Bernasconi', u'Maria')
        self.assertEquals(Store.of(r2), None)
        self._store.add(r2)
        self.assertEquals(Store.of(r2), self._store)

    def testDoubleSICard(self):
        """
        Test that assigning an SI-Card to two runners raises an exception.
        """

        r1 = Runner(u'Muster', u'Hans', 987655, store = self._store)
        self.assertRaises(RunnerException, Runner, u'Bernasconi', u'Maria', 987655, store = self._store)
        r2 = Runner(u'Bernasconi', u'Maria', 765444, store = self._store)
        self.assertRaises(RunnerException, r2.add_sicard, 987655)
        si = self._store.get(SICard, 987655)
        self.assertRaises(RunnerException, r2.add_sicard, si)
