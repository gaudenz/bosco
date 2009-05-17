#/usr/bin/env python
# -*- coding: utf-8 -*-
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

from event import RelayEvent
from course import Course, Control
from runner import Category
from observer import TriggerEventObserver
                    
# Database URI and store
db_uri = 'postgres:ubol3'
store = Store(create_database(db_uri))

# Directory with templates
template_dir = 'templates'

# create cache (but don't connect to an observer)
cache = Cache()

# create an Event Observer
observer = TriggerEventObserver(store)

event = RelayEvent(legs = [(u'0', datetime(2008,5,1,11,50)),
                           (u'1', datetime(2008,5,1,11,55)),
                           (u'2', datetime(2008,5,1,13,10)),
                           (u'3', datetime(2008,5,1,14,10))],
                   header = {'event'     : u'Jura 3er-Staffel 2008',
                             'map'       : u'Tete Plumée',
                             'place'     : u'Les Trois Chênes',
                             'date'      : u'1. May 2008',
                             'organiser' : u'UBOL'},
                   extra_rankings = [('warning',
                                      {'obj':OpenRuns(store),
                                       'scoreing_args': {'control_list': [store.find(Control, Control.code == u'155').one()],
                                                         },
                                       }
                                      ),
                                     ],
                   html_template = 'relay.html',
                   store = store,
                   cache = cache
                   )

                    
