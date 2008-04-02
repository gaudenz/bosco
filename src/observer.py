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
observer.py - Classes to observe the data store
"""

from threading import Timer
from storm.locals import *

from run import Punch
import conf

class EventObserver():
    """Observes an Event for new data (e.g. new punches)"""

    def __init__(self, interval = 5):

        self._interval = interval
        
        # allocate own store and db connection to make sure this is independant of
        # running transactions
        self._store = Store(create_database(conf.db_uri))
        
        self._registry = {'punch': []}

        self._last = {'punch': None}
        self._running = True
        self.observe() # this also starts the timer
        

    def _start_timer(self):
        if not self._running == False:
            t = Timer(self._interval, self.observe)
            t.start()

    def stop(self):
        self._running = False
        
    def register(self, obj, event):
        """Register an object to be notified of changes of type event.

        @param obj:   The object to receive to notification. obj must have a
                      update(self, event) method.
        @param event: Event type to observe. Currently only 'punch'
        """
        self._registry[event].append(obj)

    def unregister(self, obj, event):
        """Unregister an object from this observer for this event."""
        self._registry[event].remove(obj)
        
    def observe(self):
        """Does the actual observation."""

        print "observing events"
        
        # rollback store to end transaction
        self._store.rollback()
        
        last_punch = self._store.execute(Select(Max(Punch.id))).get_one()
        if self._last['punch'] != last_punch:
            self._last['punch'] = last_punch
            self._notify('punch')

        # start new timer
        self._start_timer()

    def _notify(self, event):
        """Notifies objects of an event."""
        for obj in self._registry[event]:
            obj.update(event)

    
