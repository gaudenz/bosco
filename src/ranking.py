#/usr/bin/env python
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
ranking.py - Classes to produce rankings of objects that implement
             Rankable. Each class that has a ranking (currently
             Course and Category) has to inherit from Rankable.
             Rankable specifies the interface of rankable classes.
"""

from datetime import timedelta, datetime
from copy import copy

from storm.locals import *

class RankableItem:
    """Defines the interface for all rankable items (currently Runner, Team, Run).
    This interfaces specifies the methods to access information about the RankableItem
    like name and score (time, points, ...) in an independent way. This is ensures that
    RankingFormatters don't need information about the objects in the ranking."""

    def start(self):
        raise UnscoreableException('You have to override start to rank this object with this scoreing strategy.')
    
    def finish(self):
        raise UnscoreableException('You have to override finish to rank this object with this scoreing strategy.')

    def _get_complete(self):
        raise ValidationError('You have to override the complete property to validate this object with this validation strategy.')
    complete = property(_get_complete)

    def __str__(self):
        return 'override __str__ for a more meaningful value'

class Ranking(object):
    """A Ranking objects combines a scoreing strategy, a validation strategy and a
    rankable object (course or category) and computes a ranking. The Ranking object
    is an interable object, which means you can use it much like a list. It returns
    a new iterator on every call to __iter__.
    The order of the ranking is defined by the scoreing strategy. Strategy has the be a subclass
    of ScoreingStrategy compatible with the RankableItem objects of this Rankable.
    The ranking is generated in lowest first order. The overcome this restriction 
    seperate RankingStrategies should be implemented.

    The iterator returns dictionaries with the keys 'rank', 'score', 'validation',
    'item', 'info'.
    """

    def __init__(self, rankable, scoreing, validation):
        self._rankable = rankable
        self._scoreing = scoreing
        self._validation = validation

    def __iter__(self):

        def ranking_generator(ranking_list):

            rank = 1
            for i, m in enumerate(ranking_list):
                # Only increase the rank if the current item scores higher than the previous item
                if i > 0 and ranking_list[i][0] > ranking_list[i-1][0]:
                    rank = i + 1
                yield {'rank': m[1][0] == ValidationStrategy.OK and rank or None, # only assign rank if run is OK
                       'score': m[0],
                       'validation': m[1][0],
                       'item': m[2],
                       'info': m[1][1],
                       }

        # Create list of (score, member) tuples and sort by score
        ranking_list = [(self._scoreing.score(m), self._validation.validate(m), m)
                        for m in self._rankable.members]
        ranking_list.sort(key = lambda x: x[0])
        ranking_list.sort(key = lambda x: x[1][0])

        # return the generator
        return ranking_generator(ranking_list)

class Rankable:
    """Defines the interface for rankable objects like courses and categories.
    The following attributes must be available in subclasses:
    - members
    """
    pass

class OpenRuns(Rankable):

    def __init__(self, store, control = None):
        """
        @param store:   Store for the open runs. This class uses a Storm store to
                        search for open runs, but it is not a Storm object itself!
        @param control: Only list open runs which should pass at this control or
                        punched this control. (not yet implemented)
        """
        self._store = store
        self._control = control
        
    def _get_runs(self):
        from run import Run
        return self._store.find(Run, Run.complete == False)
    
    members = property(_get_runs)
    
class Cache(object):
    """Cache for scoreing and validation results."""

    def __init__(self, observer = None):
        """
        @param observer: Observer wich notifys the cache of changes in
                         cached objects.
        @type observer:  object of class EventObserver
        """
        self._cache = {}
        self._observer = observer
        
    def __getitem__(self, key):
        (obj, func) = key
        return self._cache[obj][func]

    def __setitem__(self, key, value):
        (obj, func) = key
        if not obj in self._cache:
            self._cache[obj] = {}
        self._cache[obj][func] = value
        if self._observer:
            self._observer.register(self, obj)

    def __delitem__(self, key):
        (obj, func) = key
        if self._observer:
            self._observer.unregister(self, obj)
        del self._cache[obj]

    def __contains__(self, key):
        (obj, func) = key
        return obj in self._cache and func in self._cache[obj]
    
    def update(self, obj):
        del self[obj]

    def set_observer(self, observer):
        """
        Sets an observer for this cache.
        """
        if self._observer is not None:
            self.remove_observer()
        for obj in self._cache:
            observer.register(self, obj)
        self._observer = observer

    def remove_observer(self):
        """
        Removes any existing observer for this cache.
        """
        if self._observer is not None:
            for obj in self._cache:
                self._observer.unregister(self, obj)
            self._observer = None
        
