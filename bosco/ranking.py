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
from traceback import print_exc
import sys, re

from storm.exceptions import NotOneError
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
    The order of the ranking is defined by the scoreing strategy. Strategy has the be
    a subclass of AbstractScoreing compatible with the RankableItem objects of this Rankable.
    The ranking is generated in lowest first order. Reverse rankings are possible.

    The iterator returns dictionaries with the keys 'rank', 'scoreing', 'validation',
    'item'.

    Rankings are lazyly computed, but not updated unless you eihter call the update mehtod
    or iterate over them.
    """

    def __init__(self, rankable, event, scoreing_class = None, validator_class = None,
                 scoreing_args = None, validator_args = None, reverse = False):
        self.rankable = rankable
        self._event = event
        self._scoreing_class = scoreing_class
        self._validator_class = validator_class
        self.scoreing_args = scoreing_args
        self.validator_args = validator_args
        self._reverse = reverse
        self._ranking_list = []
        self._ranking_dict = {}

        # lazy initialization flag
        self._initialized = False

    def __iter__(self):
        """
        Iterating over the ranking automatically updates the ranking. This is mainly for
        backwards compatibility.
        """

        def ranking_generator(ranking_list):
            for result in ranking_list:
                yield result

        self.update()
        # return the generator
        return ranking_generator(self._ranking_list)

    def __getitem__(self, key):
        if not self._initialized:
            self.update()

        return self._ranking_list[key]

    def rank(self, item):
        """
        @param item:  Item ranked in this ranking
        @return:      Rank of this item
        """
        return self.info(item)['rank']

    def score(self, item):
        """
        @param item: Item ranked in this ranking
        @return:     Score of this item
        """
        return self.info(item)['scoreing']['score']

    def info(self, item):
        """
        Return information dict for one item
        @param item: Item ranked in this ranking
        @return:     dict with all information about this item (same as when iterating
                     over the ranking)
        """
        # lazy initialization
        if not self._initialized:
            self.update()

        try:
            return self._ranking_dict[item]
        except KeyError:
            raise KeyError('%s not in ranking.' % item)

    @property
    def member_count(self):
        if not self._initialized:
            self.update()
        return self._member_count

    @property
    def completed_count(self):
        if not self._initialized:
            self.update()
        return self._completed_count

    def _update_ranking_list(self):
        # Create list of (score, member) tuples and sort by score
        self._ranking_list = []
        self._member_count = 0
        self._completed_count = 0

        # convert to a list for counting as it may either be
        # a strom result set or a real list
        if not len(list(self.rankable.members)) > 0:
            # stop if rankable has no members
            return

        for m in self.rankable.members:
            try:
                score = self._event.score(m, self._scoreing_class, self.scoreing_args)
            except UnscoreableException:
                score = {'score': timedelta(0)}
                
            try:
                valid = self._event.validate(m, self._validator_class, self.validator_args)
            except ValidationError:
                print_exc(file=sys.stderr)
                continue
                
            self._member_count += 1
            if valid['status'] != Validator.NOT_COMPLETED:
                self._completed_count += 1

            self._ranking_list.append({'scoreing': score,
                                       'validation': valid,
                                       'item': m})

        self._ranking_list.sort(key = lambda x: x['scoreing']['score'], reverse = self._reverse)
        self._ranking_list.sort(key = lambda x: x['validation']['status'])
        
        rank = 1
        winner_score = self._ranking_list[0]['scoreing']['score']
        for i, m in enumerate(self._ranking_list):
            # Only increase the rank if the current item scores higher than the previous item
            if (i > 0 and (self._ranking_list[i]['scoreing']['score']
                           > self._ranking_list[i-1]['scoreing']['score'])
                or (self._reverse and (self._ranking_list[i]['scoreing']['score']
                                       < self._ranking_list[i-1]['scoreing']['score']))):
                rank = i + 1
            # only assign rank if run is OK
            m['rank'] = rank if m['validation']['status'] == Validator.OK else None
            m['scoreing']['behind'] = ((m['scoreing']['score'] - winner_score) * (self._reverse and -1 or 1)
                                       if m['validation']['status'] == Validator.OK
                                       else None)

    def _update_ranking_dict(self):
        # create dictionary with ranked objects as keys for random access
        self._ranking_dict = {}
        for obj in self._ranking_list:
            self._ranking_dict[obj['item']] = obj
 
    def update(self):
        """
        Update the ranking. Rankings are not updated automatically.
        """
        self._update_ranking_list()
        self._update_ranking_dict()
        self._initialized = True

class RelayRanking(Ranking):

    def update(self):
        self._update_ranking_list()

        leg_rankings = {}
        for leg in self._event.list_legs(self.rankable):
            r = self._event.ranking(leg)
            leg_rankings.update([(k, r) for k in leg.course_list])

        # Relay rankings for splittimes
        split_rankings = []
        for i in range(len(self._event.list_legs(self.rankable))):
            # Don't use self._event.ranking here to avoid the infinite recursion this
            # would cause otherwise. Explicitly create a ranking without split rankings
            r = Ranking(self.rankable, self._event, scoreing_args = {'legs': i+1},
                        validator_args = {'legs': i+1})
            split_rankings.append(r)

        for team in self._ranking_list:
            team['runs'] = []
            team['splits'] = []
            for i, run in enumerate(team['scoreing']['runs']):
                if run:
                    team['runs'].append(leg_rankings[run.course].info(run))
                else:
                    team['runs'].append(None)
                team['splits'].append(split_rankings[i].info(team['item']))

        self._update_ranking_dict()
        self._initialized = True

class Rankable(object):
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

    def __delitem__(self, obj):
        if self._observer:
            self._observer.unregister(self, obj)
        del self._cache[obj]

    def __contains__(self, key):
        (obj, func) = key
        return obj in self._cache and func in self._cache[obj]

    def clear(self):
        self._cache = {}
        
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

class CachingObject(object):
    """Common parent class for all caching objects."""
    
    def __init__(self, cache = None):
        """
        @param cache: scoreing cache
        """
        self._cache = cache

    def _from_cache(self, func, obj):
        """
        Check cache and return cached result if it exists.
        @param func: function which produced the result
        @param obj:  Object of the startegy.
        @type obj:   object of class RankableItem
        @raises:     KeyError if object is not in the cache
        """
        if self._cache:
            return self._cache[(obj, func)]
        else:
            raise KeyError

    def _to_cache(self, func, obj, result):
        """
        Add result to cache
        @param func: function which produced the result
        @param obj:  Object of the startegy.
        @type obj:   object of class RankableItem
        """
        if self._cache:
            self._cache[(obj, func)] = result
        
    
class AbstractScoreing(CachingObject):
    """Defines a strategy for scoring objects (runs, runners, teams). The scoreing 
    strategy is tightly coupled to the objects it scores.

    Computed scores can (and should!) be stored in a cache.
    """

    def score(self, object):
        """Returns the score of the given objects. Throws UnscoreableException if the 
        object can't be scored with this strategy. The returned score must implement 
        __cmp__."""
        raise UnscoreableException('Can\'t score with AbstractScoreing')

    """
    descriptive string about the special parameters set for this
    Scoreing. Override if you have to pass additional information
    to rankings (and formatted rankings).
    string or None
    """
    information = None
    
class TimeScoreing(AbstractScoreing):
    """Builds the score from difference of start and finish times. The start time is
    calculated by the start time strategy object. The finish time is the time of the
    finish punch.
    Subclasses can override _start and _finish the extract the start and finsh times in
    other ways."""

    def __init__(self, starttime_strategy, cache = None):
        """
        @param start_time_strategy: Strategy to find the start time
        @type start_time_strategy:  object of class StartTimeStrategy or a subclass
        """
        AbstractScoreing.__init__(self, cache)
        self._starttime_strategy = starttime_strategy
    
    def _start(self, obj):
        """Returns the start time as a datetime object."""
        return self._starttime_strategy.starttime(obj)
    
    def score(self, obj):
        """Returns a timedelta object as the score by calling start and finish on 
        the object."""
        try:
            return self._from_cache(self.score, obj)
        except KeyError:
            pass

        result = {}
        result['start'] = self._start(obj)
        result['finish'] = obj.finish_time
        try:
            result['score'] = result['finish'] - result['start']
        except TypeError:
            # is this really the best thing to do?
            result['score'] = timedelta(0)

        if result['score'] < timedelta(0):
            raise UnscoreableException('Scoreing Error, negative runtime: %(finish)s - %(start)s = %(score)s'
                                       % result)
        
        self._to_cache(self.score, obj, result)
        return result

class Starttime(CachingObject):
    """Basic start time strategy. """
    
    def starttime(self, obj):
        return obj.manual_start_time

class SelfstartStarttime(Starttime):
    """StarttimeStrategy for Selfstart"""

    def starttime(self, obj):
        return obj.start_time

class MassstartStarttime(Starttime):
    """Returns start time relative to a fixed mass start time."""

    def __init__(self, starttime, cache = None):
        """
        @param starttime: Mass start time
        @type starttime:  datetime
        """
        
        CachingObject.__init__(self, cache)
        self._starttime = starttime
        
    def starttime(self, obj):
        start = Starttime.starttime(self, obj)
        if start:
            return start
        else:
            return self._starttime

class RelayStarttime(MassstartStarttime):
    """Returns start time computed from starttime == finish time of the previous runner
    in a relay team. If the computed time is later than the mass start time, the
    mass start time is returned."""

    def __init__(self, massstart_time, ordered = True, cache = None):
        """
        @param massstart_time: Time of the mass start
        @type massstart_time: datetime
        @param ordered:   If true this assumes that the runners follow in a
                          order defined by their number.
        @type ordered:    boolean
        """
        
        MassstartStarttime.__init__(self, massstart_time, cache)
        self._prev_finish = (ordered and self._prev_finish_ordered
                             or self._prev_finish_unordered)

    def _prev_finish_ordered(self, obj):

        from runner import RunnerException

        # Get the list of runners for this team
        try:
            runners = list(obj.sicard.runner.team.members.order_by('number'))
        except AttributeError:
            raise UnscoreableException("Runner must be part of a team!")

        i = runners.index(obj.sicard.runner)
        if i == 0:
            return None
        else:
            # this assumes that each runner runs only once, use unordered if this
            # is not the case
            try:
                return runners[i-1].run.finish_time
            except RunnerException, e:
                raise UnscoreableException(u'Unable to get finish time of previous runner: %s'
                                           % e.message) 
        
    def _prev_finish_unordered(self, obj):
        
        # Get the team for this run
        team = obj.sicard.runner.team

        # This makes the whole thing dependant on the exact database layout,
        # but it is a huge perfomance win
        from course import SIStation
        from run import Punch
        store = Store.of(obj)


        # get reference time (search for finish punch of the previous runner
        # before this time
        reftime = obj.finish_time
        if reftime is None:
            punchlist = [p for p,c in obj.punchlist()]
            if len(punchlist) == 0:
                # Assume this is the last run of this team
                reftime = datetime.max
            else:
                # last real punch of this run
                reftime = obj.punchlist()[-1][0].punchtime
        
        prev_finish = store.execute(
            """SELECT MAX(COALESCE(run.manual_finish_time, run.card_finish_time))
                  FROM team JOIN runner ON team.id = runner.team
                     JOIN sicard ON runner.id = sicard.runner
                     JOIN run ON sicard.id = run.sicard
                  WHERE team.id = %s
                     AND COALESCE(run.manual_finish_time, run.card_finish_time) < %s
                     AND run.complete = true""",
#            """SELECT MAX(COALESCE(run.manual_finish_time, run.card_finish_time))
#                  FROM team JOIN runner ON team.id = runner.team
#                     JOIN sicard ON runner.id = sicard.runner
#                     JOIN run ON sicard.id = run.sicard
#                  WHERE team.id = (SELECT runner.team
#                                      FROM run
#                                         JOIN sicard ON run.sicard = sicard.id
#                                         JOIN runner ON sicard.runner = runner.id
#                                      WHERE run.id = %s)             
#                     AND COALESCE(run.manual_finish_time, run.card_finish_time) < %s
#                     AND run.complete = true""",
#            params = (obj.id,
            params = (team.id,
                      reftime,
                      )
            ).get_one()[0]

        return prev_finish

    def starttime(self, obj):
        start = Starttime.starttime(self, obj)
        if start:
            return start
        
        prev_finish = self._prev_finish(obj)
        if prev_finish is None:
            return self._starttime
        else:
            return prev_finish

