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

import pytest

from storm.locals import *
from storm.exceptions import IntegrityError

from bosco.runner import Runner
from bosco.runner import RunnerException
from bosco.runner import SICard

def test_store_add(store):
    """
    Test that a runner is added to the store if a store is given to the
    constructor.
    """
    r = Runner('Bernasconi', 'Maria')
    assert Store.of(r) is None

    store.add(r)
    assert Store.of(r) == store

def test_double_sicard(store):
    """
    Test that creating two SICard objects with the same id raises an error.
    """

    r1 = store.add(Runner('Hans', 'Muster', SICard(987655)))
    r2 = store.add(Runner('Bernasconi', 'Maria', SICard(987655)))
    with pytest.raises(IntegrityError):
        store.flush()

def test_multiple_sicards(store):
    """
    Runners can have multiple SI-cards.
    """

    s1 = SICard(987655)
    r = store.add(Runner('Hans', 'Muster', s1))
    s2 = SICard(765444)
    r.sicards.add(s2)
    assert s1 in r.sicards and s2 in r.sicards

def test_reassign_fails(store):
    """
    Test that reassign an already assign SICard fails.
    """

    si = SICard(987655)
    r1 = store.add(Runner('Hans', 'Muster', si))
    r2 = store.add(Runner('Bernasconi', 'Maria', SICard(765444)))
    store.flush()
    with pytest.raises(RunnerException):
        r2.sicards.add(si)

def test_unassign_assign(store):
    """
    First unassigning an SI-card and the assigning to another runner
    should work.
    """
    si = SICard(987655)
    r1 = store.add(Runner('Hans', 'Muster', si))
    r2 = store.add(Runner('Bernasconi', 'Maria', SICard(765444)))
    r1.sicards.remove(si)
    try:
        r2.sicards.add(si)
        store.flush()
    except RunnerException:
        self.fail("RunnerException raised although SI-card reassignment should "
                  "work.")
    assert si in r2.sicards

def test_reassig_same(store):
    """
    Test that reassigning an SI-card to the same runner it is already assigned
    works.
    """
    si = SICard(987655)
    r = store.add(Runner('Hans', 'Muster', si))
    try:
        r.sicards.add(si)
        store.flush()
    except RunnerException:
        self.fail("RunnerException raised although SI-card reassignment should "
                  "work.")
    assert si in r.sicards
