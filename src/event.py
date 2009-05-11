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
event.py - Event configuration. All front-end programs should use
           conf.event which is a subclass of Event
"""

from datetime import timedelta

from course import Course
from runner import Category
from ranking import (SequenceCourseValidator, TimeScoreing, SelfstartStarttime,
                     RelayStarttime, RelayMassstartStarttime,
                     Ranking, CourseValidator, OpenRuns,
                     ControlPunchtimeScoreing,
                     Relay24hScoreing, Relay12hScoreing, RelayValidator,
                     ValidationError, UnscoreableException)

from formatter import MakoRankingFormatter

class Event(object):
    """Model of all event specific ranking information. The default
    implementation uses SequenceCourseValidator, TimeScoreing and SelfstartStarttime.
    Subclass this class to customize your event."""

    def __init__(self, header = {}, extra_rankings = [],
                 template_dir = 'templates',
                 print_template = 'course.tex', html_template = 'course.html',
                 cache = None, store = None):
        """
        @param header:         gerneral information for the ranking header.
                               Typical keys:
                               'organiser', 'map', 'place', 'date', 'event'
        @type header:          dict of strings
        @param extra_rankings: list of extra rankings
        @type extra_rankings:  list of tuples (description (string), ranking_args),
                               ranking_args is a dicts with keys for the
                               ranking method:
                               'rankable', 'scoreing_class',
                               'validation_class', 'scoreing_args', 'validation_args',
                               'reverse',
        @param template_dir:   templates directory
        @param print_template: template for printing (latex)
        @param html_template:  template for html output (screen display)
        @param cache:          Cache to use for this object
        @param store:          Store to retrieve possible rankings
        """
        
        self._strategies = {}
        self._cache = cache
        self._header = header
        self._extra_rankings = extra_rankings
        self._template_dir = template_dir
        self._template = {}
        self._template['print'] = print_template
        self._template['html'] = html_template
        self._store = store

    @staticmethod
    def _key(cls, args):
        """make a hashable key out of cls and args"""
        
        arg_list = []
        for k,v in args.items():
            if type(v) == list:
                v = tuple(v)
            arg_list.append((k, v))
        return (cls, tuple(arg_list))

    def remove_cache(self):
        """Removes the cache. No caching occurs anymore."""
        self._cache = None
        self._strategies = {}

    def clear_cache(self, obj = None):
        """
        Clear the cache
        @param obj: Only clear the cache for obj
        """
        if obj is not None:
            self._cache.update(obj)
        else:
            self._cache.clear()
        
    def validate(self, obj, validator_class = None, args = None):
        # Don't define args={}, default arguments are created at function definition time
        # and you would end up modifing the default args below! You must create a new
        # empty dictionary on every invocation!
        
        """
        Get a validator
        @param obj:             object to validate, 
        @param validator_class: validation class used
        @param args:            dict of keyword arguments for the validation strategy object
        @return:                validation result from validator_class.validate(obj)
        @see:                   Validator for more information about validation classes
        """
        
        from run import Run
        from runner import Runner

        if obj is None:
            raise ValidationError("Can't validate objects of type %s" % type(obj))
        
        if validator_class is None:
            validator_class = SequenceCourseValidator
            
        if args is None:
            args = {}
            
        if 'cache' not in args:
            args['cache'] = self._cache
            
        if issubclass(validator_class, CourseValidator):
            if type(obj) == Runner:
                # validate run of this runner
                obj = obj.run

            if type(obj) == Run and 'course' not in args:
                if obj.course is None:
                    raise ValidationError("Can't validate run without course")
                args['course'] = obj.course

        if self._key(validator_class, args) not in self._strategies:
            # create validator instance
            self._strategies[self._key(validator_class, args)] = validator_class(**args)

        return self._strategies[self._key(validator_class, args)].validate(obj)
    
    def score(self, obj, scoreing_class = None, args = None):
        """
        Get the score of an object
        @param obj:            object to score
        @param scoreing_class: scoreing strategy used
        @param args:           additional arguments for the scoreing class's constructor
        @type args:            dict of keyword arguments
        @return:               scoreing result from scoreing_class.score(obj)
        @see:                  AbstractScoreing for more information about scoreing classes
        """

        from runner import Runner
        
        if obj is None:
            raise UnscoreableException("Can't score objects of type %s" % type(obj))
        
        if args is None:
            args = {}

        if not 'cache' in args:
            args['cache'] = self._cache

        if scoreing_class is None:
            scoreing_class = TimeScoreing
            if 'starttime_strategy' not in args:
                args['starttime_strategy'] = SelfstartStarttime(args['cache'])
                
        if self._key(scoreing_class, args) not in self._strategies:
            # create scoreing instance
            if not 'cache' in args:
                args['cache'] = self._cache
            self._strategies[self._key(scoreing_class, args)] = scoreing_class(**args)

        if type(obj) == Runner:
            # Score run of this runner
            obj = obj.run
            
        return self._strategies[self._key(scoreing_class, args)].score(obj)

    def ranking(self, obj, scoreing_class = None, validation_class = None,
                scoreing_args = None, validation_args = None, reverse = False):
        """
        Get a ranking for a Rankable object
        @param obj:              ranked object (Category, Course, ...)
        @param scoreing_class:   scoreing strategy used, None for default strategy
        @param validation_class: validation strategy used, None for default strategy
        @param scoreing_args:    scoreing args, None for default args
        @param validation_args:  validation args, None for default args
        @param reverse:          produce reversed ranking
        """

        if type(obj) == OpenRuns:
            scoreing_class = scoreing_class or ControlPunchtimeScoreing
            validation_class = validation_class or ControlPunchtimeScoreing
            validation_args = validation_args or scoreing_args
            reverse = True
            
        return Ranking(obj, self, scoreing_class, validation_class,
                       scoreing_args, validation_args, reverse)

    def format_ranking(self, rankings, type = 'html'):
        """
        @param ranking: Rankings to format
        @type ranking:  list of objects of class Ranking
        @param type:    'html' (default) or 'print'
        @return:        RankingFormatter object for the ranking
        """

        return MakoRankingFormatter(rankings, self._header,
                                    self._template[type], self._template_dir)
    def list_rankings(self):
        """
        @return: list of possible rankings
        """
        l = [ (c.code, self.ranking(c)) for c in self._store.find(Course)]
        l.extend([ (e[0], self.ranking(**e[1])) for e in self._extra_rankings ])
        l.sort(key = lambda x: x[0])
        return l

    def list_courses(self):
        """
        @return: list of all courses in the event 
        """
        return list(self._store.find(Course))

    def list_categories(self):
        """
        @return: list of all categories in the event
        """
        return list(self._store.find(Category))
    
class RelayEvent(Event):
    """Event class for a traditional relay."""

    def __init__(self, legs, header={}, extra_rankings=[],
                 template_dir = 'templates',
                 print_template = 'relay.tex',
                 html_template = 'relay.html',
                 cache = None, store = None):
        """
        @param legs: list of (legcode, startime) tuples
        @see:        Event for other arguments
        """

        Event.__init__(self, header, extra_rankings, template_dir, print_template,
                       html_template, cache, store)

        self._starttimes = dict(legs)
        
    def validate(self, obj, validator_class = None, args = None):

        from runner import Team
        
        if type(obj) == Team and validator_class is None:
            validator_class = RelayValidator

        return Event.validate(self, obj, validator_class, args)

    def score(self, obj, scoreing_class = None, args = None):
        """
        @args: for a team the key 'legs' specifies to score after
               this leg number (starting from 1).
        @see:  Event
        """

        from runner import Team
        from run import Run

        if args is None:
            args = {}

        if not 'cache' in args:
            args['cache'] = self._cache
            
        if type(obj) == Run and scoreing_class is None:
            if obj.course is None:
                raise UnscoreableException("Can't score a relay leg without a course.")
            scoreing_class = TimeScoreing
            args['starttime_strategy'] = RelayMassstartStarttime(self._starttimes[obj.course.code], args['cache'])
        elif type(obj) == Team and scoreing_class is None:
            if not 'legs' in args:
                args['legs'] = len(self._startimes)
            time = timedelta(0)
            # compute sum of individual run times
            # this automatically takes mass starts into account
            for i, r in enumerate(obj.runners.order_by('number')):
                if not i < args['legs']:
                    break
                time += self.score(r)
                
            return {'score':time}
            
        return Event.score(self, obj, scoreing_class, args)

#    def ranking(self, obj):
#        pass
    
    def list_rankings(self):
        l = Event.list_rankings(self)
        return l
    
class Relay24hEvent(Event):
    """Event class for the 24h orientieering relay."""

    def __init__(self, starttime_24h, starttime_12h, speed,
                 header = {},
                 duration_24h = timedelta(hours=24),
                 duration_12h = timedelta(hours=12),
                 extra_rankings = [],
                 template_dir = 'templates',
                 print_template = '24h.tex',
                 html_template = '24h.html',
                 cache = None, store = None):
        
        Event.__init__(self, header, extra_rankings, template_dir, print_template,
                       html_template,
                       cache, store)

        self._starttime = {u'24h':starttime_24h,
                           u'12h':starttime_12h}
        self._speed     = speed
        self._duration  = {u'24h':duration_24h,
                           u'12h':duration_12h}
        self._strategy  = {u'24h':Relay24hScoreing,
                           u'12h':Relay12hScoreing}
        
    def _get_team_strategy(self, team, args):
        cat =  team.category.name
        args['event_ranking'] = self
        if 'starttime' not in args:
            args['starttime'] = self._starttime[cat]
        if 'speed' not in args:
            args['speed'] = self._speed
        if 'duration' not in args:
            args['duration'] = self._duration[cat]
        return (self._strategy[cat], args)

    def _get_run_strategy(self, run, args):
        try:
            cat = run.sicard.runner.team.category.name
        except AttributeError:
            return (None, args)
        
        if 'starttime_strategy' not in args:
            args['starttime_strategy'] = RelayStarttime(self._starttime[cat],
                                                        ordered = False,
                                                        cache = self._cache)
        return (TimeScoreing, args)
        
    def validate(self, obj, validator_class = None, args = None):

        from runner import Team

        if args is None:
            args = {}
        
        if type(obj) == Team and validator_class is None:
            (validator_class, args) = self._get_team_strategy(obj, args)

        return Event.validate(self, obj, validator_class, args)
            

    def score(self, obj, scoreing_class = None, args = None):

        from runner import Team
        from run import Run
        
        if args is None:
            args = {}
            
        if type(obj) == Team and scoreing_class is None:
            (scoreing_class, args) = self._get_team_strategy(obj, args)
        elif type(obj) == Run and scoreing_class is None:
            (scoreing_class, args) = self._get_run_strategy(obj, args)

        return Event.score(self, obj, scoreing_class, args)
    
    def list_rankings(self):
        l = Event.list_rankings(self)
        l.extend([(c.name, self.ranking(c)) for c in self._store.find(Category)])
        l.sort(key = lambda x:x[0])
        return l