class RelayMassstartStarttime(RelayStarttime):
    
    def starttime(self, obj):
        start = Starttime.starttime(self, obj)
        if start:
            return start
        
        prev_finish = self._prev_finish(obj)
        if prev_finish is None:
            return self._starttime
        else:
            return self._starttime < prev_finish and self._starttime or prev_finish

class Validator(CachingObject):
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
        return {'status':Validator.OK}

class CourseValidator(Validator):
    """Validation strategy for courses."""

    def __init__(self, course, cache = None):
        Validator.__init__(self, cache)
        self._course = course
        
    def validate(self, run):
        """Check if run is a valid run for this course. This only checks if the run
        is complete has a start punch and a finish punch. It does not check any controls!
        Override this in subclasses for more usefull validation (and call super() to not
        duplicate this code)."""
        try:
            return self._from_cache(self.validate, run)
        except KeyError:
            pass

        result = {'override':False}
        if run.override is not None:
            if run.override == Validator.OK and run.complete == False:
                # return not completed even if override is OK to avoid inconsistencies
                result['status'] = Validator.NOT_COMPLETED
            else:
                result['status'] =  run.override
            result['override'] = True
        elif not run.complete:
            result['status'] = Validator.NOT_COMPLETED
        elif not run.finish_time:
            result['status'] =  Validator.DID_NOT_FINISH
        else:
            result['status'] = Validator.OK

        # add all punches to punchlist
        result['punchlist'] = [ ('ok', p[0]) for p in run.punchlist() ]
        result['punchlist'].extend([ ('ignored', p[0]) for p in run.punchlist(ignored=True) ])

        self._to_cache(self.validate, run, result)
        return result

