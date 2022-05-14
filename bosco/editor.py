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
import sys

from abc import ABCMeta, abstractmethod
from datetime import datetime, date
from time import sleep
from subprocess import Popen, PIPE
from traceback import print_exc

from storm.exceptions import NotOneError, LostObjectError
from storm.expr import Func, LeftJoin
from storm.locals import *

from sireader import SIReaderReadout, SIReaderException, SIReader

from .runner import Team, Runner, SICard, Category, Club
from .run import Run, Punch, RunException
from .course import Control, SIStation, Course
from .formatter import AbstractFormatter, ReportlabRunFormatter
from .ranking import ValidationError, UnscoreableException, Validator, OpenRuns

class Observable:

    def __init__(self):
        self._observers = []

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def _notify_observers(self, event = None, message = None):
        for o in self._observers:
            o.update(self, event, message)

class ItemFinderException(Exception):
    pass


class ItemFinder(Observable, metaclass=ABCMeta):
    """Searches for items"""

    def __init__(self, store):
        super().__init__()
        self._store = store
        self._term = ''
        self._query = None

    @abstractmethod
    def _format_result(self, r):
        pass

    def get_results(self, limit=False, start=0):
        """Returns the results of the current search."""
        if self._query is None:
            return []

        return map(
            self._format_result,
            self._query.order_by(self._item_class.id),
        )

    def set_search_term(self, term):
        """Set the search string"""
        self._term = str(term).split()
        self._update_query()

    def _update_query(self):
        """Updates the internal search query."""
        term_condition = []
        for t in self._term:
            condition_parts = []
            for column, col_type in self._search_config['terms']:
                if col_type == 'int':
                    try:
                        condition_parts.append(column == int(t))
                    except (ValueError, TypeError):
                        pass
                elif col_type == 'partial_string':
                    try:
                        condition_parts.append(column.lower().like("%%%s%%" % str(t).lower()))
                    except (ValueError, TypeError):
                        pass
                elif col_type == 'exact_string':
                    try:
                        condition_parts.append(column.lower() == str(t).lower())
                    except (ValueError, TypeError):
                        pass

            if len(condition_parts) > 0:
                term_condition.append(Or(*condition_parts))

        if len(term_condition) == 0:
            # An empty list of conditions should return no results
            term_condition.append(False)

        self._query = self._store.using(
            self._item_class,
            *self._search_config['joins'],
        ).find(
            self._item_class,
            And(*term_condition),
        )
        self._notify_observers()


# Alias of the Category class to be able to join Teams to Categories at the same
# time as joining Runners to Categories.
TeamCategory = ClassAlias(Category)

class RunFinder(ItemFinder):
    """Searches for runs."""

    _item_class = Run

    _search_config = {
        'joins': (
            LeftJoin(SICard, Run.sicard == SICard.id),
            LeftJoin(Runner, SICard.runner == Runner.id),
            LeftJoin(Course, Run.course == Course.id),
            LeftJoin(Category, Runner.category == Category.id),
            LeftJoin(Team, Runner.team == Team.id),
            LeftJoin(TeamCategory, Team.category == TeamCategory.id),
        ),
        'terms': (
            (Run.id, 'int'),
            (SICard.id, 'int'),
            (Runner.given_name, 'partial_string'),
            (Runner.surname, 'partial_string'),
            (Runner.number, 'exact_string'),
            (Runner.solvnr, 'exact_string'),
            (Team.name, 'partial_string'),
            (Team.number, 'exact_string'),
            (Category.name, 'exact_string'),
            (Course.code, 'exact_string'),
            (TeamCategory.name, 'exact_string'),
        ),
    }

    def _format_result(self, r):

        runner = r.sicard.runner
        team = runner and runner.team or None
        club = runner and runner.club and runner.club.name or None

        return (
            r.id,
            r.course and r.course.code and str(r.course.code)
            or 'unknown',
            r.readout_time and RunEditor._format_time(r.readout_time) or 'unknown',
            runner and runner.number and str(runner.number)
            or 'unknown',
            runner and str(runner) or 'unknown',
            team and str(team) or club and str(club) or 'unknown',
            team and str(team.category) or runner and str(runner.category)
            or 'unkown'
        )


