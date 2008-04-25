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
from ranking import Relay24hEventRanking, Validator, Relay24hScore, Cache

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

        self._cache = Cache()
        self._event_ranking = Relay24hEventRanking(datetime(2008,4,14,19,0),
                                                   datetime(2008,4,15,17,0),
                                                   5,
                                                   timedelta(hours=4, minutes=30),
                                                   timedelta(hours=4, minutes=30),
                                                   self._cache)

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
    
    def testRelay24h(self):
        self.assertEquals(self._event_ranking.validate(self.getTeam(u'019'))['status'],
                          Validator.OK)
        self.assertEquals(self._event_ranking.validate(self.getTeam(u'021'))['status'],
                          Validator.OK)
        self.assertEquals(self._event_ranking.validate(self.getTeam(u'003'))['status'],
                          Validator.OK)
        self.assertEquals(self._event_ranking.validate(self.getTeam(u'004'))['status'],
                          Validator.DISQUALIFIED)
        self.assertEquals(self._event_ranking.validate(self.getTeam(u'005'))['status'],
                          Validator.DISQUALIFIED)
#        self.assertEquals(self._event_ranking.validate(self.getTeam(u'006'))['status'],
#                          Validator.DISQUALIFIED)
        self.assertEquals(self._event_ranking.validate(self.getTeam(u'009'))['status'],
                          Validator.OK)

        self.getTeam(u'005').override = True
        # notify cache that this team has changed
        self._cache.update(self.getTeam(u'005'))
        self.assertEquals(self._event_ranking.validate(self.getTeam(u'005'))['status'],
                          Validator.OK)

        self.assertEquals(self._event_ranking.score(self.getTeam(u'019'))['score'],
                          Relay24hScore(41,timedelta(minutes=41*6)))        
        self.assertEquals(self._event_ranking.score(self.getTeam(u'021'))['score'],
                          Relay24hScore(40,timedelta(minutes=40*6)))
        self.assertEquals(self._event_ranking.score(self.getTeam(u'003'))['score'],
                          Relay24hScore(38,timedelta(minutes=41*6)))
        self.assertEquals(self._event_ranking.score(self.getTeam(u'009'))['score'],
                          Relay24hScore(40,timedelta(minutes=40*6)))