class SequenceCourseValidator(CourseValidator):
    """Validation strategy for a normal orienteering course.
    This class uses a dynamic programming "longest common subsequence"
    algorithm to validate the run and find missing and additional punches.
    @see http://en.wikipedia.org/wiki/Longest_common_subsequence_problem.
    """

    def __init__(self, course, cache = None):

        CourseValidator.__init__(self, course, cache)
        
        # list of all controls which have sistations
        self._controllist = self._course.controllist()

    @staticmethod
    def _exact_match(plist, clist):
        """check if plist exactly matches clist
        @param plist: list of punches
        @param clist: list of controls. All controls with no sistations or which are
                      overriden must be removed!
        @return:      True or False
        """
        if len(plist) != len(clist):
            return False
        
        for i,c in enumerate(clist):
            if not plist[i][1] is c:
                return False

        return True
            
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
            return SequenceCourseValidator._backtrack(C, plist, clist, i-1, j-1) + [ clist[j-1] ]
        else:
            if C[i][j-1] > C[i-1][j]:
                return SequenceCourseValidator._backtrack(C, plist, clist, i, j-1)
            else:
                return SequenceCourseValidator._backtrack(C, plist, clist, i-1, j)
        
    @staticmethod
    def _diff(C, plist, clist, i = None, j = None):
        """
        @return: list of (status, punch or control) tuples. status is 'ok', 'additional' or
                 'missing' or '' (for special SIStations)
        """

        from course import SIStation
        
        if i is None:
            i = len(plist)
        if j is None:
            j = len(clist)
            
        if i > 0 and j > 0 and plist[i-1][1] is clist[j-1]:
            result_list = SequenceCourseValidator._diff(C, plist, clist, i-1, j-1)
            result_list.append(('ok',plist[i-1][0]))
        else:
            if j > 0 and (i == 0 or C[i][j-1] >= C[i-1][j]):
                result_list = SequenceCourseValidator._diff(C, plist, clist, i, j-1)
                result_list.append(('missing', clist[j-1]))
            elif i > 0 and (j == 0 or C[i][j-1] < C[i-1][j]):
                result_list = SequenceCourseValidator._diff(C, plist, clist, i-1, j)
                result_list.append(((plist[i-1][0].sistation.id > SIStation.SPECIAL_MAX
                                     and 'additional'
                                     or ''),
                                    plist[i-1][0]))
            else:
                result_list = []
        return result_list
                
    def validate(self, run):
        """Validate the run if it is valid for this course."""

        try:
            return self._from_cache(self.validate, run)
        except KeyError:
            pass

        from course import SIStation

        # do basic checks from CourseValidator
        result = super(type(self), self).validate(run)
        
        punchlist = run.punchlist()

        if SequenceCourseValidator._exact_match(punchlist, self._controllist):
            diff_list = [('ok', p[0]) for p in punchlist]
        else:
            C = SequenceCourseValidator._build_lcs_matrix(punchlist, self._controllist)
            diff_list = SequenceCourseValidator._diff(C,
                                                      punchlist,
                                                      self._controllist)

        # add ignored and special punches into diff_list
        ignorelist = run.punchlist(ignored=True)
        i = 0
        for p,c in ignorelist:
            while i < len(diff_list):
                if (diff_list[i][0] == 'missing'
                    or p.punchtime > diff_list[i][1].punchtime):
                    i += 1
                else:
                    break
            diff_list.insert(i, ('ignored', p))
            
        if result['status'] == Validator.OK and result['override'] is False:
            if 'missing' in dict(diff_list):
                result['status'] = Validator.MISSING_CONTROLS

        result['punchlist'] = diff_list
            
        self._to_cache(self.validate, run, result)
        return result