class RunnerFinder(ItemFinder):
    """Search for Runners."""

    _item_class = Runner

    _search_config = {
        'joins': (
            LeftJoin(SICard, SICard.runner == Runner.id),
            LeftJoin(Category, Runner.category == Category.id),
            LeftJoin(Team, Runner.team == Team.id),
            LeftJoin(TeamCategory, Team.category == TeamCategory.id),
        ),
        'terms': (
            (SICard.id, 'int'),
            (Runner.given_name, 'partial_string'),
            (Runner.surname, 'partial_string'),
            (Runner.number, 'exact_string'),
            (Runner.solvnr, 'exact_string'),
            (Team.name, 'partial_string'),
            (Team.number, 'exact_string'),
            (Category.name, 'exact_string'),
            (TeamCategory.name, 'exact_string'),
        ),
    }

    def _format_result(self, r):

        team = r.team or None
        club = r.club and r.club.name or None

        return (
            r.id,
            str(r.number),
            str(r),
            team and str(team) or club and str(club) or 'unknown',
            team and str(team.category) or r and str(r.category)
            or 'unkown'
        )


class TeamFinder(ItemFinder):
    """Search for teams."""

    _item_class = Team

    _search_config = {
        'joins': (
            LeftJoin(Category, Team.category == Category.id),
        ),
        'terms': (
            (Team.name, 'partial_string'),
            (Team.number, 'exact_string'),
            (Category.name, 'exact_string'),
        ),
    }

    def _format_result(self, t):

        return (
            t.id,
            str(t.number),
            str(t),
            str(t.category),
        )


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


class RunEditorException(Exception):
    pass