class AbstractScoreingStrategy(object):
    """Defines a strategy for scoring objects (runs, runners, teams). The scoreing 
    strategy is tightly coupled to the objects it scores.

    Computed scores can (and should!) be stored in a cache.
    """

    def __init__(self, cache = None):
        """
        @param cache: scoreing cache
        """
        self._cache = cache

    def score(self, object):
        """Returns the score of the given objects. Throws UnscoreableException if the 
        object can't be scored with this strategy. The returned score must implement 
        __cmp__."""
        raise UnscoreableException('Can\'t score with AbstractScoreingStrategy')
        
    def _from_cache_score(self, obj):
        """
        Check cache and return cached result if it exists.
        @param obj:  Object of the startegy.
        @type obj:   object of class RankableItem
        @raises:     KeyError if object is not in the cache
        """
        if self._cache:
            return self._cache[(obj, self.score)]
        else:
            raise KeyError

    def _to_cache_score(self, obj, result):
        """
        Check cache and return cached result if it exists.
        @param obj:  Object of the startegy.
        @type obj:   object of class RankableItem
        """
        if self._cache:
            self._cache[(obj, self.score)] = result
        
class AbstractTimeScoreingStrategy(AbstractScoreingStrategy):
    """Builds the score from difference of start and finish times. Subclasses must
    override _start and _finish the extract the start and finsh times from objects."""
    
    def _start(self, obj):
        """Returns the start time as a datetime object."""
        raise UnscoreableException('You have to override _start in subclasses.')
    
    def _finish(self, obj):
        """Returns the finish time as a datetime object."""
        raise UnscoreableException('You have to override _finish in subclasses.')
    
    def score(self, obj):
        """Returns a timedelta object as the score by calling start and finish on 
        the object."""
        try:
            return self._from_cache_score(obj)
        except KeyError:
            pass
        
        try:
            result = self._finish(obj) - self._start(obj)
        except TypeError:
            # is this really the best thing to do?
            result = timedelta(0)

        self._to_cache_score(obj, result)
        return result
        
class MassStartTimeScoreingStrategy(AbstractTimeScoreingStrategy):
    """Returns time scores relative to a fixed mass start time."""
    
    def __init__(self, starttime, cache = None):
        AbstractScoreingStrategy.__init__(self, cache)
        self._starttime = starttime
        
    def _start(self, obj):
        return self._starttime
    
    def _finish(self, obj):
        return obj.finish()
    
class SelfStartTimeScoreingStrategy(MassStartTimeScoreingStrategy):
    """Returns time scores from start and finish punches on a Run object."""
    
    def __init__(self, cache = None):
        AbstractScoreingStrategy.__init__(self, cache)
        
    def _start(self, obj):
        return obj.start()
    
class RelayTimeScoreingStrategy(MassStartTimeScoreingStrategy):
    """Returns time scores computed from starttime == finish time of the previous runner
    in a relay team. For the first runner the start time is used."""

    def _start(self, obj):
        if obj.punches.count() == 0:
            # Can't compute start time if there are no punches
            return None
        
        # Get the team for this run
        team = obj.sicard.runner.team

        # This makes the whole thing dependant on the exact database layout,
        # but it is a huge perfomance win
        from course import SIStation
        store = Store.of(team)
        starttime = store.execute(
            """SELECT MAX(finishtime) FROM (
                  SELECT MIN(punch.punchtime) AS finishtime
                     FROM team JOIN runner ON team.id = runner.team
                        JOIN sicard ON runner.id = sicard.runner
                        JOIN run ON sicard.id = run.sicard
                        JOIN punch ON run.id = punch.run
                     WHERE team.id = %s
                        AND punch.sistation = %s
                        AND punch.punchtime < %s
                     GROUP BY run.id)
                  AS finishtimes""",
            params = (team.id,
                      SIStation.FINISH,
                      obj.punches.order_by('punchtime').first().punchtime)
            ).get_one()[0]
        
        if starttime == None:
            return self._starttime
        else:
            return starttime