class AbstractRelayScoreing(AbstractScoreing, Validator):
    """Base class for all relay scoreing classes. This class contains some
    common mehtods used in relay scoreing.
    """

    def __init__(self, event, cache = None):
        AbstractScoreing.__init__(self, cache)
        self._event = event
        
    def _runs(self, team):
        """
        Return a sorted list of all completed runs of a team that have a course out of a given set.
        @return: dict with the following keys:
                 * finish:        finish time of the run
                 * runner:        runner id of the run
                 * course:        course of the run
                 * validation:    validation code
                 * lkm:           lkm run on this code
                 * score:         score of the run
                 * expected_time: expected time of the run
        """
        try:
            return self._from_cache(self._runs, team)
        except KeyError:
            runs = []
            for r in team.runs:
                if r.complete is False:
                    continue
                if r.course is None:
                    continue
                if not r.course.code in self._courses:
                    continue
                runs.append( {'finish':r.finish_time,
                              'runner':r.sicard.runner.id,
                              'course':r.course.code,
                              'validation':self._event.validate(r)['status']})
                if runs[-1]['validation'] == Validator.OK:
                    runs[-1]['lkm'] = r.course.lkm()
                else:
                    runs[-1]['score'] = self._event.score(r)['score']
                    runs[-1]['expected_time'] = r.course.expected_time(self._speed)
                
            runs.sort(key=lambda x:x['finish'] or datetime.max)
            self._to_cache(self._runs, team, runs)
            return runs

