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
from copy import copy

from base import MyStorm
from ranking import Rankable, RankableItem

class AbstractRunner(object, RankableItem):
    """Base class for all runner like classes (runners, teams). This
    class defines the interface for all objects that work with any kind
    of runners or teams."""

    name = None
    number = None
    official = None
    sicards = None

class Runner(AbstractRunner, MyStorm):
    __storm_table__ = 'runner'

    id = Int(primary=True)
    number = Unicode()
    given_name = Unicode()
    surname = Unicode()
    dateofbirth = Date()
    sex = RawStr()
    startblock = Int()
    starttime = Date()
    _category_id = Int(name='category')
    category = Reference(_category_id, 'Category.id')
    club = Int()
    address1 = Unicode()
    address2 = Unicode()
    zipcode = Unicode()
    city = Unicode()
    email = Unicode()
    solvnr = Unicode()
    startfee = Int()
    paid = Bool()
    comment = Unicode()
    _team_id = Int(name='team')
    team = Reference(_team_id, 'Team.id')
    sicards = ReferenceSet(id, 'SICard._runner_id')

    def __init__(self, sname, gname, sicard = None, category = None, number = None,
                 store = None):
        self.surname = sname
        self.given_name = gname
        self.number = number
        if store is not None:
            self._store = store
        if sicard is not None:
            self.add_sicard(sicard)
        if category is not None:
            self.set_category(category)
        
    def __str__(self):
        return '%s %s' % (self.given_name, self.surname)

    def _get_run(self): 
        runs = []
        for si in self.sicards:
            for r in si.runs:
                runs.append(r)
                
        if len(runs) == 1:
            return runs[0]
        elif len(runs) > 1:
            # search for complete runs
            complete_runs = [ r for r in runs if r.complete == True ]
            if len(complete_runs) == 1:
                # if there is only one complete run, return this run
                return complete_runs[0]
            else:
                raise RunnerException('%s runs for runner %s' % (len(runs), self))
        else:
            raise RunnerException('No run found for runner %s' % self)
    run = property(_get_run)


    def add_sicard(self, cardnr):
        """Adds an SI-Card by it's id. If the card does not exist it is created on the fly.
        If the card is already assigned to another runner an exception is raised.
        
        @param cardnr: sicard id
        @type cardnr:  int or sicard object
        """
        if type(cardnr) == int:
            sicard = self._store.get(SICard, cardnr)
            if sicard is None:
                sicard = SICard(cardnr)
        else:
            sicard = cardnr

        if sicard.runner == self or sicard.runner == None:
            return self.sicards.add(sicard)
        
        raise RunnerException("SI-Card %s already assigned to runner %s" %
                              (cardnr, "%s %s (%s)" %
                                       (sicard.runner.given_name,
                                        sicard.runner.surname,
                                        sicard.runner.number)
                               )
                              )

    def set_category(self, category_name):
        """Sets the category for this runner. Categories are NOT created on the fly!"""
        if type(category_name) == unicode:
            category = self._store.find(Category, Category.name == category_name).one()
            if category is None:
                raise RunnerException("Category '%s' not found." % category_name)
        else:
            category = category_name
        self.category = category
        
    def start(self):
        return self._get_run().start()

    def finish(self):
        return self._get_run().finish()
        
class Team(AbstractRunner, Storm):
    __storm_table__ = 'team'
    
    id = Int(primary=True)
    number = Unicode()
    name = Unicode()
    official = Bool()
    override = Int()
    _responsible_id = Int(name='responsible')
    responsible = Reference(_responsible_id, 'Runner.id')
    _category_id = Int(name='category')
    category = Reference(_category_id, 'Category.id')
    members = ReferenceSet(id, 'Runner._team_id')

    def __init__(self, number, name, category, responsible = None, official = True):
        self.number = number
        self.name = name
        self.category = category
        self.official = official
        self.responsible = responsible

    def __unicode__(self):
        return self.name

    def _get_runs(self):
        runs = []
        # import this here to avoid a circular import
        from run import Run
        for m in self.members:
            for si in m.sicards:
                runs.extend(list(si.runs))
        return runs
    runs = property(_get_runs)


class SICard(Storm):
    __storm_table__ = 'sicard'

    id = Int(primary=True)
    _runner_id = Int(name='runner')
    runner = Reference(_runner_id, 'Runner.id')
    runs = ReferenceSet(id, 'Run._sicard_id')

    def __init__(self, nr):
        self.id = nr

class Category(Storm, Rankable):
    __storm_table__ = 'category'

    id = Int(primary=True)
    name = Unicode()
    runners = ReferenceSet(id, 'Runner._category_id')
    teams = ReferenceSet(id, 'Team._category_id')

    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return self.name

    def _get_members(self):
        l = list(self.runners)
        l.extend(list(self.teams))
        return l
    members = property(_get_members)
    
class RunnerException(Exception):
    pass
