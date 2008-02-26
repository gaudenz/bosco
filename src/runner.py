#/usr/bin/env python
#    runner.py - Runners, Teams, SI-Cards, ...
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

class Runner(Storm):
    __storm_table__ = 'runner'

    id = Int(primary=True)
    number = Unicode()
    given_name = Unicode()
    surname = Unicode()
    dateofbirth = Date()
    sex = Unicode()
    startblock = Int()
    starttime = Date()
    category_id = Int()
    category = Reference(category_id, 'Category.id')
    club_id = Int()
    address1 = Unicode()
    address2 = Unicode()
    zipcode = Unicode()
    city = Unicode()
    email = Unicode()
    solvnr = Unicode()
    startfee = Int()
    paid = Bool()
    comment = Unicode()
    team_id = Int()
    team = Reference(team_id, 'Team.id')
    sicards = ReferenceSet(id, 'SICard.runner_id')

    def __init__(self, sname, gname):
        self.surname = sname
        self.given_name = gname
        
class Team(Storm):
    __storm_table__ = 'team'
    
    id = Int(primary=True)
    number = Unicode()
    name = Unicode()
    official = Bool()
    responsible_id = Int()
    responsible = Reference(responsible_id, 'Runner.id')
    category_id = Int()
    category = Reference(category_id, 'Category.id')
    members = ReferenceSet(id, 'Runner.team_id')

    def __init__(self, number, name, responsible, category, official = True):
        self.number = number
        self.name = name
        self.category = category
        self.official = official
        self.responsible = responsible

class SICard(Storm):
    __storm_table__ = 'sicard'

    id = Int(primary=True)
    runner_id = Int()
    runner = Reference(runner_id, 'Runner.id')
    runs = ReferenceSet(id, 'Run.sicard_id')

    def __init__(self, nr):
        self.id = nr

class Category(Storm):
    __storm_table__ = 'category'

    id = Int(primary=True)
    name = Unicode()
    runners = ReferenceSet(id, 'Runner.category_id')
    teams = ReferenceSet(id, 'Team.category_id')

    def __init__(self, name):
        self.name = name
