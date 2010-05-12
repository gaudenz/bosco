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
editor.py - High level editing classes.
"""

from datetime import datetime
from time import sleep
from storm.exceptions import NotOneError, LostObjectError
from storm.locals import *

from runner import Team, Runner, SICard, Category
from run import Run, Punch, RunException
from course import Control, SIStation, Course
from formatter import AbstractRankingFormatter
from ranking import ValidationError, UnscoreableException, Validator
from sireader import SIReaderReadout, SIReaderException

class Observable(object):

    def __init__(self):
        self._observers = []
        
    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def _notify_observers(self, event = None):
        for o in self._observers:
            o.update(self, event)

class RunFinderException(Exception):
    pass

class RunFinder(Observable):
    """Searches for runs and/or runners."""

    _search_config = {'run'      : {'title' : u'Run',
                                    'joins' : True, # no tables to join, always true 
                                    'terms' : ((Run.id, 'int'),
                                               ),
                                    },
                      'sicard'   : {'title' : u'SICard',
                                    'joins' : True, # no tables to join, alway true
                                    'terms' : ((Run.sicard, 'int'),
                                               ),
                                    },
                      'runner'   : {'title': u'Runner',
                                    'joins' : And(Run.sicard == SICard.id,
                                                  SICard.runner == Runner.id),
                                    'terms' : ((Runner.given_name, 'partial_string'),
                                               (Runner.surname, 'partial_string'),
                                               (Runner.number, 'exact_string'),
                                               (Runner.solvnr, 'exact_string'),
                                               ),
                                    },
                      'team'     : {'title': u'Team',
                                    'joins' : And(Run.sicard == SICard.id,
                                               SICard.runner == Runner.id,
                                               Runner.team == Team.id),
                                    'terms' : ((Team.name, 'partial_string'),
                                               (Team.number, 'exact_string'),
                                               ),
                                    },
                      'category' : {'title': u'Category',
                                    'joins' : And(Run.sicard == SICard.id,
                                                  SICard.runner == Runner.id,
                                                  Or(Runner.category == Category.id,
                                                     And(Runner.team == Team.id,
                                                         Team.category == Category.id)
                                                     )
                                                  ),
                                    'terms' : ((Category.name, 'exact_string'),
                                               ),
                                    },
                      'course'   : {'title': u'Course',
                                    'joins' : And(Run.course == Course.id),
                                    'terms' : ((Course.code, 'exact_string'),
                                               ),
                                    },
                      }

    def __init__(self, store):
        super(RunFinder, self).__init__()
        self._store = store
        self._term = ''
        self._query = None
        self.set_search_domain('runner')

    def get_results(self, limit = False, start = 0):
        """Returns the results of the current search."""
        if self._query is None:
            return []

        results = []
        for r in self._query.order_by(Run.id):
            runner = r.sicard.runner
            team = runner and runner.team or None
            results.append((r.id, 
                            r.course and r.course.code and unicode(r.course.code) 
                              or 'unknown', 
                            r.readout_time and unicode(r.readout_time) or 'unknown', 
                            runner and runner.number and unicode(runner.number) 
                              or 'unknown',
                            runner and unicode(runner) or 'unknown',
                            team and unicode(team) or 'unknown',
                            team and unicode(team.category) or runner and unicode(runner.category)
                              or 'unkown'
                            ))

        return results

    def set_search_term(self, term):
        """Set the search string"""
        self._term = unicode(term).split()
        self._update_query()

    def get_search_domains(self):
        """
        @return List of (key, description) pairs of valid search domains.
        """
        return [(k, v['title']) for k,v in self._search_config.items() ]

    def set_search_domain(self, domain):
        """
        @param domain: set of search domains. Valid search domains are those
                       defined in _search_config.
        """
        if domain in self._search_config.keys():
            self._domain = domain
            self._update_query()
        else:
            raise RunFinderException("Search domain %s is invalid." % domain)

    def _update_query(self):
        """Updates the internal search query."""
        term_condition = []
        for t in self._term:
            condition_parts = []
            for column, col_type in self._search_config[self._domain]['terms']:
                if col_type == 'int':
                    try:
                        condition_parts.append(column == int(t))
                    except (ValueError, TypeError):
                        pass
                elif col_type == 'partial_string':
                    try:
                        condition_parts.append(column.lower().like("%%%s%%" % unicode(t).lower()))
                    except (ValueError, TypeError):
                        pass
                elif col_type == 'exact_string':
                    try:
                        condition_parts.append(column.lower() == unicode(t).lower())
                    except (ValueError, TypeError):
                        pass

            if len(condition_parts) > 0:
                term_condition.append(Or(*condition_parts))

        if len(term_condition) == 0:
            # An empty list of conditions should return no results
            term_condition.append(False)

        self._query = self._store.find(Run,
                                       And(self._search_config[self._domain]['joins'],
                                           *term_condition
                                           )
                                       )
        self._notify_observers()



class RunEditorException(Exception):
    pass

class RunEditor(Observable):
    """High level run editor. This class is intended as a model for a
    (graphical) editing front-end.
    The editor only edits one run at a time. Runs can be loaded from the
    database or read from an SI Reader station. If polling the reader is
    enabled, the edited run may change at any time!
    """

    _station_codes = {SIStation.START:  'start',
                      SIStation.FINISH: 'finish',
                      SIStation.CHECK:  'check',
                      SIStation.CLEAR:  'clear'}
    max_progress = 7
    
    # singleton instance
    __single = None
    __initialized = False
    
    def __new__(classtype, *args, **kwargs):
        """
        Override class creation to ensure that only one RunEditor is instantiated.
        """
       
        if classtype != type(classtype.__single):
            classtype.__single = object.__new__(classtype, *args, **kwargs)
        return classtype.__single
    
    def __init__(self, store, event, sireader_port = None):
        """
        @param store: Storm store of the runs
        @param event: object of class (or subclass of) Event. This is used for
                      run and team validation
        @param sireader_port: Serial port name of the SI Reader. None means autodetect.
        @note:        Later "instantiations" of this singleton discard all arguments.
        """
        if self.__initialized == True:
            return 
        
        Observable.__init__(self)
        self._store = store
        self._event = event
        
        self._run = None
        self._running = False
        self.progress = None
        self._is_changed = False

        self.connect_reader(sireader_port)
        
        self.__initialized = True

    run_readout_time = property(lambda obj: obj._run and obj._run.readout_time and str(obj._run.readout_time) or 'unknown')
    run_clear_time = property(lambda obj: obj._run and obj._run.clear_time and str(obj._run.clear_time) or 'unknown')
    run_check_time = property(lambda obj: obj._run and obj._run.check_time and str(obj._run.check_time) or 'unknown')
    run_card_start_time = property(lambda obj: obj._run and obj._run.card_start_time and str(obj._run.card_start_time) or 'unknown')
    run_manual_start_time = property(lambda obj: obj._run and obj._run.manual_start_time and str(obj._run.manual_start_time) or '')
    run_start_time = property(lambda obj: obj._run and obj._run.start_time and str(obj._run.start_time) or 'unknown')
    run_card_finish_time = property(lambda obj: obj._run and obj._run.card_finish_time and str(obj._run.card_finish_time) or 'unknown')
    run_manual_finish_time = property(lambda obj: obj._run and obj._run.manual_finish_time and str(obj._run.manual_finish_time) or '')
    run_finish_time = property(lambda obj: obj._run and obj._run.finish_time and str(obj._run.finish_time) or 'unknown')

    def has_runner(self):
        if self._run is None:
            return False
        return self._run.sicard.runner is not None

    def has_course(self):
        return self._run.course is not None

    def has_run(self):
        return self._run is not None
    
    def _get_runner_name(self):
        try:
            return unicode(self._run.sicard.runner or '')
        except AttributeError:
            return ''
    runner_name = property(_get_runner_name)

    runner_given_name = property(lambda obj: obj._run and obj._run.sicard.runner and
                                 obj._run.sicard.runner.given_name or '')
    runner_surname = property(lambda obj: obj._run and obj._run.sicard.runner and
                              obj._run.sicard.runner.surname or '')
    runner_dateofbirth = property(lambda obj: obj._run and obj._run.sicard.runner and
                                  str(obj._run.sicard.runner.dateofbirth) or '')
    
    def _get_runner_number(self):
        try:
            return self._run.sicard.runner.number or ''
        except AttributeError:
            return ''
    runner_number = property(_get_runner_number)

    runner_category = property(lambda obj: obj._run and obj._run.sicard.runner and
                               obj._run.sicard.runner.category and 
                               obj._run.sicard.runner.category.name or '')

    def _get_runner_team(self):
        try:
            return u'%3s: %s' % (self._run.sicard.runner.team.number, self._run.sicard.runner.team.name)
        except AttributeError:
            return ''
    runner_team = property(_get_runner_team)

    def _get_runner_sicard(self):
        try:
            return unicode(self._run.sicard.id)
        except AttributeError:
            return ''
    runner_sicard = property(_get_runner_sicard)

    def _get_run_id(self):
        try:
            return str(self._run.id)
        except AttributeError:
            return ''
    run_id = property(_get_run_id)
    
    def _get_run_course(self):
        try:
            return self._run.course.code
        except AttributeError:
            return ''
    run_course = property(_get_run_course)

    def _get_run_validation(self):
        try:
            validation = self._event.validate(self._run)
        except ValidationError:
            return ''
        return AbstractRankingFormatter.validation_codes[validation['status']]
    run_validation = property(_get_run_validation)

    def _get_run_score(self):
        try:
            return unicode(self._event.score(self._run)['score'])
        except UnscoreableException:
            return ''
    run_score = property(_get_run_score)

    def _get_run_override(self):
        try:
            override = self._run.override
        except AttributeError:
            return 0
        if override is None:
            return 0
        else:
            return override
    run_override = property(_get_run_override)

    def _get_run_complete(self):
        try:
            return self._run.complete
        except AttributeError:
            return False
    run_complete = property(_get_run_complete)

    def _get_team_validation(self):
        na = 'NA'
        if self._run is None:
            return ''
        
        try:
            team = self._run.sicard.runner.team
        except AttributeError:
            return na
        if team is None:
            return na
        try:
            validation = self._event.validate(team)
        except ValidationError:
            return ''
        return AbstractRankingFormatter.validation_codes[validation['status']]
    team_validation = property(_get_team_validation)

    def _get_team_score(self):
        try:
            return unicode(self._event.score(self._run.sicard.runner.team)['score'])
        except (UnscoreableException, AttributeError):
            return ''
    team_score = property(_get_team_score)
    
    def _raw_punchlist(self):
        try:
            punchlist = self._event.validate(self._run)['punchlist']
        except ValidationError:
            if self._run is None:
                return []
            
            # create pseudo validation result
            punchlist = [ ('', p) for p in self._run.punches ]

        # add finish punch if it does not have one
        if self._run.finish_time is None:
            punchlist.append(('missing',
                              self._store.get(SIStation, SIStation.FINISH)))
        return punchlist
        
    def _get_punchlist(self):

        def StationCode(si):
            if si <= SIStation.SPECIAL_MAX:
                return RunEditor._station_codes[si]
            else:
                return str(si)
            
        punchlist = []
        for code, p in self._raw_punchlist():
            if type(p) == Punch:
                punchlist.append((p.sequence and str(p.sequence) or '',
                                  p.sistation.control and p.sistation.control.code or '',
                                  StationCode(p.sistation.id),
                                  p.card_punchtime and str(p.card_punchtime) or '',
                                  p.manual_punchtime and str(p.manual_punchtime) or '',
                                  str(int(p.ignore)),
                                  str(code)))
            elif type(p) == Control:
                punchlist.append(('',
                                  p.code,
                                  '',
                                  '',
                                  '',
                                  str(int(False)),
                                  code))
            elif type(p) == SIStation:
                punchlist.append(('',
                                  '',
                                  StationCode(p.id),
                                  '',
                                  '',
                                  str(int(False)),
                                  code))
        return punchlist
    punchlist = property(_get_punchlist)

    def _set_changed(self, value):
        self._is_changed = value
        if self._is_changed == True:
            self._clear_cache()
            self._notify_observers('run')
    def _get_changed(self):
        return self._is_changed
    changed = property(_get_changed, _set_changed)
    
    def _clear_cache(self):
        try:
            self._event.clear_cache(self._run)
        except KeyError:
            pass
        try:
            if self._run.sicard.runner.team is not None:
                self._event.clear_cache(self._run.sicard.runner.team)
        except (AttributeError, KeyError):
            pass
        
    def get_runnerlist(self):
        runners = [(None, '')]
        for r in self._store.find(Runner).order_by('number'):
            runners.append((r.id, u'%s: %s' % (r.number, r)))
        return runners

    def get_teamlist(self):
        teams = [(None, '')]
        for t in self._store.find(Team).order_by('number'):
            teams.append((t.id, u'%3s: %s' % (t.number, t.name)))
        return teams

    def _create_virtual_sicard(self):
        """
        Creates a virtual SI-Card used when no real card number is
        available.
        """
        min_id = self._store.find(SICard).min(SICard.id) - 1
        if min_id > -1:
            min_id = -1
        return SICard(min_id)

    def set_runner(self, runner):
        if self._run is None:
            return

        runner = self._store.get(Runner, runner)

        if runner == self._run.sicard.runner:
            # return if runner did not change
            return

        if runner is None:
            # connect to a virtual sicard not belonging to any runner
            # leaves the sicard with the runner so to not reconnect this
            # run if another run with this sicard is created
            self._run.sicard = self._create_virtual_sicard()
            self.changed = True
            return

        if self._run.sicard.runner is None or self._run.sicard.runs.count() == 1:
            self._run.sicard.runner = runner
        else:
            # run already belongs to another runner
            # and there are other runs connected to this sicard
            # create a new 'virtual' sicard
            si = self._create_virtual_sicard()
            self._run.sicard = si
            runner.sicards.add(si)
            
        self.changed = True

    def set_runner_number(self, n, force = False):

        # unset number?
        if n == '':
            if self._run.sicard.runner is not None:
                self._run.sicard.runner.number = None
                self.changed = True
            return
        
        # numbers must be unique. See if there is already another runner
        # with this number
        prev_runner = self._store.find(Runner, Runner.number == n).one()

        if prev_runner is self._run.sicard.runner:
            return
        
        if prev_runner is not None and force is False:
            raise RunEditorException(u'Runner %s (%s) already has this number.' % (unicode(prev_runner), prev_runner.number))

        if self._run.sicard.runner is None:
            self._run.sicard.runner = Runner()
            
        if prev_runner is not None:
            prev_runner.number = None
            
        self._run.sicard.runner.number = n
        self.changed = True

    def set_runner_category(self, cat_name):
        
        if not self.has_runner():
            self._run.sicard.runner = Runner()

        cat = self._store.find(Category, Category.name == cat_name).one()
        self._run.sicard.runner.category = cat
        self.set_course(cat_name)
        self.changed = True
            
    def set_runner_given_name(self, n):
        try:
            self._run.sicard.runner.given_name = n
        except AttributeError:
            self._run.sicard.runner = Runner(given_name = n)

        self.changed = True

    def set_runner_surname(self, n):
        try:
            self._run.sicard.runner.surname = n
        except AttributeError:
            self._run.sicard.runner = Runner(surname = n)

        self.changed = True

    def set_runner_dateofbirth(self, d):

        # First convert date string to a date object. If this fails
        # it raises an Exception which should be handeld  by the caller.
        if d == '':
            d = None
        else:
            d = datetime.strptime(d, '%Y-%m-%d').date()

        if self._run.sicard.runner is None:
            self._run.sicard.runner = Runner()

        self._run.sicard.runner.dateofbirth = d    
        self.changed = True

    def set_runner_team(self, team):

        if team is not None:
            team = self._store.get(Team, team)

        if self._run.sicard.runner is None:
            self._run.sicard.runner = Runner()
            
        self._run.sicard.runner.team = team
        self.changed = True
    
    def set_course(self, course):
        if course == '':
            course = None
        try:
            self._run.set_coursecode(course)
        except RunException:
            pass
        else:
            self.changed = True

    def set_override(self, override):
        if override == 0:
            override = None
        self._run.override = override
        self.changed = True

    def set_complete(self, complete):
        self._run.complete = complete
        self.changed = True

    def parse_time(self, time):
        if time == '':
            return None
        else:
            return datetime.strptime(time, '%Y-%m-%d %H:%M:%S')

    def set_manual_start_time(self, time):
        self._run.manual_start_time = self.parse_time(time)
        self.changed = True

    def set_manual_finish_time(self, time):
        self._run.manual_finish_time = self.parse_time(time)
        self.changed = True
    
    def set_punchtime(self, punch, time):

        punch = self._raw_punchlist()[punch]
        if punch[0] == 'missing':
            # Create new manual punch with this time
            if type(punch[1]) == Control:
                si = punch[1].sistations.any()
            elif type(punch[1]) == SIStation:
                si = punch[1]
            self._run.punches.add(Punch(si,
                                        manual_punchtime = self.parse_time(time)))
        elif punch[1].card_punchtime is None and time == '':
            # remove punch if both times would become None
            self._store.remove(punch[1])
        else:
            punch[1].manual_punchtime = self.parse_time(time)

        self.changed = True
        
    def set_ignore(self, punch, ignore):
        punch = self._raw_punchlist()[punch][1]
        if ignore == '' or ignore == '0':
            punch.ignore = False
        elif ignore == '1':
            punch.ignore = True

        self.changed = True

    def load(self, run):
        """
        Loads a run into the editor. All uncommited changes to the previously
        loaded run will be lost!
        @param run: run id
        """
        self.rollback()
        self._run = self._store.get(Run, run)
        self._clear_cache()
        self._notify_observers('run')

    def new(self):
        """
        Create a new empty run
        """
        self.rollback()
        self._run = self._store.add(Run(self._create_virtual_sicard()))
        # Flush the store to assign default values to the new run
        self._store.flush()
        self.changed = True
        
    def commit(self):
        """Commit changes to the database."""
        self._store.commit()
        self.changed = False

    def rollback(self):
        """Rollback all changes."""
        self._store.rollback()
        
        if self._run is not None:
            try:
                tmp = self._run.sicard
            except LostObjectError:
                # Clear run if it got lost by the rollback action
                # Store.of(self._run) still returns the store because it
                # may reference objects in the store. Use this hack instead.
                self._run = None
            
            self.changed = False
            # But notify observers that the object may have changed and clear
            # the cache
            self._clear_cache()
            self._notify_observers('run')

    def _get_port(self):
        if self._sireader is None:
            return 'not connected'
        else:
            return '%s (at %s baud)' % (self._sireader.port,
                                        self._sireader.baudrate)
    port = property(_get_port)
    
    def _get_status(self):
        if self._sireader is None:
            return ''
        elif self._running is False and self.sicard is None:
            return 'No SI-Card inserted.'
        elif self.sicard is None:
            return 'Waiting for SI-Card...'
        elif self._running and self.sicard_runner is not None:
            return 'Reading SI-Card %s of runner %s...' % (self.sicard,
                                                           self.sicard_runner)
        elif self._running:
            return 'Reading SI-Card %s...' % self.sicard
        elif self.sicard_runner is not None:
            return 'SI-Card %s of runner %s inserted.' % (self.sicard,
                                                          self.sicard_runner)
        else:
            return 'SI-Card %s inserted.' % self.sicard
    status = property(_get_status)

    def _get_progress(self):
        return self._progress
    def _set_progress(self, msg):
        if msg is None:
            # reset progress
            self._progress = (0, 'Waiting for SI-Card...')
        else:
            # increase by one
            self._progress = (self._progress[0] + 1, msg)
        self._notify_observers('progress')
    progress = property(_get_progress, _set_progress)

    def _get_sicard(self):
        if self._sireader is not None:
            return self._sireader.sicard
        else:
            return None
    sicard = property(_get_sicard)

    def _get_sicard_runner(self):
        if self.sicard is not None:
            runner = self._store.find(Runner,
                                      SICard.id == self.sicard,
                                      SICard.runner == Runner.id).one()
            if runner is None:
                return None
            else:
                string = '%s: %s %s' % (runner.number,
                                        runner.given_name,
                                        runner.surname)
            if runner.team is None:
                return string
            else:
                return '%s (%s)' % (string, runner.team.name)
    sicard_runner = property(_get_sicard_runner)

    def connect_reader(self, port = None):
        """
        Connect an SI-Reader
        @param port: serial port name, default autodetected
        """
        try:
            self._sireader = SIReaderReadout(port)
        except SIReaderException:
            self._sireader = None
            
        self._notify_observers('reader')
        
    def start_reader(self):
        """Start immediately reading out inserted SI-Cards. While polling
        the reader the edited run may change at any time if a new SI-Card
        is inserted."""
        self._running = True

    def stop_reader(self):
        """Stop reading  si-cards."""
        self._running = False

    def poll_reader(self):
        """Polls the sireader for changes. If the reader is started, the
        card is read out immediately. Otherwise the run must be loaded
        manually by calling load_run_from_card."""
        if self._sireader is not None:
            if self._sireader.poll_sicard():
                self._notify_observers('reader')
                if self.sicard is not None and self._running:
                    self.load_run_from_card()
                    
    def load_run_from_card(self):
        """Read out card data and create or load a run based on this data."""
        
        if self.sicard is None:
            return

        # clear current run
        self._run = None

        # wrap everything in a try - except block to be able to roll back
        # on error
        try:
            self.rollback()
            self.progress = None
            self.progress = 'Reading card data...'
        
            card_data = self._sireader.read_sicard()

            # find complete runs with this sicard
            self.progress = 'Searching for matching run...'
            runs = self._store.find(Run,
                                    Run.sicard == card_data['card_number'],
                                    Run.complete == True)

            for r in runs:
                if self._compare_run(r, card_data):
                    self._run = r
                    self._sireader.ack_sicard()
                    return
        
            # search for incomplete run with this sicard
            self.progress = 'Searching for open run...'
            try:
                self._run = self._store.find(Run,
                                             Run.sicard == card_data['card_number'],
                                             Run.complete == False).one()
            except NotOneError:
                self._run = None

            if self._run is None:
                # Create new run
                self.progress = 'Creating new run and adding punches...'
                self._run = Run(card_data['card_number'],
                                punches = card_data['punches'],
                                card_start_time = card_data['start'],
                                check_time = card_data['check'],
                                clear_time = card_data['clear'],
                                card_finish_time = card_data['finish'],
                                readout_time = datetime.now(),
                                store = self._store)
            else:
                self.progress = 'Adding punches to existing run...'
                self._run.card_start_time = card_data['start']
                self._run.card_finish_time = card_data['finish']
                self._run.card_check_time = card_data['check']
                self._run.card_clear_time = card_data['clear']
                self._run.add_punchlist(card_data['punches'])

            # mark run as complete
            self._run.complete = True
            
            if self._run.course is None:
                self.progress = 'Searching matching course ...'
                # Search Course for this run
                courses = self._store.find(Course)
                self._clear_cache()
                for c in courses:
                    self._run.course = c
                    valid = self._event.validate(self._run)
                    if  valid['status'] == Validator.OK:
                        break
                    else:
                        self._run.course = None
                        self._clear_cache()
            else:
                self.progress = 'Course already set.'

            self.progress = 'Updating validation...'
            self.progress = 'Commiting run to database...'
            self.commit()
            self._sireader.ack_sicard()
            self.changed = True
                
        finally:
            # roll back and re-raise the exception
            self.rollback()
            self.progress = None
        
        self.progress = None
        
        
    def _compare_run(self, run, card_data):
        """
        Compares run to card_data
        @return: True if card_data matches run, False otherwise
        """
        if run.sicard.id != card_data['card_number']:
            return False

        punches = run.punches.find(Not(Punch.card_punchtime == None))
        if punches.count() != len(card_data['punches']):
            # different punch count
            return False
            
        card_data['punches'].sort(key = lambda x: x[1])
        for i,p in enumerate(punches.order_by('card_punchtime')):
            if not p.card_punchtime == card_data['punches'][i][1]:
                return False

        return True
            
class TeamEditor(Observable):

    def __init__(self, store, event):
        """
        @param store: Storm store of the runs
        @param event: object of class (or subclass of) Event. This is used for
                      run and team validation
        """
        Observable.__init__(self)
        self._store = store
        self._event = event
        
        self._team = None

    def get_teamlist(self):
        teams = []
        for t in self._store.find(Team).order_by('number'):
            teams.append((t.id, '%3s: %s' % (t.number, t.name)))

        return teams

    def _get_validation(self):
        try:
            validation = self._event.validate(self._team)
        except (ValidationError, AttributeError):
            return ''
        return AbstractRankingFormatter.validation_codes[validation['status']]
    validation = property(_get_validation)

    def _get_score(self):
        try:
            return unicode(self._event.score(self._team)['score'])
        except (UnscoreableException, AttributeError):
            return ''
    score = property(_get_score)

    def _get_runs(self):

        def format_runner(runner):
            if r.sicard.runner is None:
                return ''
            elif r.sicard.runner.number is None:
                return unicode(runner)
            else:
                return unicode('%3s: %s' % (r.sicard.runner.number,
                                            r.sicard.runner))
            
        if self._team is None:
            return []
        
        runs = self._team.runs
        runs.sort(key = lambda x: x.finish_time or datetime.max)
        result = []
        for r in runs:
            try:
                code = self._event.validate(r)['status']
                validation = AbstractRankingFormatter.validation_codes[code]
            except ValidationError:
                validation = ''
            try:
                score = self._event.score(r)
            except UnscoreableException:
                score = {'start':'', 'finish':'', 'score':''}

            result.append((str(r.id),
                           r.course and r.course.code or '',
                           format_runner(r.sicard.runner),
                           str(r.sicard.id),
                           str(score['start'] or ''),
                           str(score['finish'] or ''),
                           validation,
                           str(score['score'])))
        return result
    runs = property(_get_runs)

    def load(self, team):
        self._store.rollback()
        self._team = self._store.get(Team, team)
        self._notify_observers()
