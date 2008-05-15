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
Test the correct ranking of the 24h Relay test event
"""

import unittest

from storm.locals import *
from datetime import datetime, timedelta

from ranking import Cache
from runner import Category
from event import Relay24hEvent

from tests.eventtest import EventTest

class Relay24h2008Test(EventTest):

    def setUp(self):

        self.import_sql('tests/24h_testevent.sql')
        self.import_refdata('tests/24h_testevent.pck')
        
        store = Store(create_database('postgres:24h_test'))
        cat24h = store.find(Category, Category.name == u'24h').one()
        cat12h = store.find(Category, Category.name == u'12h').one()

        # Set up event object
        self.event = Relay24hEvent(starttime_24h = datetime(2008,4,30,21,55),
                              starttime_12h = datetime(2008,4,30,22,50),
                              speed = 1.5,
                              extra_rankings = [('24h_lkm',
                                                 {'obj':cat24h,
                                                  'scoreing_args':{'method':'lkm'}
                                                  }
                                                 ),
                                                ('24h_speed',
                                                 {'obj':cat24h,
                                                  'scoreing_args':{'method':'speed'},
                                                  'reverse':True,
                                                  }
                                                 ),
                                                ('12h_lkm',
                                                 {'obj':cat12h,
                                                  'scoreing_args':{'method':'lkm'}
                                                  }
                                                 ),
                                                ('12h_speed',
                                                 {'obj':cat12h,
                                                  'scoreing_args':{'method':'speed'},
                                                  'reverse':True
                                                  }
                                                 ),
                                                ('24h_start',
                                                 {'obj':cat24h,
                                                  'scoreing_args':{'blocks':'start'},
                                                  'validation_args':{'blocks':'start'}
                                                  }
                                                 ),
                                                ('24h_night',
                                                 {'obj':cat24h,
                                                  'scoreing_args':{'blocks':'night'},
                                                  'validation_args':{'blocks':'night'}
                                                  }
                                                 ),
                                                ('24h_day',
                                                 {'obj':cat24h,
                                                  'scoreing_args':{'blocks':'day'},
                                                  'validation_args':{'blocks':'day'}
                                                  }
                                                 ),
                                                ('12h_start',
                                                 {'obj':cat12h,
                                                  'scoreing_args':{'blocks':'start'},
                                                  'validation_args':{'blocks':'start'}
                                                  }
                                                 ),
                                                ('12h_day',
                                                 {'obj':cat12h,
                                                  'scoreing_args':{'blocks':'day'},
                                                  'validation_args':{'blocks':'day'}
                                                  }
                                                 ),
                                                ],
                              duration_24h = timedelta(hours=2, minutes = 6),
                              duration_12h = timedelta(hours=1, minutes = 3),
                              cache = Cache(), store = store)

    def testRanking(self):
        """Test the correct ranking of all courses and runs."""
        self.doTestRanking()
