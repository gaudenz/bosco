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

class Runner(AbstractRunner, Storm):
    __storm_table__ = 'runner'

    id = Int(primary=True)
    number = Unicode()
    given_name = Unicode()
    surname = Unicode()
    dateofbirth = Date()
    sex = RawStr()
    _nation_id = Int(name='nation')
    nation = Reference(_nation_id, 'Country.id')
    solvnr = Unicode()
    startblock = Int()
    starttime = Date()
    _category_id = Int(name='category')
    category = Reference(_category_id, 'Category.id')
    _club_id = Int(name='club')
    club = Reference(_club_id, 'Club.id')
    address1 = Unicode()
    address2 = Unicode()
    zipcode = Unicode()
    city = Unicode()
    _address_country_id = Int(name='address_country')
    address_country = Reference(_address_country_id, 'Country.id')
    email = Unicode()
    startfee = Int()
    paid = Bool()
    preferred_category = Unicode()
    doping_declaration = Bool()
    comment = Unicode()
    _team_id = Int(name='team')
    team = Reference(_team_id, 'Team.id')
    sicards = ReferenceSet(id, 'SICard._runner_id')

    def __init__(self, surname=u'', given_name=u'', sicard = None, category = None, number = None,
                 dateofbirth=None, sex=None, nation=None, solvnr=None, startblock=None, 
                 starttime=None, club=None, address1=None, address2=None, zipcode=None, 
                 city=None, address_country=None, email=None, startfee=None, paid=None, 
                 preferred_category=None, doping_declaration=None, comment=None,
                 ):
        self.surname = surname
        self.given_name = given_name
        if sicard is not None:
            self.sicards.add(sicard)
        self.category = category
        self.number = number
        self.dateofbirth = dateofbirth
        self.sex = sex
        self.nation = nation
        self.solvnr = solvnr
        self.startblock = startblock
        self.starttime = starttime
        self.club = club
        self.address1 = address1
        self.address2 = address2
        self.zipcode = zipcode
        self.city = city
        self.address_country = address_country
        self.email = email
        self.startfee = startfee
        self.paid = paid
        self.preferred_category = preferred_category
        self.doping_declaration = doping_declaration
        self.comment = comment
        
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return (u'%s %s' % (self.given_name, self.surname))

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
                raise RunnerException(u'%s runs for runner %s (%s)' % (len(runs), self, self.number))
        else:
            raise RunnerException(u'No run found for runner %s (%s)' % (self, self.number))
    run = property(_get_run)
        
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

    def __str__(self):
        return unicode(self).encode('utf-8')
    
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


def sicard_runner_validator(sicard, attribute, value):
    """This validator avoids that SI-cards are reassigned from one
    runner to another. If you really want to reassign an SI-card, first
    remove it from the first runner and then assign it to the other."""

    if sicard._runner_id is None or sicard._runner_id == value or value is None:
        return value

    raise RunnerException("SI-Card %s is already assigned to runner %s %s (%s)" %
                          (sicard.id, sicard.runner.given_name, sicard.runner.surname,
                           sicard.runner.number)
                          )

class SICard(Storm):
    __storm_table__ = 'sicard'

    id = Int(primary=True)
    _runner_id = Int(name='runner',
                     validator = sicard_runner_validator)
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

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.name

    def _get_members(self):
        l = list(self.runners)
        l.extend(list(self.teams))
        return l
    members = property(_get_members)

class Country(Storm):
    __storm_table__ = 'country'

    id = Int(primary=True)
    name = Unicode()
    code2 = Unicode()
    code3 = Unicode()
    runners = ReferenceSet(id, 'Runner._nation_id')

    def __init__(self, code3, code2, name=None):
        self.name = name
        self.code3 = code3
        self.code2 = code2

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.code3


class Club(Storm):
    __storm_table__ = 'club'

    id = Int(primary=True)
    name = Unicode()
    runners = ReferenceSet(id, 'Runner._club_id')

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.name


class RunnerException(Exception):
    pass
