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

def test_run(testevent):
    """Search in runs."""
    testevent._finder.set_search_domain('run')
    for r in testevent._runs:
        testevent._finder.set_search_term(r.id)
        assert ([testevent._run_tuple(testevent._runs.index(r))]
                == testevent._finder.get_results())

def test_sicard(testevent):
    """Search in sicards."""
    testevent._finder.set_search_domain('sicard')

    for r in testevent._runs:
        testevent._finder.set_search_term(r.sicard.id)
        assert ([testevent._run_tuple(testevent._runs.index(r))]
                == testevent._finder.get_results())

    testevent._finder.set_search_term('abc')
    assert [] == testevent._finder.get_results()

    testevent._finder.set_search_term('xyz')
    assert [] == testevent._finder.get_results()

    testevent._finder.set_search_term(0)
    assert [] == testevent._finder.get_results()

    testevent._finder.set_search_term([])
    assert [] == testevent._finder.get_results()

def test_runner(testevent):
    """Search in runners."""
    testevent._finder.set_search_domain('runner')

    # Search for full given name
    hanses = [testevent._run_tuple(0),
              testevent._run_tuple(2),
              ]
    testevent._finder.set_search_term("Hans")
    assert hanses == testevent._finder.get_results()

    testevent._finder.set_search_term("hans")
    assert hanses == testevent._finder.get_results()

    # Search for number
    testevent._finder.set_search_term("102")
    assert ([(testevent._runs[1].id,
              "A",
              "unknown",
              "102",
              "Trudi Gerster",
              "The best team ever",
              "D135",
              )]
            == testevent._finder.get_results())

    # Search for runner by given and surname
    result = [(testevent._runs[4].id,
               "A",
               "unknown",
               "unknown",
               "Dada Gugus",
               "unknown",
               "HAM",
               )]
    testevent._finder.set_search_term("Gugus Dada")
    assert result == testevent._finder.get_results()

    testevent._finder.set_search_term("Dada Gugus")
    assert result == testevent._finder.get_results()

    testevent._finder.set_search_term("Da Gu")
    assert result == testevent._finder.get_results()

def test_team(testevent):
    """Search in teams."""
    testevent._finder.set_search_domain('team')

    team_runs = [ testevent._run_tuple(i)
                  for i in range(3)
                  ]

    testevent._finder.set_search_term('1')
    assert team_runs == testevent._finder.get_results()
    testevent._finder.set_search_term('best')
    assert team_runs == testevent._finder.get_results()

def test_category(testevent):
    """Search in categories."""
    testevent._finder.set_search_domain('category')
    HAM = [testevent._run_tuple(i)
           for i in range(6)]
    testevent._finder.set_search_term('HAM')
    assert HAM == testevent._finder.get_results()
    testevent._finder.set_search_term('HA')
    assert [] == testevent._finder.get_results()
    testevent._finder.set_search_term('D135')
    assert ([testevent._run_tuple(i) for i in range(3)]
            == testevent._finder.get_results())

def test_course(testevent):
    """Search in courses."""
    testevent._finder.set_search_domain('course')
    testevent._finder.set_search_term('A')
    assert ([testevent._run_tuple(i) for i in range(6)]
            == testevent._finder.get_results())

def test_run_without_runner(testevent):
    """Test that runs without a runner and a course"""
    testevent._finder.set_search_domain('sicard')
    testevent._finder.set_search_term(9999)
    assert ([testevent._run_tuple(6)]
            == testevent._finder.get_results())
