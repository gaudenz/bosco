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

class EventObserver(object):
    """Observes an Event for new data (e.g. new punches).
    @warn: This will rollback the store every <intervall> seconds!
    """

    def _punch_notify(self, punch):
        
        # send notifications for run
        if punch.run in self._registry:
            self._notify(punch.run)
            
        # send notifications for runner
        if punch.run.sicard.runner in self._registry:
            self._notify(punch.run.sicard.runner)

        # send notifications for team
        if punch.run.sicard.runner.team in self._registry:
            self._notify(punch.run.sicard.runner.team)
            
    _tables = [(Punch, _punch_notify),
               ]
    
    def __init__(self, store, interval = 5):

        self._interval = interval
        
        # allocate own store and db connection to make sure this is independant of
        # running transactions
        self._store = store
        
        self._registry = {}

        self._last = {}
        for t in EventObserver._tables:
            self._last[t[0]] = self._get_max(t[0])
            
        self._running = False
        
    def _start_timer(self):
        if self._running == True:
            t = Timer(self._interval, self.observe)
            t.start()
            
    def stop(self):
        self._running = False
        
    def register(self, obj, observable):
        """Register an object to be notified of changes of type event.

        @param obj:        The object to receive to notification. obj must have a
                           update(self, event) method.
        @param observable: object that should be observed for changes. Currently
                           run, runner and team are supported
        """
        if not observable in self._registry:
            self._registry[observable] = []
        self._registry[observable].append(obj)
        if self._running == False:
            self._running = True
            self._start_timer()

    def unregister(self, obj, observable):
        """Unregister an object from this observer for this observable."""
        self._registry[observable].remove(obj)
        if len(self._registry[observable]) == 0:
            del(self._registry[observable])
        if len(self._registry) == 0:
            self._running = False
        
    def observe(self):
        """Does the actual observation."""

        # rollback store to end transaction
        self._store.rollback()

        for t in EventObserver._tables:
            last = self._get_max(t[0])
            if self._last[t[0]] != last:
                for i in range(self._last[t[0]]+1, last+1):
                    obj = self._store.get(t[0], i)
                    if not obj is None:
                        t[1](self, obj)
            self._last[t[0]] = last
            
        # start new timer
        self._start_timer()

    def _get_max(self, t):
        return self._store.execute(Select(Max(t.id))).get_one()[0] or 0
    
    def _notify(self, observable):
        """Notifies objects of an event."""
        for obj in self._registry[observable]:
            obj.update(observable)

    