class RelayScoreing(AbstractRelayScoreing):
    """Combined validator and scoreing class for relay teams. This
    class validates and scores teams in a classical relay with
    different legs and a fixed order of the legs. It supports optional
    legs with a default time if the leg is not run successfully or if
    a runner runs longer than the default time. It also supports
    multiple course variants for a leg."""

    def __init__(self, legs, event, cache=None):
        """
        @param legs: list of dicts with the following keys:
                     * 'variants': tuple of course codes that are valid variants for this leg.
                     * 'starttime': start time for all non replaced runners, type datetime
                     * 'defaulttime': time scored if no runner of the team successfully
                       completes this leg or if the runner on this legs needs more time than
                       the defaulttime, type timedelta or None if there is no defaulttime
        @type legs:  dict
        @param event: Event object used to validate and score individual runs.
        @type event:  instance of a class derived from Event
        """
        super(RelayScoreing, self).__init__(event,cache)
        self._legs = legs
        self._speed = 0
        self._courses = []
        for l in self._legs:
            self._courses.extend(l['variants'])

    def _runs(self, team):
        """
        Return a list of all completed runs for this team. Ordered by leg. If there is
        no run for a leg the list contains None at this index. If there is more than one run for
        a leg the result is undefined.
        @type team: instance of Team
        @return type: list of runs
        """
        try:
            return self._from_cache(self._runs, team)
        except KeyError:
            pass

        runs =  dict([(r.course.code, r) for r in team.runs
                      if r.course is not None and r.complete])
        
        result = []
        for l in self._legs:
            for v in l['variants']:
                if v in runs.keys():
                    result.append(runs[v])
                    break
            else:
                # no valid run for this leg
                result.append(None)

        self._to_cache(self._runs, team, result)
        return result
        
    def validate(self, team):
        """Validates a relay team.
        @see: Validator
        """
        try:
            return self._from_cache(self.validate, team)
        except KeyError:
            pass

        from runner import RunnerException

        result = {'override':False}
        # check for override
        if team.override is not None:
            result['status'] = team.override
            result['override'] = True
        else:
            runners = team.members.order_by('number')
            i = 0
            for l in self._legs:
                try:
                    run = runners[i].run
                except IndexError:
                    # no more runners in team
                    if l['defaulttime'] is not None:
                        # the status remains the same
                        continue
                    else:
                        result['status'] = Validator.DISQUALIFIED
                        break
                except RunnerException: 
                    # no run or multiple runs for this runner
                    if l['defaulttime'] is not None:
                        i += 1
                        continue
                    else:
                        result['status'] = Validator.DISQUALIFIED
                        break

                try:
                    code = run.course.code
                except AttributeError:
                    # run does not have a course
                    result['status'] = Validator.DISQUALIFIED
                    break
            
                valid = self._event.validate(run)['status']
                if code in l['variants'] and (l['defaulttime'] is not None or valid == Validator.OK):
                    # everything is OK
                    i += 1
                    continue
                elif l['defaulttime'] is not None:
                    # perhaps missing runner, just continue without increasing the runner index
                    continue
                elif code in l['variants']:
                    # correct course, but not valid
                    result['status'] = valid
                    break
                else:
                    # wrong course
                    result['status'] = Validator.DISQUALIFIED
                    break
                
            if not 'status' in result:
                # if no status is assigned everything is OK
                result['status'] = Validator.OK

        self._to_cache(self.validate, team, result)
        return result

    def score(self, team):
        """Score a relay team.
        @see: AbstractScoreing
        """
        
        try:
            return self._from_cache(self.score, team)
        except KeyError:
            pass

        time = timedelta(0)

        # compute sum of individual run times
        # this automatically takes mass starts into account

        runs = self._runs(team)
        for i,l in enumerate(self._legs):
            default = l['defaulttime']

            if runs[i] is not None and self._event.validate(runs[i])['status'] == Validator.OK:
                # We have a valid run
                legscore = self._event.score(runs[i])['score']
                if default is None or  legscore < default:
                    time += legscore
                else:
                    time += default
            else:
                # No run on this leg
                if default is None:
                    # But we should have a run, set score to 0
                    # and stop processing
                    time = timedelta(0)
                    break
                else:
                    time += default
                
        # if len(runs) == 0:
        #     raise UnscoreableException(u'Unable to score team %s (%s): no '
        #                                u'valid run.' %
        #                                (team.name, team.number))
        # missing = 0 # count of missing legs
        # legs = []
        # valid = True
        # for i,l in enumerate(self._legs):
        #     default = l['defaulttime']
        #     try:
        #         r = runs[i-missing]
        #     except IndexError:
        #         # last run is missing
        #         # check for incomplete run for this leg
        #         incomplete = False
        #         for run in [r for r in team.runs if r.complete == False]:
        #             if run.course.code in l['variants']:
        #                 incomplete = True
        #                 break
        #             if default is None or incomplete:
        #                 # missing run for this leg and no default time
        #                 # continue scoreing to get leg info 
        #                 valid = False
        #         else:
        #             time += default
        #             legs.append(None)
                
        #     if r.course.code not in l['variants']:
        #         # missing leg
        #         missing += 1
        #         if default is None:
        #             valid = False
        #         else:
        #             time += default
        #             legs.append(None)
        #     else:
        #         legscore = self._event.score(r)['score']
        #         legs.append(r)
        #         if default is None or  legscore < default:
        #             time += legscore
        #         else:
        #             time += default

        # if not valid:
        #     time = timedelta(0)

        result = {'score': time,
                  'runs':  runs}

        self._to_cache(self.score, team, result)
        return result
    