class MassStartRelayTimeScoreingStrategy(RelayTimeScoreingStrategy):
    """Relay event with mass start for all runners not yet replaced."""
    
    def __init__(self, massstart_time, cache = None):
        AbstractScoreingStrategy.__init__(self, cache)
        MassStartTimeScoreingStrategy.__init__(self, massstart_time)

    def _start(self, obj):
        prev_finish = super(type(self), self)._start(obj)
        return self._starttime < prev_finish and self._starttime or prev_finish

class ValidationStrategy(object):
    """Defines a strategy for validating objects (runs, runners, teams). The validation
    strategy is tightly coupled to the objects it validates."""

    # Ranking constants (return values for validate)
    # This also defines to sorting order of these states in the
    # ranking.
    OK               = 1 # valid run
    NOT_COMPLETED    = 2 # run not yet completed but started
    MISSING_CONTROLS = 3 # missing one or more obligatory controls
    DID_NOT_FINISH   = 4 # runner did not finish (but run is complete)
    DISQUALIFIED     = 5 # disqualified for regulatory reasons
    DID_NOT_START    = 6 # runner / team did not (yet) start

    _validation_cache = {}

    def __init__(self, cache = None):
        """
        @param cache: validation cache
        """
        self._cache = cache
        
    def validate(self, obj):
        """Returns OK for every object. Override in subclasses for more meaningfull
        validations."""
        return (ValidationStrategy.OK, {})

    def _from_cache_validate(self, obj):
        """
        Check cache and return cached result if it exists.
        @param obj:  Object of the startegy.
        @type obj:   object of class RankableItem
        @raises:     KeyError if object is not in the cache
        """
        if self._cache:
            return self._cache[(obj, self.validate)]
        else:
            raise KeyError
        
    def _to_cache_validate(self, obj, result):
        """
        Check cache and return cached result if it exists.
        @param obj:  Object of the startegy.
        @type obj:   object of class RankableItem
        """
        if self._cache:
            self._cache[(obj, self.validate)] = result
        

class CourseValidationStrategy(ValidationStrategy):
    """Validation strategy for courses."""

    def __init__(self, course, cache = None):
        ValidationStrategy.__init__(self, cache)
        self._course = course
        
    def validate(self, run):
        """Check if run is a valid run for this course. This only checks if the run
        is complete has a start punch and a finish punch. It does not check any controls!
        Override this in subclasses for more usefull validation (and call super() to not
        duplicate this code)."""
        try:
            return self._from_cache_validate(run)
        except KeyError:
            pass
        
        if not run.complete:
            result = ValidationStrategy.NOT_COMPLETED
        elif not run.finish():
            result =  ValidationStrategy.DID_NOT_FINISH
        elif run.override is True:
            result = ValidationStrategy.OK
        else:
            result = ValidationStrategy.OK

        ret = (result, {})
        self._to_cache_validate(run, ret)
        return ret

