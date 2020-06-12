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

from os.path import join, dirname

from storm.locals import *
from datetime import datetime, timedelta

from bosco.runner import Category, Team, Runner
from bosco.importer import Team24hImporter, OCADXMLCourseImporter, SIRunImporter
from bosco.ranking import Validator, Relay24hScore, Cache
from bosco.event import Relay24hEvent

class Relay24hTest(unittest.TestCase):

    # Create store as class variable so that every test uses the same
    # database connection
    _store = Store(create_database('postgres:bosco_test'))

    def setUp(self):

        # import runners from testfile
        importer = Team24hImporter(join(dirname(__file__), 'import_24h_team.csv'), 'iso-8859-1')
        importer.import_data(self._store)
        
        # import courses from testfile
        importer = OCADXMLCourseImporter(join(dirname(__file__), 'import_24h_course.xml'),
                                         finish = True,
                                         start = False)
        importer.import_data(self._store)

        # import sample runs
        importer = SIRunImporter(join(dirname(__file__), 'import_24h_run.csv'))
        importer.import_data(self._store)

        self._cache = Cache()
        self._event = Relay24hEvent(starttime_24h = datetime(2008, 4, 14, 19, 0),
                                    starttime_12h = datetime(2008, 4, 15, 7, 0),
                                    speed = 5,
                                    header = {},
                                    duration_24h = timedelta(hours=4, minutes=30),
                                    duration_12h = timedelta(hours=4, minutes=30),
                                    cache = self._cache,
                                    store = self._store)

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
        valid = self._event.validate(self.getTeam('119'))

        self.assertEqual(valid['status'],
                          Validator.OK)
        self.assertEqual(self._event.validate(self.getTeam('121'))['status'],
                          Validator.OK)
        self.assertEqual(self._event.validate(self.getTeam('103'))['status'],
                          Validator.OK)
        self.assertEqual(self._event.validate(self.getTeam('104'))['status'],
                          Validator.DISQUALIFIED)
        self.assertEqual(self._event.validate(self.getTeam('105'))['status'],
                          Validator.DISQUALIFIED)
        self.assertEqual(self._event.validate(self.getTeam('106'))['status'],
                          Validator.DISQUALIFIED)
        self.assertEqual(self._event.validate(self.getTeam('109'))['status'],
                          Validator.OK)

        self.getTeam('105').override = Validator.OK
        # notify cache that this team has changed
        self._cache.update(self.getTeam('105'))
        self.assertEqual(self._event.validate(self.getTeam('105'))['status'],
                          Validator.OK)

        self.getTeam('119').override = Validator.DISQUALIFIED
        self._cache.update(self.getTeam('119'))
        self.assertEqual(self._event.validate(self.getTeam('119'))['status'],
                          Validator.DISQUALIFIED)
        
        self.assertEqual(self._event.score(self.getTeam('119'))['score'],
                          Relay24hScore(41, timedelta(minutes=41*6)))        
        self.assertEqual(self._event.score(self.getTeam('121'))['score'],
                          Relay24hScore(40, timedelta(minutes=40*6)))
        self.assertEqual(self._event.score(self.getTeam('103'))['score'],
                          Relay24hScore(38, timedelta(minutes=41*6)))
        self.assertEqual(self._event.score(self.getTeam('109'))['score'],
                          Relay24hScore(40, timedelta(minutes=40*6)))
