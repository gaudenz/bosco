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
from storm.exceptions import IntegrityError

from bosco.runner import Runner, RunnerException, SICard

class RunnerTest(unittest.TestCase):

    # Create store as class variable so that every test uses the same
    # database connection
    _store = Store(create_database('postgres:bosco_test'))

    def tearDown(self):
        # Clean up Database
        self._store.rollback()

    def testStoreAdd(self):
        """
        Test that a runner is added to the store if a store is given to the
        constructor.
        """
        r = Runner(u'Bernasconi', u'Maria')
        self.assertEquals(Store.of(r), None)
        self._store.add(r)
        self.assertEquals(Store.of(r), self._store)

    def testDoubleSICard(self):
        """
        Test that creating two SICard objects with the same id raises an error.
        """

        r1 = self._store.add(Runner(u'Hans', u'Muster', SICard(987655)))
        r2 = self._store.add(Runner(u'Bernasconi', u'Maria', SICard(987655)))
        self.assertRaises(IntegrityError, self._store.flush)

    def testMultipleSICards(self):
        """
        Runners can have multiple SI-cards.
        """
        
        s1 = SICard(987655)
        r = self._store.add(Runner(u'Hans', u'Muster', s1))
        s2 = SICard(765444)
        r.sicards.add(s2)
        self.failUnless(s1 in r.sicards and s2 in r.sicards)

    def testReassignFails(self):
        """
        Test that reassign an already assign SICard fails.
        """

        si = SICard(987655)
        r1 = self._store.add(Runner(u'Hans', u'Muster', si))
        r2 = self._store.add(Runner(u'Bernasconi', u'Maria', SICard(765444)))
        self._store.flush()
        self.assertRaises(RunnerException, r2.sicards.add, si)

    def testUnassignAssign(self):
        """
        First unassigning an SI-card and the assigning to another runner
        should work.
        """
        si = SICard(987655)
        r1 = self._store.add(Runner(u'Hans', u'Muster', si))
        r2 = self._store.add(Runner(u'Bernasconi', u'Maria', SICard(765444)))
        r1.sicards.remove(si)
        try:
            r2.sicards.add(si)
            self._store.flush()
        except RunnerException:
            self.fail("RunnerException raised although SI-card reassignment should "
                      "work.")
        self.failUnless(si in r2.sicards)

    def testReassigSame(self):
        """
        Test that reassigning an SI-card to the same runner it is already assigned
        works.
        """
        si = SICard(987655)
        r = self._store.add(Runner(u'Hans', u'Muster', si))
        try:
            r.sicards.add(si)
            self._store.flush()
        except RunnerException:
            self.fail("RunnerException raised although SI-card reassignment should "
                      "work.")
        self.failUnless(si in r.sicards)

        