class SequenceCourseValidationStrategy(CourseValidationStrategy):
    """Validation strategy for a normal orienteering course.
    This class uses a dynamic programming "longest common subsequence"
    algorithm to validate the run and find missing and additional punches.
    @see http://en.wikipedia.org/wiki/Longest_common_subsequence_problem.
    """

    @staticmethod
    def _build_lcs_matrix(plist, clist):
        """Builds the matrix of lcs subsequence lengths.
        @param plist: list of punches
        @param clist: list of controls. All controls with no sistations or which are
                      overriden must be removed!
        @return:      matrix of lcs subsequence lengths.
        """
        
        m = len(plist)
        n = len(clist)
        
        # build (m+1) * (n+1) matrix
        C = [[0] * (n+1) for i in range(m+1) ]
        
        i = j = 1
        for i in range(1, m+1):
            for j in range(1, n+1):
                if plist[i-1][1] is clist[j-1]:
                    C[i][j] = C[i-1][j-1] + 1
                else:
                    C[i][j] = max(C[i][j-1], C[i-1][j])

        return C

    @staticmethod
    def _backtrack(C, plist, clist, i = None, j = None):
        """Backtrack through the LCS Matrix to find one of possibly
        several longest common subsequences."""

        if i is None:
            i = len(plist)
        if j is None:
            j = len(clist)
            
        if i == 0 or j == 0:
            return []
        elif plist[i-1][1] is clist[j-1]:
            return SequenceCourseValidationStrategy._backtrack(C, plist, clist, i-1, j-1) + [ clist[j-1] ]
        else:
            if C[i][j-1] > C[i-1][j]:
                return SequenceCourseValidationStrategy._backtrack(C, plist, clist, i, j-1)
            else:
                return SequenceCourseValidationStrategy._backtrack(C, plist, clist, i-1, j)
        
    @staticmethod
    def _diff(C, plist, clist, i = None, j = None):
        """
        @return: (additional_punches_list, missing_controls_list)
        """

        if i is None:
            i = len(plist)
        if j is None:
            j = len(clist)
            
        additional = []
        missing = []
        if i > 0 and j > 0 and plist[i-1][1] is clist[j-1]:
            (a,m) = SequenceCourseValidationStrategy._diff(C, plist, clist, i-1, j-1)
            additional += a
            missing += m
        else:
            if j > 0 and (i == 0 or C[i][j-1] >= C[i-1][j]):
                (a, m) = SequenceCourseValidationStrategy._diff(C, plist, clist, i, j-1)
                additional += a
                missing += m
                missing.append(clist[j-1])
            elif i > 0 and (j == 0 or C[i][j-1] < C[i-1][j]):
                (a, m) = SequenceCourseValidationStrategy._diff(C, plist, clist, i-1, j)
                additional += a
                missing += m
                additional.append(plist[i-1][0])
        return (additional, missing)
                
    def validate(self, run):
        """Validate the run if it is valid for this course."""

        try:
            return self._from_cache_validate(run)
        except KeyError:
            pass
        
        result = super(type(self), self).validate(run)[0]
        # check correct sequence of controls
        
        punchlist = [(p, p.sistation.control) for p in run.punches.order_by('punchtime') ]
        # list of all controls which have sistations
        controllist = [ i.control for i in
                        self._course.sequence.order_by('sequence_number')
                        if (i.control.sistations.count() > 0 and
                            i.control.override is not True) ]

        C = SequenceCourseValidationStrategy._build_lcs_matrix(punchlist, controllist)
        (additional, missing) = SequenceCourseValidationStrategy._diff(C,
                                                                       punchlist,
                                                                       controllist)

        if result == ValidationStrategy.OK and not run.override is True:
            if len(missing) > 0:
                result = ValidationStrategy.MISSING_CONTROLS

        ret = (result, {'missing': missing,
                        'additional': additional})
            
        self._to_cache_validate(run, ret)
        return ret

