#/usr/bin/env python
#    config.py - Local Configuration
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
from datetime import datetime, timedelta

from ranking import (ControlPunchtimeScoreing, OpenRuns,
                     Cache)
from event import Relay24hEvent
from course import Course, Control
from runner import Category
from observer import TriggerEventObserver
                    
# Database URI and store
db_uri = 'postgres://24h:forst@server/24h'
#db_uri = 'postgres:24h'
store = Store(create_database(db_uri))

# Directory with templates
template_dir = 'templates'

# create cache (but don't connect to an observer)
cache = Cache()

# create an Event Observer
observer = TriggerEventObserver(store)

# EventRanking object
starttime = datetime(2008,5,10,19,00)
_cat24h = store.find(Category, Category.name == u'24h').one()
_cat12h = store.find(Category, Category.name == u'12h').one()
_last_ctrls = [store.find(Control, Control.code == u'200').one(),
               store.find(Control, Control.code == u'199').one()]

event = Relay24hEvent(starttime_24h = starttime,
                      starttime_12h = datetime(2008,5,11,7,0),
                      speed = 6,
                      extra_rankings = [('24h_lkm',
                                         {'obj':_cat24h,
                                          'scoreing_args':{'method':'lkm'}
                                          }
                                         ),
                                        ('12h_lkm',
                                         {'obj':_cat12h,
                                          'scoreing_args':{'method':'lkm'}
                                          }
                                         ),
                                        ('24h_start',
                                         {'obj':_cat24h,
                                          'scoreing_args':{'blocks':'start'},
                                          'validation_args':{'blocks':'start'}
                                          }
                                         ),
                                        ('24h_night',
                                         {'obj':_cat24h,
                                          'scoreing_args':{'blocks':'night'},
                                          'validation_args':{'blocks':'night'}
                                          }
                                         ),
                                        ('24h_day',
                                         {'obj':_cat24h,
                                          'scoreing_args':{'blocks':'day'},
                                          'validation_args':{'blocks':'day'}
                                          }
                                         ),
                                        ('12h_start',
                                         {'obj':_cat12h,
                                          'scoreing_args':{'blocks':'start'},
                                          'validation_args':{'blocks':'start'}
                                          }
                                         ),
                                        ('12h_day',
                                         {'obj':_cat12h,
                                          'scoreing_args':{'blocks':'day'},
                                          'validation_args':{'blocks':'day'}
                                          }
                                         ),
                                        ('warning',
                                         {'obj':OpenRuns(store),
                                          'scoreing_args': {'control_list': _last_ctrls,
                                                           },
                                          }
                                         ),
                                        ],
                      header = {'event'  : '24 Stunden Orientierungslauf Schweiz 2008',
                                'map'    : 'Forst',
                                'place'  : 'Heitere, Neuenegg',
                                'date'   : '11./12. May 2008',
                                'organiser' : 'UBOL / OLG Bern'},
                      duration_24h = timedelta(hours=24, minutes = 0),
                      duration_12h = timedelta(hours=12, minutes = 0),
                      cache = cache, store = store)
                                     
                                     
#rankings['warning'] = MakoRankingFormatter(ranking, header,
#                                           {'title': 'Advance Warning'},
#                                           'warning.html', template_dir)
                                   
