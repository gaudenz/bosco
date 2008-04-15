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

from datetime import timedelta
from copy import copy

from storm.locals import Store

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

    The complete ranking is only computed on the first call to __iter__. Subsequent calls
    return a ranking from cached data. Ranking objects can be registered with an
    EventObserver object to automatically invalidate the cache on changes.
    """

    def __init__(self, rankable, scoreing, validation):
        self._rankable = rankable
        self._scoreing = scoreing
        self._validation = validation
        self._ranking_list = None

    def __iter__(self):

        def ranking_generator(ranking_list, scoreing, validation):

            rank = 1
            for i, m in enumerate(ranking_list):
                # Only increase the rank if the current item scores higher than the previous item
                if i > 0 and ranking_list[i][0] > ranking_list[i-1][0]:
                    rank = i + 1
                yield {'rank': m[1] == ValidationStrategy.OK and rank or None, # only assign rank if run is OK
                       'score': m[0],
                       'validation': m[1],
                       'item': m[2],
                       'info': None,
                       }

        if self._ranking_list is None:
            # Create list of (score, member) tuples and sort by score
            self._ranking_list = [(self._scoreing.score(m), self._validation.validate(m), m)
                                    for m in self._rankable.members]
            self._ranking_list.sort(key = lambda x: x[0])
            self._ranking_list.sort(key = lambda x: x[1])

        # return the generator
        return ranking_generator(self._ranking_list, self._scoreing, self._validation)

    def update(self, event):
        """Invalidates the cache.
        @param event: type of update event, currently not used
        """
        
        # Invalidate ranking list and rollback store
        Store.of(self._rankable).rollback()
        self._ranking_list = None
    
    
class Rankable:
    """Defines the interface for rankable objects like courses and categories.
    The following attributes must be available in subclasses:
    - members
    """
    pass

class AbstractScoreingStrategy(object):
    """Defines a strategy for scoring objects (runs, runners, teams). The scoreing 
    strategy is tightly coupled to the objects it scores. """

    def score(self, object):
        """Returns the score of the given objects. Throws UnscoreableException if the 
        object can't be scored with this strategy. The returned score must implement 
        __cmp__."""
        raise UnscoreableException('Can\'t score with AbstractScoreingStrategy')
        
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
            return self._finish(obj) - self._start(obj)
        except TypeError:
            # is this really the best thing to do?
            return timedelta(0)
        
class MassStartTimeScoreingStrategy(AbstractTimeScoreingStrategy):
    """Returns time scores relative to a fixed mass start time."""
    
    def __init__(self, starttime):
        self._starttime = starttime
        
    def _start(self, obj):
        return self._starttime
    
    def _finish(self, obj):
        return obj.finish()
    
class SelfStartTimeScoreingStrategy(MassStartTimeScoreingStrategy):
    """Returns time scores from start and finish punches on a Run object."""
    
    def __init__(self):
        pass
        
    def _start(self, obj):
        return obj.start()
    
class RelayTimeScoreingStrategy(MassStartTimeScoreingStrategy):
    """Returns time scores computed from starttime == finish time of the previous runner
    in a relay team."""

    def __init__(self):
        pass

    def _start(self, obj):
        # Get the team for this run
        team = obj.sicard.runner.team
        
        # Search through all runs to find the previous run
        prev_run = None
        for m in team.members:
            for si in m.sicards:
                for r in si.runs:
                    # Select this run if it finished later than prev_run and
                    # if the finish time is earlier than the finish time of
                    # the run to score
                    if (prev_run == None or r.finish() > prev_run.finish()) \
                       and  r.finish() < obj.finish():
                        prev_run = r

        if prev_run == None:
            raise UnscoreableException('No previous run found.')

        return prev_run.finish()

class MassStartRelayTimeScoreingStrategy(RelayTimeScoreingStrategy):

    def __init__(self, massstart_time):
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

    def validate(self, obj):
        """Returns OK for every object. Override in subclasses for more meaningfull
        validations."""
        return ValidationStrategy.OK

class CourseValidationStrategy(ValidationStrategy):
    """Validation strategy for courses."""

    def __init__(self, course):
        self._course = course
        
    def validate(self, run):
        """Check if run is a valid run for this course. This only checks if the run
        is complete has a start punch and a finish punch. It does not check any controls!
        Override this in subclasses for more usefull validation (and call super() to not
        duplicate this code)."""
        if not run.complete:
            return ValidationStrategy.NOT_COMPLETED
        elif not run.finish():
            return ValidationStrategy.DID_NOT_FINISH
        else:
            return ValidationStrategy.OK

class SequenceCourseValidationStrategy(CourseValidationStrategy):
    """Validation strategy for a normal orienteering course."""
    
    def validate(self, run):
        """Validate the run if it is valid for this course."""

        valid = super(type(self), self).validate(run)
        if valid != ValidationStrategy.OK:
            return valid
        
        punchlist = run.punches.order_by('punchtime')
        controllist = [ i.control for i in self._course.sequence.order_by('sequence_number') ]
        # Iterate over all punches of this run
        i = 0
        for punch in punchlist:
            while i < len(controllist):
                if controllist[i].sistations.count() == 0:
                    # Control has no si-stations, got to next control
                    i += 1
                    continue
                elif controllist[i] is punch.sistation.control:
                    # This punch matches the control, got to next control and punch
                    i += 1
                    break
                else:
                    # Try next punch
                    break

        if i < len(controllist):
            # No more punches, but controls left
            return ValidationStrategy.MISSING_CONTROLS
        else:
            return ValidationStrategy.OK

class Relay24hScoreingStrategy(AbstractScoreingStrategy, ValidationStrategy):
    """This class is both a validation strategy and a scoreing strategy. The strategies
    are combined because they use some common private functions. This class validates
    and scores teams for the 24h relay."""

    def __init__(self, starttime):
        """
        @param starttime: Start time of the event.
        @type starttime:  datetime.datetime
        """
        self._starttime = starttime

    def _loop_over_runs(self, team):
        """This is an utility function to not duplicate code in _check_order and
        _omitted_runners. It loops over all runs, counts the omitted runners and
        checks the order. Returns a tuple
        (validation_code, number_of_omitted_runners)."""
        
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
                    return (ValidationStrategy.DISQUALIFIED, len(members)) 
                if next_runner >= len(remaining):
                    # wrap around
                    next_runner = 0
            next_runner  = (next_runner+1)%len(remaining)

        return (status, len(members) - len(remaining))

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

        # check runner order
        order = self._check_order(team)
        if not order == ValidationStrategy.OK:
            return order
                        
        # check run order
        # not cheked, this is ensured by proper event organisation :-)

        return ValidationStrategy.OK

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

        runs = team.runs
        run_scoreing_massstart = MassStartTimeScoreingStrategy(self._starttime)
        run_scoreing_relay = RelayTimeScoreingStrategy()
        
        failed = [ r for r in runs
                   if not r.course.validator(SequenceCourseValidationStrategy).validate(r) == ValidationStrategy.OK ]
        fail_penalty = timedelta(0)
        for f in failed:
            run_scoreing = f == runs[0] and run_scoreing_massstart or run_scoreing_relay
            penalty = f.course.expected_time() - run_scoreing.score(f)
            if penalty < timedelta(0):
                # no negative penalty
                penalty = timedelta(0)
            fail_penalty += penalty

        give_up_penalty = (self._omitted_runners(team)-1) * timedelta(minutes=30)
        
        finish_time = (self._starttime + timedelta(hours=24)
                       - fail_penalty - give_up_penalty)

        valid_runs = [ r for r in runs
                       if r.finish() < finish_time
                       and r.course.validator(SequenceCourseValidationStrategy).validate(r) == ValidationStrategy.OK ]
        
        return Relay24hScore(len(valid_runs),
                             max(valid_runs, key=lambda x: x.finish()).finish()
                             - self._starttime)

class Relay12hScoreingStrategy(Relay24hScoreingStrategy):
    """This class is both a valiadtion and a scoreing strategy. It implements the
    different validation algorithm of the 12h relay."""

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

        # run order is not checked yet
        return ValidationStrategy.OK

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

class UnscoreableException(Exception):
    pass

class ValidationError(Exception):
    pass