class Relay24hScoreingStrategy(AbstractScoreingStrategy, ValidationStrategy):
    """This class is both a validation strategy and a scoreing strategy. The strategies
    are combined because they use some common private functions. This class validates
    and scores teams for the 24h relay."""

    def __init__(self, starttime, speed, duration = timedelta(hours=24),
                 cache = None):
        """
        @param starttime: Start time of the event.
        @type starttime:  datetime.datetime
        @param speed:     expected speed in minutes per kilometers. Used to compute
                          penalty time for invalid runs
        @type speed:      int
        @param duration:  Duration of the event (default 24h)
        """
        AbstractScoreingStrategy.__init__(self, cache)
        self._starttime = starttime
        self._speed = speed
        self._duration = duration

    def _loop_over_runs(self, team):
        """This is an utility function to not duplicate code in _check_order and
        _omitted_runners. It loops over all runs, counts the omitted runners and
        checks the order. Returns a tuple
        (validation_code, number_of_omitted_runners)."""

        # try fetching from cache
        try:
            return self._cache[(team, self._loop_over_runs)]
        except (KeyError, TypeError):
            pass
        
        # collect team members and runs
        members = list(team.members.order_by('number'))
        runs = team.runs

        # check runner order
        remaining = copy(members)
        next_runner = 0
        status = ValidationStrategy.OK
        for i,r in enumerate(runs):
            while not r.sicard.runner == remaining[next_runner]:
                if i < len(members):
                    # not every runner has run at least once
                    status = ValidationStrategy.DISQUALIFIED
                # next_runner gave up -> delete
                del(remaining[next_runner])
                # any runners left?
                if len(remaining) == 0:
                    status = ValidationStrategy.DISQUALIFIED
                    break
                if next_runner >= len(remaining):
                    # wrap around
                    next_runner = 0
                    
            if len(remaining) == 0:
                break
            
            next_runner  = (next_runner+1)%len(remaining)

        result = (status, len(members) - len(remaining))

        # save to cache and return result
        if self._cache:
            self._cache[(team, self._loop_over_runs)] = result
        return result

    def _check_order(self, team):
        """Checks if the order of the runners is correct."""
        return self._loop_over_runs(team)[0]
        
    def _omitted_runners(self, team):
        """Count the runners that were omitted during the event and gave up."""
        return self._loop_over_runs(team)[1]
        
    def validate(self, team):
        """Validate the runs of this team according to the rules
        of the 24h orienteering event.
        The following rules apply:
          - runners must run in the defined order, omitted runners may not
            run again
          - every runner must run at least once at the beginning of the event
          - runs must be run in the following order:
            - 4 start courses (Codes S1-4), fixed order defined for each
              team
            - night courses (Codes NLD1-3, NLE1-3, NSD1-4, NSE1-5), free order
              choosen by team
            - day courses (Codes LDx, LEx, SDx, SEx), free order
              choosen by team
            - 6 finish courses (Codes F1-6), same order for each team"""

        try:
            return self._from_cache_validate(team)
        except KeyError:
            pass

        # check for override
        if team.override is True:
            result = ValidationStrategy.OK
        else:
            # check runner order
            result = self._check_order(team)
            if result == ValidationStrategy.OK:
                # check run order
                # not cheked, this is ensured by proper event organisation :-)
                pass

        ret = (result, {})
        self._to_cache_validate(team, ret)
        return ret


    def score(self, team):
        """Compute score for a 24h team according to the following rules:
        - compute finish time:
          - 24h - (omitted_runners - 1) * 30min - sum(expected_time -
            running_time) for all failed runs
        - count valid runs completed before the finish time
        - record finish time of the last VALID run
        The result is a 24hScore object consisting of the number of runs
        and the finish time of the last run (not equal to the finish time
        computed in the first step!)."""

        try:
            return self._from_cache_score(team)
        except KeyError:
            pass
        
        runs = [r for r in team.runs if r.complete]
        run_scoreing = RelayTimeScoreingStrategy(self._starttime)
        
        failed = [ r for r in runs
                   if not r.course.validator(SequenceCourseValidationStrategy).validate(r)[0] == ValidationStrategy.OK ]
        fail_penalty = timedelta(0)
        for f in failed:
            penalty = f.course.expected_time(self._speed) - run_scoreing.score(f)
            if penalty < timedelta(0):
                # no negative penalty
                penalty = timedelta(0)
            fail_penalty += penalty
 
        give_up_penalty = (self._omitted_runners(team)-1) * timedelta(minutes=30)
        if give_up_penalty < timedelta(0):
            # correct penalty if no runner gave up
            give_up_penalty = timedelta(0)
        
        finish_time = (self._starttime + self._duration
                       - fail_penalty - give_up_penalty)

        valid_runs = [ r for r in runs
                       if r.finish() <= finish_time
                       and r.course.validator(SequenceCourseValidationStrategy).validate(r)[0] == ValidationStrategy.OK ]

        if len(valid_runs) > 0:
            result = Relay24hScore(len(valid_runs),
                                 max(valid_runs, key=lambda x: x.finish()).finish()
                                 - self._starttime)
        else:
            result = Relay24hScore(0, timedelta(0))

        self._to_cache_score(team, result)
        return result

