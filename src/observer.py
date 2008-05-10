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
from datetime import datetime

from run import Punch, Run
from runner import Team
import conf

class EventObserver(object):
    """Observes an Event for new data (e.g. new punches).
    @warn: This will rollback the store every <intervall> seconds!
    """

    def _punch_notify(self, punch):

        self._run_notify(punch.run)
        
    def _run_notify(self, run):

        # send notification for run
        self._notify(run)

        # send for runner
        if run.sicard.runner is not None:
            self._runner_notify(run.sicard.runner)

        # send notifications for course
        if run.course is not None:
            self._course_notify(run.course)


    def _runner_notify(self, runner):
        self._notify(runner)

        # send for team
        if runner.team is not None:
            self._team_notify(runner.team)

        # send notifications for category
        if runner.category is not None:
            self._category_notify(runner.category)
                
    def _team_notify(self, team):
        self._notify(team)

        # send for category
        if team.category is not None:
            self._category_notify(team.category)

    def _category_notify(self, category):
        self._notify(category)

    def _course_notify(self, course):
        self._notify(course)
        
    _tables = [(Punch, _punch_notify),
               ]
    
    def __init__(self, store, interval = 5, rollback = True):
        """
        @param interval: Check interval
        @param rollback: Rollback store before checking for new objects?
                         This is necessary to get new objects added by other
                         connections but it resets all uncommited changes.
        """

        self._interval = interval
        
        self._store = store
        self._rollback = rollback
        
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
        if self._rollback:
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
        try:
            for obj in self._registry[observable]:
                obj.update(observable)
        except KeyError:
            pass

    
class TriggerEventObserver(EventObserver):
    """Observes an Event for new data (e.g. new punches).
    This implementation uses triggers and a log table to
    also get notified of changed values.
    @warn: This will rollback the store every <intervall> seconds!
    """

    _tables = {Punch : EventObserver._punch_notify,
               Run   : EventObserver._run_notify,
               Team  : EventObserver._team_notify,
               }

    def __init__(self, store, interval = 5, rollback = True):
        """
        @param interval: Check interval
        @param rollback: Rollback store before checking for new objects?
                         This is necessary to get new objects added by other
                         connections but it resets all uncommited changes.
        """
        EventObserver.__init__(self, store, interval, rollback)
        self._last = datetime.now()
        
    def observe(self):
        """Does the actual observation."""

        try:
            # rollback store to end transaction
            if self._rollback:
                self._store.rollback()

            changed = self._store.execute("""SELECT object_type, change_time, row
                                               FROM log
                                               WHERE change_time > %s
                                               ORDER BY change_time""",
                                          params = [self._last])
        
            for row in changed:
                for obj_type in self._tables.keys():
                    if row[0] == obj_type.__storm_table__:
                        obj = self._store.get(obj_type, row[2])
                        if obj is not None:
                            self._tables[obj_type](self, obj)

            # obj is now the last object
            try:
                self._last = row[1]
            except UnboundLocalError:
                pass

        finally:
            # start new timer, even if an exception occurs
            self._start_timer()

    
