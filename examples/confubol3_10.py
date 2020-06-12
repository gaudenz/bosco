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

starttime = datetime(2009, 5, 21, 11, 45)
event = RelayEvent(legs = [{'name':        '0',
                            'variants':    ('0A', '0B'), 
                            'starttime':   starttime, 
                            'defaulttime': timedelta(minutes=5)},
                           {'name':        '1',
                            'variants':    ('1AA', '1AB', '1BA', '1BB'), 
                            'starttime':   datetime(2009, 5, 21, 11, 50), 
                            'defaulttime': None},
                           {'name':        '2',
                            'variants':    ('2', ), 
                            'starttime':   datetime(2009, 5, 21, 13, 45), 
                            'defaulttime': None},
                           {'name':        '3',
                            'variants':    ('3AA', '3AB', '3BA', '3BB'), 
                            'starttime':   datetime(2009, 5, 21, 13, 45), 
                            'defaulttime': None}
                           ],
                   header = {'event'     : 'Jura 3er-Staffel 2010',
                             'map'       : 'Bois du Devens',
                             'place'     : 'Le Devens',
                             'date'      : '13. Mai 2010',
                             'organiser' : 'UBOL'},
                   html_template = 'relay.html',
                   store = store,
                   cache = cache
                   )

                    