class RunEditor(Observable, metaclass=Singleton):
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

    __initialized = False

    def __init__(self, store, event):
        """
        @param store: Storm store of the runs
        @param event: object of class (or subclass of) Event. This is used for
                      run and team validation
        @note:        Later "instantiations" of this singleton discard all arguments.
        """
        if self.__initialized == True:
            return

        Observable.__init__(self)
        self._store = store
        self._event = event

        self._run = None
        self.progress = None
        self._is_changed = False

        self._sireader = None

        self._print_command = "lp -o media=A5"

        self.__initialized = True

    @staticmethod
    def _format_time(time, date = True):
        format = date and '%x %X' or '%X'
        return time.strftime(format)

    run_readout_time = property(lambda obj: obj._run and obj._run.readout_time and RunEditor._format_time(obj._run.readout_time) or 'unknown')
    run_clear_time = property(lambda obj: obj._run and obj._run.clear_time and RunEditor._format_time(obj._run.clear_time) or 'unknown')
    run_check_time = property(lambda obj: obj._run and obj._run.check_time and RunEditor._format_time(obj._run.check_time) or 'unknown')
    run_card_start_time = property(lambda obj: obj._run and obj._run.card_start_time and RunEditor._format_time(obj._run.card_start_time) or 'unknown')
    run_manual_start_time = property(lambda obj: obj._run and obj._run.manual_start_time and RunEditor._format_time(obj._run.manual_start_time) or '')
    run_start_time = property(lambda obj: obj._run and obj._run.start_time and RunEditor._format_time(obj._run.start_time) or 'unknown')
    run_card_finish_time = property(lambda obj: obj._run and obj._run.card_finish_time and RunEditor._format_time(obj._run.card_finish_time) or 'unknown')
    run_manual_finish_time = property(lambda obj: obj._run and obj._run.manual_finish_time and RunEditor._format_time(obj._run.manual_finish_time) or '')
    run_finish_time = property(lambda obj: obj._run and obj._run.finish_time and RunEditor._format_time(obj._run.finish_time) or 'unknown')

    def has_runner(self):
        return self.has_run() and self._run.sicard.runner is not None

    def has_course(self):
        return self._run.course is not None

    def has_run(self):
        return self._run is not None

    def _get_runner_name(self):
        try:
            return str(self._run.sicard.runner or '')
        except AttributeError:
            return ''
    runner_name = property(_get_runner_name)

    runner_given_name = property(lambda obj: obj._run and obj._run.sicard.runner and
                                 obj._run.sicard.runner.given_name or '')
    runner_surname = property(lambda obj: obj._run and obj._run.sicard.runner and
                              obj._run.sicard.runner.surname or '')
    runner_dateofbirth = property(lambda obj: obj._run and obj._run.sicard.runner and
                                  obj._run.sicard.runner.dateofbirth and
                                  obj._run.sicard.runner.dateofbirth.strftime('%x') or '')

    runner_club = property(lambda obj: obj._run and obj._run.sicard.runner and
                           obj._run.sicard.runner.club and
                           obj._run.sicard.runner.club.name or '')

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
            return '%3s: %s' % (self._run.sicard.runner.team.number, self._run.sicard.runner.team.name)
        except AttributeError:
            return ''
    runner_team = property(_get_runner_team)

    def _get_runner_sicard(self):
        try:
            return str(self._run.sicard.id)
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
        return AbstractFormatter.validation_codes[validation['status']]
    run_validation = property(_get_run_validation)

    def _get_run_score(self):
        try:
            return str(self._event.score(self._run)['score'])
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
        return AbstractFormatter.validation_codes[validation['status']]
    team_validation = property(_get_team_validation)

    def _get_team_score(self):
        try:
            return str(self._event.score(self._run.sicard.runner.team)['score'])
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
            punchlist = [ ('ignored', p) for p in self._run.punches.order_by(Func('COALESCE', Punch.manual_punchtime, Punch.card_punchtime))]

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
            if isinstance(p, Punch):
                punchlist.append((p.sequence and str(p.sequence) or '',
                                  p.sistation.control and p.sistation.control.code or '',
                                  StationCode(p.sistation.id),
                                  p.card_punchtime and RunEditor._format_time(p.card_punchtime) or '',
                                  p.manual_punchtime and RunEditor._format_time(p.manual_punchtime) or '',
                                  str(int(p.ignore)),
                                  str(code)))
            elif isinstance(p, Control):
                punchlist.append(('',
                                  p.code,
                                  '',
                                  '',
                                  '',
                                  str(int(False)),
                                  code))
            elif isinstance(p, SIStation):
                punchlist.append(('',
                                  '',
                                  StationCode(p.id),
                                  '',
                                  '',
                                  str(int(False)),
                                  code))
        return punchlist
    punchlist = property(_get_punchlist)

    print_command = property(lambda x:x._print_command)

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
            runners.append((r.id, '%s: %s' % (r.number, r)))
        return runners

    def get_teamlist(self):
        teams = [(None, '')]
        for t in self._store.find(Team).order_by('number'):
            teams.append((t.id, '%3s: %s' % (t.number, t.name)))
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
        """
        Changes the runner of the current run. If no runner is found
        the run is disconnected from the current runner. If the current
        runner has multiple runs, a "virtual" sicard is created.
        @param runner: ID of the new runner
        """

        if self._run is None:
            return

        runner = self._store.get(Runner, runner)

        if runner == self._run.sicard.runner:
            # return and don't commit if runner did not change
            return

        if runner is None:
            # connect to a virtual sicard not belonging to any runner
            # leaves the sicard with the runner so to not reconnect this
            # run if another run with this sicard is created
            self._run.sicard = self._create_virtual_sicard()
        elif self._run.sicard.runner is None or self._run.sicard.runs.count() == 1:
            self._run.sicard.runner = runner
        else:
            # run already belongs to another runner
            # and there are other runs connected to this sicard
            # create a new 'virtual' sicard
            si = self._create_virtual_sicard()
            self._run.sicard = si
            runner.sicards.add(si)

        self.commit()

    def set_runner_number(self, n, force = False):

        # unset number?
        if n == '':
            if self._run.sicard.runner is not None:
                self._run.sicard.runner.number = None
                self.commit()
            return

        # numbers must be unique. See if there is already another runner
        # with this number
        prev_runner = self._store.find(Runner, Runner.number == n).one()

        # Attention: check for prev_runnner first, None is None == True !
        if prev_runner and prev_runner is self._run.sicard.runner:
            # same runner as current runner, nothing to be done
            return

        if prev_runner is not None and force is False:
            raise RunEditorException('Runner %s (%s) already has this number.' % (str(prev_runner), prev_runner.number))

        if not self.has_runner():
            self._run.sicard.runner = Runner()

        if prev_runner is not None:
            # unset number on previous runner, force is True by now
            prev_runner.number = None

        self._run.sicard.runner.number = n
        self.commit()

    def set_runner_category(self, cat_name):

        if not self.has_runner():
            self._run.sicard.runner = Runner()

        cat = self._store.find(Category, Category.name == cat_name).one()
        self._run.sicard.runner.category = cat
        self.set_course(cat_name)
        self.commit()

    def set_runner_given_name(self, n):
        try:
            self._run.sicard.runner.given_name = n
        except AttributeError:
            self._run.sicard.runner = Runner(given_name = n)

        self.commit()

    def set_runner_surname(self, n):
        try:
            self._run.sicard.runner.surname = n
        except AttributeError:
            self._run.sicard.runner = Runner(surname = n)

        self.commit()

    def set_runner_dateofbirth(self, d):

        # First convert date string to a date object. If this fails
        # it raises an Exception which should be handeld  by the caller.
        if d == '':
            d = None
        else:
            d = datetime.strptime(d, '%x').date()

        if self._run.sicard.runner is None:
            self._run.sicard.runner = Runner()

        self._run.sicard.runner.dateofbirth = d
        self.commit()

    def set_runner_team(self, team):

        if team is not None:
            team = self._store.get(Team, team)

        if self._run.sicard.runner is None:
            self._run.sicard.runner = Runner()

        self._run.sicard.runner.team = team
        self.commit()

    def set_runner_club(self, clubname):

        if clubname != '':
            club = self._store.find(Club, Club.name == clubname).one()
            if club is None:
                club = Club(clubname)
        else:
            club = None

        if self._run.sicard.runner is None:
            self._run.sicard.runner = Runner()

        self._run.sicard.runner.club = club
        self.commit()

    def set_course(self, course):
        if course == '':
            course = None
        try:
            self._run.set_coursecode(course)
        except RunException:
            pass
        else:
            self.commit()

    def set_override(self, override):
        if override == 0:
            override = None
        self._run.override = override
        self.commit()

    def set_complete(self, complete):
        self._run.complete = complete
        self.commit()

    def parse_time(self, time):
        if time == '':
            return None

        # try date and time in current locale
        try:
            return datetime.strptime(time, '%x %X')
        except ValueError:
            pass

        # try only time in current locale
        try:
            t = datetime.strptime(time, '%X')
            today = date.today()
            return t.replace(year=today.year, month=today.month, day=today.day)
        except ValueError:
            pass

        # try YYYY-mm-dd hh:mm:ss representation
        try:
            return datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass

        # try hh:mm:ss
        try:
            t = datetime.strptime(time, '%H:%M:%S')
            today = date.today()
            return t.replace(year=today.year, month=today.month, day=today.day)
        except ValueError:
            pass

        # we just don't know how to interpret this time
        return None

    def set_manual_start_time(self, time):
        self._run.manual_start_time = self.parse_time(time)
        self.commit()

    def set_manual_finish_time(self, time):
        self._run.manual_finish_time = self.parse_time(time)
        self.commit()

    def set_punchtime(self, punch, time):

        punch = self._raw_punchlist()[punch]
        if punch[0] == 'missing':
            # Create new manual punch with this time
            if isinstance(punch[1], Control):
                si = punch[1].sistations.any()
            elif isinstance(punch[1], SIStation):
                si = punch[1]
            self._run.punches.add(Punch(si,
                                        manual_punchtime = self.parse_time(time)))
        elif punch[1].card_punchtime is None and time == '':
            # remove punch if both times would become None
            self._store.remove(punch[1])
        else:
            punch[1].manual_punchtime = self.parse_time(time)

        self.commit()

    def set_ignore(self, punch, ignore):
        punch = self._raw_punchlist()[punch][1]
        if ignore == '' or ignore == '0':
            punch.ignore = False
        elif ignore == '1':
            punch.ignore = True

        self.commit()

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

    def new(self, si_nr = None):
        """
        Create a new empty run. This rolls back any uncommited changes!
        @param si_nr: number of the SI-Card
        """
        self.rollback()
        if si_nr is None:
            sicard = self._create_virtual_sicard()
        else:
            sicard = self._store.get(SICard, si_nr)
            if sicard is None:
                sicard = SICard(si_nr)
        self._run = self._store.add(Run(sicard))
        self.commit()

    def new_from_reader(self):
        """
        Creates a new empty run for the card currently inserted into the reader.
        If an open run for this card already exists, this run is loaded and no
        new run created.
        """
        si_nr = self._sireader.sicard
        if not si_nr:
            raise RunEditorException("Could not read SI-Card.")

        self.rollback()
        self._run = None
        sicard = self._store.get(SICard, si_nr)
        if sicard is None:
            sicard = SICard(si_nr)
        else:
            # try to load existing open run
            self._run = self._store.find(Run,
                                         Run.sicard == si_nr,
                                         Run.complete == False).order_by(Run.id).last()

        if self._run is None:
            # Create new run
            self._run = self._store.add(Run(sicard))

        self.commit()
        self._sireader.ack_sicard()

    def delete(self):
        """
        Deletes the current run.
        """
        # first remove all punches
        for p in self._run.punches:
            self._store.remove(p)
        self._store.remove(self._run)
        self._run = None
        self.commit()

    def commit(self):
        """Commit changes to the database."""
        try:
            self._store.commit()
            # some errors (notably LostObjectError) only occur when the object
            # is accessed again, clear cache triggers these
            self._clear_cache()
        except LostObjectError as e:
            # run got removed during the transaction
            self._run = None
            self._notify_observers('error', str(e))
        except Exception as e:
            print_exc(file=sys.stderr)
            self._notify_observers('error', str(e))

        self._notify_observers('run')

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
        elif self.sicard is None:
            return 'No SI-Card inserted.'
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

    def print_run(self):
        f = ReportlabRunFormatter(self._run, self._event._header, self._event)
        Popen(self._print_command, shell=True, stdin=PIPE).communicate(input=str(f))

    def connect_reader(self, port = None):
        """
        Connect an SI-Reader
        @param port: serial port name, default autodetected
        """
        fail_reasons = []
        try:
            self._sireader = SIReaderReadout(port)
        except SIReaderException as e:
            fail_reasons.append(str(e))
        else:

            # check for correct reader configuration
            fail_template = "Wrong SI-Reader configuration: %s"
            config = self._sireader.proto_config
            if config['auto_send'] == True:
                fail_reasons.append(fail_template % "Autosend is enabled.")
            if config['ext_proto'] == False:
                fail_reasons.append(fail_template % "Exended protocol is not enabled.")
            if config['mode'] != SIReader.M_READOUT:
                fail_reasons.append(fail_template % "Station is not in readout mode.")

        if len(fail_reasons) > 0:
            self._sireader = None

        self._notify_observers('reader')

        if len(fail_reasons) > 0:
            raise RunEditorException("\n".join(fail_reasons))

    def poll_reader(self):
        """Polls the sireader for changes."""
        if self._sireader is not None:
            try:
                if self._sireader.poll_sicard():
                    self._notify_observers('reader')
            except IOError:
                # try to reconnect on error
                try:
                    self._sireader.reconnect()
                except SIReaderException:
                    # reconnection failed, disconnect reader and reraise
                    self._sireader = None
                    self._notify_observers('reader')
                    raise

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
                if not self._run.readout_time:
                    self._run.readout_time = datetime.now()
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

        # compare punches
        card_data['punches'].sort(key = lambda x: x[1])
        for i, p in enumerate(punches.order_by('card_punchtime')):
            if not p.card_punchtime == card_data['punches'][i][1]:
                return False

        # compare start and finish time
        if not run.card_start_time == card_data['start']:
            return False
        if not run.card_finish_time == card_data['finish']:
            return False

        return True

    def set_print_command(self, command):
        self._print_command = command