class Relay12hScoreingStrategy(Relay24hScoreingStrategy):
    """This class is both a valiadtion and a scoreing strategy. It implements the
    different validation algorithm of the 12h relay."""

    def __init__(self, starttime, speed, duration = timedelta(hours=12),
                 cache = None):
        """
        @param starttime: Start time of the event.
        @type starttime:  datetime.datetime
        @param speed:     expected speed in minutes per kilometers. Used to compute
                          penalty time for invalid runs
        @type speed:      int
        @param duration:  Duration of the event (default 24h)
        """
        super(type(self), self).__init__(starttime, speed, duration,
                                         cache)
        
    def _omitted_runners(self, team):
        """The order of the runners for the 12h relay is free. So no runner may
        be omitted. Runner that give up don't cause a time penalty."""
        return 0

    def validate(self, team):
        """Validate the runs of this team according to the rules
        of the 12h orienteering event.
        The following rules apply:
          - the order of the runners is free the team may change it at
            any time
          - runs must be run in the following order:
            - 1 start course (Code S), individually for each team
            - day courses (Codes LDx, LEx, SDx, SEx), free order
              choosen by team
            - 2 finish courses (Codes F1-2), same order for each team"""

        try:
            return self._from_cache_validate(team)
        except KeyError:
            pass
        
        # run order is not checked yet
        result = ValidationStrategy.OK

        ret = (result, {})
        self._to_cache_validate(team, ret)
        return ret

class Relay24hScore(object):

    def __init__(self, runs, time):
        self._runs = runs
        self._time = time

    def __cmp__(self, other):
        """compares two Relay24hScore objects."""
        
        if self._runs > other._runs:
            return -1
        elif self._runs < other._runs:
            return 1
        else:
            if self._time < other._time:
                return -1
            elif self._time > other._time:
                return 1
            else:
                return 0

    def __str__(self):
        return "Runs: %s, Time: %s" % (self._runs, self._time) 

class ControlPunchtimeScoreingStrategy(AbstractScoreingStrategy, ValidationStrategy):
    """Scores according to the (expected) absolute punchtime at a given control.
    This is not intended for preliminary results but to watch a control near the
    finish and to show incomming runners.
    To make effective use of this you need a rankable with all open runs as members.
    RankableItems scored with this strategy should be open runs.
    This is a combined scoreing and validation strategy. 
    """

    def __init__(self, control_list, distance_to_finish = 0,
                 cache = None):
        """
        @param control_list:       score at these controls
        @param distance_to_finish: distance form control to the finish.
                                   This is used to compute the expected
                                   time at this control (not yet implemented)
        """
        AbstractScoreingStrategy.__init__(self, cache)
        self._controls = control_list
        self._distance_to_finish = distance_to_finish

    def validate(self, run):
        """
        @return: ValidationStrategy.OK if the control was punched,
                 ValidationStrategy.NOT_COMPLETED if the control was not yet punched
        """
        try:
            return self._from_cache_validate(run)
        except KeyError:
            pass

        punchlist = [p.sistation.control for p in run.punches]
        result = ValidationStrategy.NOT_COMPLETED
        for c in self._controls:
            if c in punchlist:
                result = ValidationStrategy.OK
                break
        
        ret = (result, {})
        self._to_cache_validate(run, ret)
        return ret

    def score(self, run):
        """
        @return: time of the punch or datetime.min if punchtime is unknown.
                 If more than one of the control was punched, the punchtime
                 of the first in the list is returned.
        """
        try:
            return self._from_cache_score(run)
        except KeyError:
            pass
        
        try:
            (controls, punchtimes) = zip(*[(p.sistation.control, p.punchtime)
                                           for p in run.punches])
            
            result = datetime.min
            for c in self._controls:
                try:
                    index = list(controls).index(c)
                    result = punchtimes[index]
                    break
                except ValueError:
                    pass
            
        except ValueError:
            # no punches in this run
            result = datetime.min
        
        self._to_cache_score(run, result)
        return result
    
class UnscoreableException(Exception):
    pass

class ValidationError(Exception):
    pass