class Relay24hScoreing(AbstractRelayScoreing):
    """This class is both a validation strategy and a scoreing strategy. The strategies
    are combined because they use some common private functions. This class validates
    and scores teams for the 24h relay."""

    START   = re.compile('^SF[1-4]$')
    NIGHT   = re.compile('^[LS][DE]N[1-5]$')
    DAY     = re.compile('^[LS][DE][1-4]$')
    FINISH  = re.compile('^FF[1-6]$')

    POOLNAMES = ['start','night', 'day','finish']
    
    def __init__(self, starttime, speed, duration, event, method = 'runcount',
                 blocks = 'finish', cache = None):
        """
        @param starttime:     Start time of the event.
        @type starttime:      datetime.datetime
        @param speed:         expected speed in minutes per kilometers. Used to compute
                              penalty time for invalid runs
        @type speed:          int
        @param event:         object of class Event to score and
                              validate single runs
        @param duration:      Duration of the event
        @param method:        score calculation method, currently implemented:
                              runcount: count valid runs
                              lkm: sum of lkms of all valid runs
        @type method:         str
        @param blocks:        score until the end of this block. Possible blocks:
                              'start', 'night', 'day', 'finish' (default)
        """
        AbstractRelayScoreing.__init__(self, event, cache)
        self._starttime = starttime
        self._speed = speed
        self._duration = duration
        self._method = method

        self._courses = []
        all_courses = self._event.list_courses()
        if blocks in self.POOLNAMES:
            self._courses.extend([ c.code for c in all_courses
                                   if self.START.match(c.code) ])
        if blocks in self.POOLNAMES[1:]:
            self._courses.extend([ c.code for c in all_courses
                                   if self.NIGHT.match(c.code) ])
        if blocks in self.POOLNAMES[2:]:
            self._courses.extend([ c.code for c in all_courses
                                   if self.DAY.match(c.code) ])
        if blocks in self.POOLNAMES[3:]:
            self._courses.extend([ c.code for c in all_courses
                                   if self.FINISH.match(c.code) ])

        self._pool = [[ c for c in self._courses if self.START.match(c) ],
                      [ c for c in self._courses if self.NIGHT.match(c) ],
                      [ c for c in self._courses if self.DAY.match(c) ],
                      ]

        self._blocks = blocks

    def _loop_over_runs(self, team):
        """This is an utility function to not duplicate code in _check_order and
        _omitted_runners. It loops over all runs, counts the omitted runners and
        checks the order. Returns a tuple
        (validation_code, number_of_omitted_runners)."""

        # try fetching from cache
        try:
            return self._from_cache(self._loop_over_runs, team)
        except KeyError:
            pass
        
        # collect team members and runs
        members = [ r.id for r in  team.members.order_by('number')]
        runs = self._runs(team)
        
        # check runner order
        remaining = copy(members)
        next_runner = 0
        status = Validator.OK
        for i,r in enumerate(runs):
            while not r['runner'] == remaining[next_runner]:
                if i < len(members):
                    # not every runner has run at least once
                    status = Validator.DISQUALIFIED
                # next_runner gave up -> delete
                del(remaining[next_runner])
                # any runners left?
                if len(remaining) == 0:
                    status = Validator.DISQUALIFIED
                    break
                if next_runner >= len(remaining):
                    # wrap around
                    next_runner = 0
                    
            if len(remaining) == 0:
                break
            
            next_runner  = (next_runner+1)%len(remaining)

        result = (status, len(members) - len(remaining))

        # save to cache and return result
        self._to_cache(self._loop_over_runs, team, result)
        return result

    def _check_order(self, team):
        """Checks if the order of the runners is correct."""
        return self._loop_over_runs(team)[0]
        
    def _omitted_runners(self, team):
        """Count the runners that were omitted during the event and gave up."""
        return self._loop_over_runs(team)[1]

    def _check_pools(self, team):
        # check for pool completion

        # make semi-deep copy of self._pool, it will be modified!
        pool = [ copy(p) for p in self._pool ]

        i = 0
        runs = self._runs(team)
        remaining_runs = copy(runs)
        for r in runs:
            while i <= 2 and len(pool[i]) == 0:
                # pool finished
                i += 1

            if i > 2:
                # all pools finished
                break

            try:
                pool[i].remove(r['course'])
                remaining_runs.remove(r)
            except ValueError:
                return {'status': Validator.DISQUALIFIED,
                        'unfinished pool': self.POOLNAMES[i],
                        'run': r['course']}
                    

        # check for proper order of finish courses
        finish_pool = [ c for c in self._courses if self.FINISH.match(c) ]
        finish_pool.sort()
        for i,c in enumerate(finish_pool):
            if i >= len(remaining_runs):
                # no more runs
                break
            
            if c != remaining_runs[i]['course']:
                return {'status': Validator.DISQUALIFIED,
                        'unfinished pool': self.POOLNAMES[3],
                        'run': remaining_runs[i]['course']}

        return {'status': Validator.OK}
    
    def validate(self, team):
        """Validate the runs of this team according to the rules
        of the 24h orienteering event.
        The following rules apply:
          - runners must run in the defined order, omitted runners may not
            run again
          - every runner must run at least once at the beginning of the event
          - runs must be run in the following order:
            - 4 start courses (Codes SF1-4), fixed order defined for each
              team
            - night courses (Codes LDNx, LENx, SDNx, SENx), free order
              choosen by team
            - day courses (Codes LDx, LEx, SDx, SEx), free order
              choosen by team
            - 6 finish courses (Codes FF1-6), same order for each team"""

        try:
            return self._from_cache(self.validate, team)
        except KeyError:
            pass

        result = {'override':False}
        # check for override
        if team.override is not None:
            result['status'] = team.override
            result['override'] = True
        else:
            # check runner order
            result['status'] = self._check_order(team)
            if result['status'] == Validator.OK:
                result = self._check_pools(team)
            else:
                result['runner order'] =  False
            
        result['information'] = {'blocks': self._blocks}
        self._to_cache(self.validate, team, result)
        return result

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
            return self._from_cache(self.score, team)
        except KeyError:
            pass
        
        runs = self._runs(team)
        
        failed = []
        for r in runs:
            status = r['validation']
            if status in [Validator.MISSING_CONTROLS,
                          Validator.DID_NOT_FINISH,
                          Validator.DISQUALIFIED]:
                failed.append(r)
                
        fail_penalty = timedelta(0)
        for f in failed:
            penalty = (f['expected_time']
                       - f['score'])
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

        valid_runs  = [ r for r in runs
                        if r['validation'] == Validator.OK
                        and r['finish'] <= finish_time]

        if len(valid_runs) > 0:
            runtime = max(valid_runs, key=lambda x: x['finish'])['finish'] - self._starttime
        else:
            runtime = timedelta(0)
            
        if self._method == 'runcount':
            result = Relay24hScore(len(valid_runs),runtime)
        elif self._method in ['lkm', 'speed']:
            lkm = 0
            for r in valid_runs:
                lkm += r['lkm']
            if self._method == 'lkm':
                result = Relay24hScore(lkm, runtime)
            elif self._method == 'speed':
                result = lkm > 0 and Relay24hScore((runtime.seconds/60.0)/lkm, runtime) or Relay24hScore(0, runtime)
        else:
            raise UnscoreableException("Unknown scoreing method '%s'." % self._method)
        
        ret = {'score':result,
               'finishtime': finish_time,
               'information': {'method': self._method,
                               'blocks': self._blocks},
               }
        self._to_cache(self.score, team, ret)
        return ret