class RunListFormatter:

    def format_run(self, run):

        def format_runner(runner):
            if run.sicard.runner is None:
                return ''
            elif run.sicard.runner.number is None:
                return str(runner)
            else:
                return str('%3s: %s' % (run.sicard.runner.number,
                                            run.sicard.runner))

        # run validation and score
        try:
            code = self._event.validate(run)['status']
            validation = AbstractFormatter.validation_codes[code]
        except ValidationError:
            validation = ''
        try:
            score = self._event.score(run)
        except UnscoreableException:
            score = {'start':'', 'finish':'', 'score':''}

        # team validation and score
        team = run.sicard.runner and run.sicard.runner.team or None
        try:
            code = self._event.validate(team)['status']
            team_validation =  AbstractFormatter.validation_codes[code]
        except ValidationError:
            team_validation = ''

        return (str(run.id),
                run.course and run.course.code or '',
                format_runner(run.sicard.runner),
                str(run.sicard.id),
                team and team.name or '',
                str('start' in score and score['start'] or ''),
                str('finish' in score and score['finish'] or ''),
                validation,
                team_validation,
                str(score['score']))

class TeamEditor(Observable, RunListFormatter):

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
        return AbstractFormatter.validation_codes[validation['status']]
    validation = property(_get_validation)

    def _get_score(self):
        try:
            return str(self._event.score(self._team)['score'])
        except (UnscoreableException, AttributeError):
            return ''
    score = property(_get_score)

    def _get_runs(self):

        if self._team is None:
            return []

        runs = self._team.runs
        runs.sort(key = lambda x: x.finish_time or datetime.max)
        result = []
        for r in runs:
            result.append(self.format_run(r))

        return result
    runs = property(_get_runs)

    def load(self, team):
        self._store.rollback()
        self._team = self._store.get(Team, team)
        self._notify_observers()

class Reports(RunListFormatter):

    # list of supported reports
    # these are (method, descriptive name) tuples
    # the method should return a list of Run objects
    _supported_reports = (('_open_runs',   'Open runs'  ),
                          ('_orphan_runs', 'Orphan runs'),
                          )

    def __init__(self, store, event):
        """
        @param store: Storm store of the runs
        @param event: object of class (or subclass of) Event. This is used for
                      run and team validation
        """
        self._store = store
        self._event = event
        self._report = None

    def list_reports(self):
        return Reports._supported_reports

    def set_report(self, report):
        if report in [r[0] for r in Reports._supported_reports]:
            self._report = report

    def _get_runs(self):
        runs = getattr(self, self._report)()
        result = []
        for r in runs:
            result.append(self.format_run(r))
        return result
    runs = property(_get_runs)

    def _open_runs(self):
        """Lists all runs that are not yet completed."""
        return OpenRuns(self._store).members

    def _orphan_runs(self):
        """Lists all runs that don't belong to any runner."""
        return self._store.find(Run,
                                And(Run.sicard == SICard.id,
                                    SICard.runner == None,
                                    )
                                )
