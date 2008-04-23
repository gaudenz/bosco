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
Test specific to the 24h relay.
"""

import unittest

from storm.locals import *
from datetime import datetime, timedelta

from runner import Category, Team, Runner
from importer import Team24hImporter, OCADXMLCourseImporter, SIRunImporter
from ranking import ValidationStrategy, Relay24hScoreingStrategy, Relay24hScore, Cache

class Relay24hTest(unittest.TestCase):

    # Create store as class variable so that every test uses the same
    # database connection
    _store = Store(create_database('postgres:24h_test'))

    def setUp(self):

        # import runners from testfile
        importer = Team24hImporter('tests/import_24h_team.csv', 'iso-8859-1')
        importer.import_data(self._store)
        
        # import courses from testfile
        importer = OCADXMLCourseImporter('tests/import_24h_course.xml',
                                         finish = True,
                                         start = False)
        importer.import_data(self._store)

        # import sample runs
        importer = SIRunImporter('tests/import_24h_run.csv')
        importer.import_data(self._store)

        # commit to database
        self._store.commit()
        
    def tearDown(self):
        # Clean up Database
        self._store.execute('TRUNCATE course CASCADE')
        self._store.execute('TRUNCATE sistation CASCADE')
        self._store.execute('TRUNCATE control CASCADE')
        self._store.execute('TRUNCATE run CASCADE')
        self._store.execute('TRUNCATE punch CASCADE')
        self._store.execute('TRUNCATE sicard CASCADE')
        self._store.execute('TRUNCATE runner CASCADE')
        self._store.execute('TRUNCATE category CASCADE')
        self._store.commit()

    def getTeam(self, number):
        return self._store.find(Team, Team.number == number).one()
    
    def testRelay24hValidation(self):
        cache = Cache()
        validator = Relay24hScoreingStrategy(datetime(2008,4,14,19,0), 5,
                                             validation_cache = cache)
        self.assertEquals(validator.validate(self.getTeam(u'019')),
                          ValidationStrategy.OK)
        self.assertEquals(validator.validate(self.getTeam(u'021')),
                          ValidationStrategy.OK)
        self.assertEquals(validator.validate(self.getTeam(u'003')),
                          ValidationStrategy.OK)
        self.assertEquals(validator.validate(self.getTeam(u'004')),
                          ValidationStrategy.DISQUALIFIED)
        self.assertEquals(validator.validate(self.getTeam(u'005')),
                          ValidationStrategy.DISQUALIFIED)
#        self.assertEquals(validator.validate(self.getTeam(u'006')),
#                          ValidationStrategy.DISQUALIFIED)
        self.assertEquals(validator.validate(self.getTeam(u'009')),
                          ValidationStrategy.OK)

    def testRelay24hScoreing(self):
        cache = Cache()
        scoreing = Relay24hScoreingStrategy(datetime(2008,4,14,19,0), 5,
                                            duration = timedelta(hours=4, minutes=30),
                                            scoreing_cache = cache)
        score = scoreing.score(self.getTeam(u'019'))

        self.assertEquals(scoreing.score(self.getTeam(u'019')),
                          Relay24hScore(41,timedelta(minutes=41*6)))        
        self.assertEquals(scoreing.score(self.getTeam(u'021')),
                          Relay24hScore(40,timedelta(minutes=40*6)))
        self.assertEquals(scoreing.score(self.getTeam(u'003')),
                          Relay24hScore(38,timedelta(minutes=41*6)))
        self.assertEquals(scoreing.score(self.getTeam(u'009')),
                          Relay24hScore(40,timedelta(minutes=40*6)))
