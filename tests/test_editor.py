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
from storm.locals import *

@pytest.mark.parametrize('what', ['id',
                                  'course',
                                  'sicard.id',
                                  'sicard.runner',
                                  'sicard.runner.team.number',
                                  'sicard.runner.team.name',
                                  'sicard.runner.category',
                                  'sicard.runner.team.category',
                                  ])
def test_runfinder(testevent, what):
    """Test that a RunFinder finds the right run"""
    def dot_access(item, path):
        if not '.' in path:
            return getattr(item, path, None)
        else:
            attr, remaining = path.split('.', 1)
            return dot_access(getattr(item, attr, None), remaining)

    for r in testevent._runs:
        searchterm = dot_access(r, what)
        if not searchterm:
            continue

        testevent._run_finder.set_search_term(str(searchterm))
        assert (testevent._run_finder._format_result(r)
                in list(testevent._run_finder.get_results()))

def test_runfinder_sicard(testevent):
    """Search in sicards."""

    testevent._run_finder.set_search_term('abc')
    assert [] == list(testevent._run_finder.get_results())

    testevent._run_finder.set_search_term('xyz')
    assert [] == list(testevent._run_finder.get_results())

    testevent._run_finder.set_search_term(0)
    assert [] == list(testevent._run_finder.get_results())

    testevent._run_finder.set_search_term([])
    assert [] == list(testevent._run_finder.get_results())

def test_runfinder_runner(testevent):
    """Search in runners."""

    # Search for full given name
    hanses = [testevent._run_tuple(0),
              testevent._run_tuple(2),
              ]
    testevent._run_finder.set_search_term("Hans")
    assert hanses == list(testevent._run_finder.get_results())

    testevent._run_finder.set_search_term("hans")
    assert hanses == list(testevent._run_finder.get_results())

    # Search for number
    testevent._run_finder.set_search_term("102")
    assert ([(testevent._runs[1].id,
              "A",
              "unknown",
              "102",
              "Trudi Gerster",
              "The best team ever",
              "D135",
              )]
            == list(testevent._run_finder.get_results()))

    # Search for runner by given and surname
    result = [(testevent._runs[4].id,
               "A",
               "unknown",
               "unknown",
               "Dada Gugus",
               "unknown",
               "HAM",
               )]
    testevent._run_finder.set_search_term("Gugus Dada")
    assert result == list(testevent._run_finder.get_results())

    testevent._run_finder.set_search_term("Dada Gugus")
    assert result == list(testevent._run_finder.get_results())

    testevent._run_finder.set_search_term("Da Gu")
    assert result == list(testevent._run_finder.get_results())

def test_runfinder_run_without_runner(testevent):
    """Test that runs without a runner and a course"""
    testevent._run_finder.set_search_term(9999)
    assert ([testevent._run_tuple(6)]
            == list(testevent._run_finder.get_results()))

@pytest.mark.parametrize('what', ['name', 'number', 'solvnr', 'team'])
def test_runnerfinder(testevent, what):
    """Test that a RunnerFinder finds the right runner"""
    for run in testevent._runs:
        if not run.sicard.runner:
            continue
        r = run.sicard.runner

        searchterm = getattr(r, what)
        if not searchterm:
            continue

        testevent._runner_finder.set_search_term(str(searchterm))
        assert (testevent._runner_finder._format_result(r)
                in list(testevent._runner_finder.get_results()))

def test_runnerfinder_by_sicard(testevent):
    """Test that a RunnerFinder finds a runner by SICard number"""
    for run in testevent._runs:
        if not run.sicard.runner:
            continue
        r = run.sicard.runner

        for sicard in r.sicards:
            testevent._runner_finder.set_search_term(str(sicard.id))
            assert (testevent._runner_finder._format_result(r)
                    in list(testevent._runner_finder.get_results()))

@pytest.mark.parametrize('what', ['name', 'number', 'category'])
def test_teamfinder(testevent, what):
    """Test that a TeamFinder finds the right team"""
    t = testevent._team
    testevent._team_finder.set_search_term(str(getattr(t, what)))
    assert (testevent._team_finder._format_result(t)
             in list(testevent._team_finder.get_results()))