class Relay12hScoreing(Relay24hScoreing):
    """This class is both a valiadtion and a scoreing strategy. It implements the
    different validation algorithm of the 12h relay."""

    START   = re.compile('^SF[1-2]$')
    NIGHT   = re.compile('^$')
    DAY     = re.compile('^[LS][DE][1-4]$')
    FINISH  = re.compile('^FF[1-2]$')

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
            - 2 start course (Code SF1-2), individually for each team
            - day courses (Codes LDx, LEx, SDx, SEx), free order
              choosen by team
            - 2 finish courses (Codes FF1-2), same order for each team"""

        try:
            return self._from_cache(self.validate, team)
        except KeyError:
            pass
        
        # only check pools
        result = self._check_pools(team)

        result['information'] = {'blocks':self._blocks}
        
        self._to_cache(self.validate, team, result)
        return result

class Relay24hScore(object):

    def __init__(self, runs, time):
        self.runs = runs
        self.time = time

    def __cmp__(self, other):
        """compares two Relay24hScore objects."""
        
        if self.runs > other.runs:
            return -1
        elif self.runs < other.runs:
            return 1
        else:
            if self.time < other.time:
                return -1
            elif self.time > other.time:
                return 1
            else:
                return 0

    def __sub__(self, other):
        """Subtracts Relay24hScore objects. This is mainly usefull to calculate
        differences between teams."""
        return Relay24hScore(self.runs - other.runs, self.time - other.time)

    def __mul__(self, other):
        """Multiplication of Relay24hScore objects. This is to theoretically allow
        reverse Rankings (behind score multiplied by -1).
        """
        return Relay24hScore(self.runs * other, self.time * other)

    def __str__(self):
        return "Runs: %s, Time: %s" % (self.runs, self.time) 

class ControlPunchtimeScoreing(AbstractScoreing, Validator):
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
        AbstractScoreing.__init__(self, cache)
        self._controls = control_list
        self._distance_to_finish = distance_to_finish

    def validate(self, run):
        """
        @return: Validator.OK if the control was punched,
                 Validator.NOT_COMPLETED if the control was not yet punched
        """
        try:
            return self._from_cache(self.validate, run)
        except KeyError:
            pass

        punchlist = [c for p,c in run.punchlist()]
        result = Validator.NOT_COMPLETED
        for c in self._controls:
            if c in punchlist:
                result = Validator.OK
                break
        
        ret = {'status': result}
        self._to_cache(self.validate, run, ret)
        return ret

    def score(self, run):
        """
        @return: time of the punch or datetime.min if punchtime is unknown.
                 If more than one of the control was punched, the punchtime
                 of the first in the list is returned.
        """
        try:
            return self._from_cache(self.score, run)
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

        ret = {'score':result}
        self._to_cache(self.score, run, ret)
        return ret
    
class RoundCountScoreing(AbstractScoreing, CourseValidator):
    """This scoreing strategy computes the score as the count of complete runs of a course.
    This is mostly usefull for non orienteering events where runners have to run as much rounds
    as possible in a predifined time intervall.
    Be aware that SI Card 5 and SI Card 8 only hold 30 punches!

    This is a combined validator and scoreing strategy.
    """

    def __init__(self, course, mindiff = timedelta(0), cache = None):
        """
        @param course  Course object with all controls on the roundcourse. In the simplest case
                       this course has only 1 control.
        @param mindiff Minimal time difference between valid punches. This is necessary to avoid
                       counting two runs if runners punch the only control of the course two times
                       without running the round in between.
        @type mindiff  timedelta
        """
        super(RoundCountScoreing, self).__init__(cache)
        self._course = course
        self._mindiff = mindiff

        # list of all controls which have sistations
        self._controllist = self._course.controllist()

    def validate(self, run):

        try:
            return self._from_cache(self.validate, run)
        except KeyError:
            pass

        # do basic checks from CourseValidator
        result = CourseValidator.validate(self, run)

        result['score'] = 0
        i = 0
        lastpunch = None
        punchlist = []
        for code, punch in result['punchlist']:

            if not code == 'ok':
                punchlist.append((code, punch))
                continue

            if (not punch.sistation.control
                or punch.sistation.control not in self._controllist):
                punchlist.append(('ignored', punch))
                continue

            if lastpunch and punch.punchtime - lastpunch < self._mindiff:
                # additional punch for same round
                punchlist.append(('additional', punch))
                continue

            if punch.sistation.control is self._controllist[i]:
                lastpunch = punch.punchtime
                i += 1
                punchlist.append(('ok', punch))

            if i == len(self._controllist):
                # round completed
                result['score'] += 1
                i = 0

        result['punchlist'] = punchlist
        self._to_cache(self.validate, run, result)
        return result

    def score(self, run):

        return self.validate(run)

class UnscoreableException(Exception):
    pass

class ValidationError(Exception):
    pass
