#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    import_teams.py - Import Data from go2ol.ch
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

from csv import reader, writer, Sniffer, Error
from datetime import datetime, date
from time import sleep
from sys import exit, hexversion
if hexversion > 0x20500f0:
    from xml.etree.ElementTree import parse
else:
    from elementtree.ElementTree import parse
import re
from os import fsync

from storm.locals import *
from storm.exceptions import NotOneError, IntegrityError

from psycopg2 import DataError

from .runner import Runner, Team, SICard, Category, Country, Club
from .course import Control, Course, Course, SIStation
from .run import Run, Punch

class Importer:
    """Base class for all Importer classes to import event
       data. This class provides the general interface for (GUI)
       import frontends."""

    def __init__(self, fname, verbose):
        pass

    def import_data(self, store):
        """Import runner data into store. Creates all the necessary objects
           and add them to the store, but don't commit the store."""
        pass

class CSVImporter(Importer):
    """Import form a CSV file. The first line of the file contains
       descriptive labels for the values. All further lines are read
       into a list of dictionaries using these labels."""

    def __init__(self, fname, encoding, verbose = False):

        self._verbose = verbose

        # List of dicts
        self.data = []

        # Set up CSV reader
        fh = open(fname, 'r', encoding=encoding)
        try:
            dialect = Sniffer().sniff(fh.read(1024))
            fh.seek(0)
            csv = reader(fh, dialect = dialect)
        except Error:
            fh.seek(0)
            csv = reader(fh, delimiter="\t")

        # Read labels
        labels = [ v.strip() for v in next(csv) ]
        self._fieldcount = len(labels)

        # Read values
        for line in csv:
            try:
                if line[0].strip()[0] == '#':
                    # skip comment lines
                    continue
            except IndexError:
                pass
            d = {}
            for i, v in enumerate(line):
                d[labels[i]] = v.strip()

            self.data.append(d)

class RunnerImporter(CSVImporter):
    """Import Runner data from CSV file.
    This class currently only consists of helper functions for derived classes.
    """

    @staticmethod
    def _parse_yob(yob):
        """Parses the year of birth
        @rtype: date or None
        """
        if yob is None:
            return None
        try:
            return date(int(yob), 1, 1)
        except ValueError:
            return None

    @staticmethod
    def _get_sicard(si_str, store):
        try:
            si_int = int(si_str)
        except ValueError:
            if not si_str == '':
                raise InvalidSICardException("Invalid SI Card number '%s'" % si_str)
            else:
                raise NoSICardException()
        if si_int == 0:
            raise NoSICardException()

        sicard = store.get(SICard, si_int)
        if sicard is None:
            sicard = SICard(si_int)

        return sicard

    @staticmethod
    def _add_sicard(runner, sicard, store, force = False):
        """Add SI Card to runner if it is valid.
        @return One of the SICARD_* constants above.
        """

        if sicard and sicard.runner == runner:
            # this card is already assigned to this runner
            return
        elif sicard and sicard.runner:
            if force:
                print(("Forcing reassignment of SI-Card %s from runner %s %s (%s) "
                       "to runner %s %s (%s)." %
                       (sicard.id, sicard.runner.given_name, sicard.runner.surname, 
                        sicard.runner.number, runner.given_name, runner.surname, 
                        runner.number)))
                sicard.runner = None
            else:
                raise AlreadyAssignedSICardException("SI-Card %s is already assigned to runner "
                                                     "%s %s (%s). Not assigning any card to "
                                                     "runner %s %s (%s)." %
                                                     (sicard.id, sicard.runner.given_name,
                                                      sicard.runner.surname,
                                                      sicard.runner.number, runner.given_name, 
                                                      runner.surname, runner.number))

        runner.sicards.add(sicard)

    @staticmethod
    def _parse_sex(sex):
        if sex is None:
            return None
        sex = sex.lower()
        return (sex == 'm' and 'male'
                or sex == 'f' and 'female'
                or None)

class SOLVDBImporter(RunnerImporter):
    """Import runners from the SOLV runner database. Uses what the SOLV calls
    a VELPOZ data file. This can also be used to import reduced files which do not 
    contain all the columns of the SOLV database.
    Additionally to the fields of the SOLV database the fields "Angemeldete_Kategorie" and 
    "Bahn" are supported. They link the runner to the given Category and create an open run 
    for the given Course respectively.
    """

    def import_data(self, store):

        for i, r in enumerate(self.data):
            if self._verbose:
                print("%i: Adding %s %s" % (i+1, r.get('Vorname', ''),
                                            r.get('Name', '')))

            try:
                # check if we already know this SI-Card
                try:
                    sicard = RunnerImporter._get_sicard(r.get('SI_Karte', None), store)
                except InvalidSICardException as e:
                    print(("Runner %s %s (%s): %s" %
                           (r.get('Vorname', ''), r.get('Name', ''), r.get('SOLV-Nr', ''), str(e))))
                    sicard = None
                except NoSICardException as e:
                    sicard = None
                else:
                    if sicard.runner and not (sicard.runner.given_name == r.get('Vorname', None) and 
                                              sicard.runner.surname == r.get('Name', None)):
                        # This sicard is already assigned and the names do not match. Don't
                        # assign an sicard to this runner
                        print(("SI-card %i already assigned to runner %s %s. Can't assign to "
                               "runner %s %s on line %i" %
                               (sicard.id, sicard.runner.given_name, sicard.runner.surname,
                                r.get('Vorname'), r.get('Name'), i+2)))
                        sicard = None

                # check if we already know this runner
                # get solvnr and startnumber, treat empty values (eg. '') as None
                solvnr = r.get('SOLV-Nr', None) or None
                startnumber = r.get('Startnummer', None) or None
                runner = runner_solv = runner_number = runner_sicard = None
                if solvnr:
                    runner_solv = store.find(Runner, Runner.solvnr == solvnr).one()
                if startnumber:
                    runner_number = store.find(Runner, Runner.number == startnumber).one()
                if sicard:
                    runner_sicard = sicard.runner

                if ((runner_solv or runner_number or runner_sicard)
                    and len({runner_solv, runner_number, runner_sicard} - {None}) > 1): 
                    # we have matching runners for solvnr, number or sicard
                    # and they are not all the same
                    print(("SOLV Number %s, Start Number %s or SI-card %s are already in the "
                           "database and assigned to different runners. Skipping "
                           "entry for %s %s on line %i" %
                           (r.get('SOLV-Nr', ''), r.get('Startnummer', ''), r.get('SI-Karte', ''), r.get('Vorname', ''), r.get('Name', ''),
                            i+2)))
                    continue

                if runner_solv:
                    runner = runner_solv
                    print(("Runner %s %s with SOLV Number %s already exists. "
                           "Updating information." %
                           (runner.given_name, runner.surname, runner.solvnr)
                           ))
                elif runner_number:
                    runner = runner_number
                    print(("Runner %s %s with Start Number %s already exists. "
                           "Updating information." %
                           (runner.given_name, runner.surname, runner.number)
                           ))
                elif runner_sicard:
                    runner = runner_sicard
                    print(("Runner %s %s with SI-card %s already exists. "
                           "Updating information." %
                           (runner.given_name, runner.surname, sicard.id)
                           ))
                else:
                    runner = store.add(Runner(solvnr=solvnr, number=startnumber))

                if sicard:
                    RunnerImporter._add_sicard(runner, sicard, store)

                clubname = r.get('Verein', None)
                if clubname:
                    club = store.find(Club, Club.name == clubname).one()
                else:
                    club = None
                if not club and clubname is not None:
                    club = Club(r.get('Verein', ''))

                runner.given_name = r.get('Vorname', None)
                runner.surname = r.get('Name', None)
                runner.dateofbirth = RunnerImporter._parse_yob(r.get('Jahrgang', None))
                runner.sex = RunnerImporter._parse_sex(r.get('Geschlecht', None))
                nationname = r.get('Nation', None)
                if nationname:
                    runner.nation = store.find(Country, Country.code3 == nationname).one()
                runner.solvnr = solvnr
                runner.club = club
                runner.address1 = r.get('Adressz1', None)
                runner.address2 = r.get('Adressz2', None)
                runner.zipcode = r.get('PLZ', None)
                runner.city = r.get('Ort', None)
                countryname = r.get('Land', None)
                if countryname:
                    runner.address_country = store.find(Country, Country.code2 == countryname).one()
                runner.email = r.get('Email', None)
                runner.preferred_category = r.get('Kategorie', None)
                dop = r.get('Dop.Stat', None)
                if dop is not None:
                    runner.doping_declaration = bool(int(dop))

                # Add category if present
                categoryname = r.get('Angemeldete_Kategorie', None)
                if categoryname:
                    category = store.find(Category, Category.name == categoryname).one()
                    if not category:
                        category = Category(categoryname)
                    runner.category = category

                # Add run if course code is present
                coursecode = r.get('Bahn', None)
                if coursecode:
                    course = store.find(Course, Course.code == coursecode).one()
                    sicount = runner.sicards.count()
                    if sicount == 1 and course:
                        store.add(Run(runner.sicards.one(), course))
                    elif sicount != 1:
                        print(("Can't add run for runner %s %s on line %i: %s." %
                               (r.get('Vorname', ''), r.get('Name', ''), i+2,
                                sicount == 0 and "No SI-card" or "More than one SI-card")
                               ))
                    elif course is None:
                        print(("Can't add run for runner %s %s on line %i: Course not found" % 
                               (r.get('Vorname', ''), r.get('Name', ''), i+2)
                               ))

                store.flush()
            except (DataError, IntegrityError) as e:
                print(("Error importing runner %s %s on line %i: %s\n"
                       "Import aborted." %
                       (r.get('Vorname', ''), r.get('Name', ''), i+2, str(e).decode('utf-8', 'replace'))
                       ))
                store.rollback()
                return

class Team24hImporter(RunnerImporter):
    """Import participant data for 24h event from CSV file."""

    RUNNER_NUMBERS       = ['A', 'B', 'C', 'D', 'E', 'F']
    TEAM_NUMBER_FORMAT   = '%03d'
    RUNNER_NUMBER_FORMAT = '%(team)s%(runner)s'

    def import_data(self, store):

        # Create categories
        cat_24h = Category('24h')
        next_24h = 101
        cat_12h = Category('12h')
        next_12h = 201

        for t in self.data:

            # Create the team
            if t['Kurz'] == '24h':
                team = Team(Team24hImporter.TEAM_NUMBER_FORMAT % next_24h,
                            t['Teamname'], cat_24h)
                next_24h += 1
            elif t['Kurz'] == '12h':
                team = Team(Team24hImporter.TEAM_NUMBER_FORMAT % next_12h,
                            t['Teamname'], cat_12h)
                next_12h += 1

            # Create individual runners
            num = 0
            i = 1
            while num < int(t['NofMembers']):
                if t['Memyear%s' % str(i)] == '':
                    # discard runners with an empty year of
                    # birth
                    i += 1
                    continue

                runner = Runner(t['Memfamilyname%s' % str(i)],
                                t['Memfirstname%s' % str(i)])
                if t['Memsex%s' % str(i)] == 'M':
                    runner.sex = 'male'
                elif t['Memsex%s' % str(i)] == 'F':
                    runner.sex = 'female'
                runner.dateofbirth = RunnerImporter._parse_yob(t['Memyear%s' % str(i)])
                runner.number = Team24hImporter.RUNNER_NUMBER_FORMAT % \
                                {'team' : team.number,
                                 'runner' : Team24hImporter.RUNNER_NUMBERS[num]}

                # Add SI Card if valid
                try:
                    sicard = RunnerImporter._get_sicard(t['Memcardnr%s' % str(i)], store)
                except NoSICardException as e:
                    print(("Runner %s %s of Team %s (%s) has no SI-card." %
                           (runner.given_name, runner.surname, team.name, team.number)))
                except InvalidSICardException as e:
                    print(("Runner %s %s of Team %s (%s) has an invalid SI-card: %s" %
                           (runner.given_name, runner.surname, team.name, team.number,
                            str(e))))
                else:
                    RunnerImporter._add_sicard(runner, sicard, store)

                # Add runner to team
                team.members.add(runner)

                num += 1
                i += 1

            # Add team to store
            store.add(team)

class TeamRelayImporter(RunnerImporter):
    """Import participant data for a Relay."""

    # 0 leg needs 0 not '' otherwise the numbers do
    # not sort correctly as they are strings!
    RUNNER_NUMBERS       = ['0', '1', '2', '3']
    RUNNER_NUMBER_FORMAT = '%(runner)i%(team)02i'

    def import_data(self, store):

        self._categories = {}
        for line, t in enumerate(self.data):
            if not (t['Kategorie'] and t['Teamname']):
                if self._verbose:
                    print(
                        f'{line+1}: Skipping team withtout a category or name.',
                    )
                continue

            if self._verbose:
                print(("%i: Importing team %s (%s):" %
                       (line+1, t['Teamname'], t['AnmeldeNummer'])))

            try:
                # Create category
                if t['Kategorie'] not in self._categories:
                    cat = store.find(
                        Category, Category.name == t['Kategorie']
                    ).one()

                    if cat:
                        self._categories[t['Kategorie']] = cat
                    else:
                        self._categories[t['Kategorie']] = Category(t['Kategorie'])

                # Create the team
                team = Team(t['AnmeldeNummer'],
                                t['Teamname'], self._categories[t['Kategorie']])

                # Create individual runners
                num = 0
                i = 1
                while num < (self._fieldcount-4)/6:
                    surname = t['Name%s' % str(i)]
                    given_name =  t['Vorname%s' % str(i)]
                    number = TeamRelayImporter.RUNNER_NUMBER_FORMAT % \
                                    {'team' : int(team.number),
                                     'runner' : i}
                    if surname == '' and given_name == '':
                        # don't add runner without any name
                        i += 1
                        num += 1
                        continue

                    if self._verbose:
                        print(("  * Adding runner %s %s (%s)." %
                               (given_name, surname, number)))

                    runner = store.add(Runner(surname, given_name))
                    runner.sex = RunnerImporter._parse_sex(t.get('Geschlecht%s' % str(i), None))
                    runner.dateofbirth = RunnerImporter._parse_yob(t['Jahrgang%s' % str(i)]) 
                    runner.number = number

                    # Add SI Card if valid
                    try:
                        sicard = RunnerImporter._get_sicard(t['SI-Card%s' % str(i)], store)
                    except NoSICardException as e:
                        print(("Runner %s %s of Team %s (%s) has no SI-card." %
                               (runner.given_name, runner.surname, team.name, team.number)))
                    except InvalidSICardException as e:
                        print(("Runner %s %s of Team %s (%s) has an invalid SI-card: %s" %
                               (runner.given_name, runner.surname, team.name, team.number,
                                str(e))))
                    else:
                        RunnerImporter._add_sicard(runner, sicard, store)

                    # Add open run if SICard
                    try:
                        si = runner.sicards.one()
                    except NotOneError:
                        pass
                    else:
                        if si is not None:
                            r = store.add(Run(si))
                            r.set_coursecode(str(t['Bahn%s' % i]))

                    # Add runner to team
                    team.members.add(runner)

                    num += 1
                    i += 1

                # Add team to store
                store.add(team)
            except (DataError, IntegrityError) as e:
                print(("Error importing team %s (%s) on line %i: %s\n"
                       "Import aborted." %
                       (t['Teamname'], t['AnmeldeNummer'], line+2, e)
                       ))
                store.rollback()
                return


class SIRunImporter(Importer):
    """Import SICard readout data from a backup file.
       File Format:
       Course Code;SICard Number;ReadoutTime;StartTime;FinishTime;CheckTime;ClearTime;Control Code 1;Time1;Control Code 2;Time2;...
       Time Format is YYYY-MM-DD HH:MM:SS.ssssss
       Example:
       SE1;345213;2008-02-20 12:32:54.000000;2008-02-20 12:14:00.000000;2008-02-20 13:27:06.080200;2008-02-20 12:10:21.000000;2008-02-20 12:10:07.002000;32;2008-02-20 12:19:23.000000;76;2008-02-20 12:20:57.300000;...
       """

    timestamp_re = re.compile('([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})(\.([0-9]{6}))?')

    TIMEFORMAT = '%Y-%m-%d %H:%M:%S'

    COURSE = 0
    CARDNR = 1
    READOUT= 2
    START  = 3
    FINISH = 4
    CHECK  = 5
    CLEAR  = 6
    BASE   = 7

    def __init__(self, fname, replay = False, interval = 10, encoding = 'utf-8',
                 verbose = False):
        self._replay = replay
        self._interval = interval
        self._verbose = verbose
        csv = reader(open(fname, 'r', encoding=encoding),  delimiter=';')
        self.__runs = []
        for line in csv:
            try:
                if line[0].strip()[0] == '#':
                    # skip comment lines
                    continue
            except IndexError:
                pass
            self.__runs.append(line)

    @staticmethod
    def __datetime(punchtime):
        """Create a datetime object from a punchtime given as string in the
           format YYYY-MM-DD HH:MM:SS.ssssss."""

        if punchtime == '':
            return None

        match = SIRunImporter.timestamp_re.match(punchtime)
        if match is None:
            raise RunImportException('Invalid time format: %s' % punchtime)

        (year, month, day, hour, minute, second, dummy, microsecond) = \
               match.groups()
        if microsecond is None:
            microsecond = 0

        return datetime(int(year), int(month), int(day), int(hour),
                        int(minute), int(second), int(microsecond))

    def add_punch(self, station, timestring):
        """
        Adds a punch to the list of punches.

        """

        time = self.__datetime(timestring)
        if time is not None:
            self._punches.append((station, time))
        else:
            raise RunImportException('Empty punchtime for station "%s".' % station)

    def import_data(self, store):

        for line in self.__runs:
            course_code = line[SIRunImporter.COURSE]
            cardnr = line[SIRunImporter.CARDNR]

            self._punches = []
            i = SIRunImporter.BASE
            while i < len(line):
                self.add_punch(int(line[i]), line[i+1])
                i += 2

            run = Run(int(cardnr),
                      course = course_code,
                      punches = self._punches,
                      card_start_time = self.__datetime(line[SIRunImporter.START]),
                      card_finish_time = self.__datetime(line[SIRunImporter.FINISH]),
                      check_time = self.__datetime(line[SIRunImporter.CHECK]),
                      clear_time = self.__datetime(line[SIRunImporter.CLEAR]),
                      readout_time = self.__datetime(line[SIRunImporter.READOUT]),
                      store = store)
            run.complete = True
            store.add(run)
            if self._replay is True:
                print("Commiting Run %s for SI-Card %s" % (course_code, cardnr))
                store.commit()
                sleep(self._interval)

class SIRunExporter(SIRunImporter):
    """Export Run data to a backup file."""

    def __init__(self, fname, verbose = False):
        self.__file = open(fname, 'ab')
        self._verbose = verbose
        self.__csv = writer(self.__file, delimiter=';')

    @staticmethod
    def __punch2string(punch):
        """Convert a punch to a (sistationnr, timestring) tuple. If punch is
        None ('', '') is retruned.
        @param punch: punch to convert
        @type punch:  object of class Punch
        """
        if punch is None:
            return ('', '')

        return (str(punch.sistation.id),
                '%s.%06i' % (punch.punchtime.strftime(SIRunImporter.TIMEFORMAT),
                            punch.punchtime.microsecond)
                )

    def export_run(self, run):

        line = [''] * SIRunImporter.BASE
        line[SIRunImporter.COURSE] = run.course.code
        line[SIRunImporter.CARDNR] = run.sicard.id
        line[SIRunImporter.READOUT] = run.readout_time and run.readout_time.strftime(SIRunImporter.TIMEFORMAT) or ''
        line[SIRunImporter.START] = SIRunExporter.__punch2string(run.punches.find(Punch.sistation == SIStation.START).one())[1]
        line[SIRunImporter.CHECK] = SIRunExporter.__punch2string(run.punches.find(Punch.sistation == SIStation.CHECK).one())[1]
        line[SIRunImporter.CLEAR] = SIRunExporter.__punch2string(run.punches.find(Punch.sistation == SIStation.CLEAR).one())[1]
        line[SIRunImporter.FINISH] = SIRunExporter.__punch2string(run.punches.find(Punch.sistation == SIStation.FINISH).one())[1]
        for punch in run.punches.find(Not(Or(Punch.sistation == SIStation.START,
                                             Punch.sistation == SIStation.CLEAR,
                                             Punch.sistation == SIStation.CHECK,
                                             Punch.sistation == SIStation.FINISH
                                             ))):
            punch_string = SIRunExporter.__punch2string(punch)
            line.append(punch_string[0])
            line.append(punch_string[1])

        self.__csv.writerow(line)
        self.__file.flush()
        fsync(self.__file)

class OCADXMLCourseImporter(Importer):
    """Import Course Data from an OCAD XML File produced by OCAD 9."""

    # Known IOF Data Format versions
    KNOWN_VERSIONS = ('2.0.3', )

    # Known Root Tags
    KNOWN_ROOTTAGS = ('CourseData', )

    # XPaths to control point codes
    CONTROL_PATHS  = ('./StartPoint/StartPointCode',
                      './FinishPoint/FinishPointCode',
                      './Control/ControlCode',
                      )

    def __init__(self, fname, finish, start, verbose = False):
        self.__tree = parse(fname)
        self._start = start
        self._finish = finish
        self._verbose = False

        version = self.__tree.find('./IOFVersion').attrib['version']
        if not version in OCADXMLCourseImporter.KNOWN_VERSIONS:
            raise FileFormatException("Unknown IOFVersion '%s'" % version)

        roottag = self.__tree.getroot().tag
        if not roottag in OCADXMLCourseImporter.KNOWN_ROOTTAGS:
            raise FileFormatException("Wrong root tag: '%s'" % roottag)

    @staticmethod
    def __length(node, tag = 'total'):
        if tag == 'total':
            length_tag = 'CourseLength'
            climb_tag = 'CourseClimb'
        elif tag == 'control':
            length_tag = 'LegLength'
            climb_tag = 'LegClimb'
        elif tag == 'finish':
            length_tag = 'DistinceToFinish'
            climb_tag = 'ClimbToFinish'
        else:
            return (None, None)

        try:
            length = int(node.findtext(length_tag))
        except (TypeError, ValueError):
            length = None
        try:
            climb = int(node.findtext(climb_tag))
        except (TypeError, ValueError):
            if length is not None:
                # Set climb to 0 if length is given
                climb = 0
            else:
                climb = None

        return (length, climb)


    def import_data(self, store):

        # create SI Stations for start and finish if requested
        if self._start:
            station = store.get(SIStation, SIStation.START)
            if station is None:
                station = store.add(SIStation(SIStation.START))
        if self._finish:
            station = store.get(SIStation, SIStation.FINISH)
            if station is None:
                station = store.add(SIStation(SIStation.FINISH))

        # read control codes
        for path in OCADXMLCourseImporter.CONTROL_PATHS:
            for code_el in self.__tree.findall(path):
                code = code_el.text.strip() and str(code_el.text.strip()) or None
                if not code:
                    raise FileFormatException('Empty Control Code in Control Definition')
                # search for control in Store
                control = store.find(Control, Control.code == code).one()
                if control is None:
                    # Create new control
                    control = Control(code, store=store)

        # Read courses
        for c_el in self.__tree.findall('./Course'):
            variations = c_el.findall('CourseVariation')
            if len(variations) == 1:
                var = variations[0]
                # Get Course properties
                course_code = str(c_el.findtext('CourseName').strip())
                (length, climb) = OCADXMLCourseImporter.__length(var, 'total')
                course = Course(course_code, length, climb)
                store.add(course)

                # read control codes and sequence numbers into dict
                controls = {}
                for control_el in var.findall('CourseControl'):
                    code = control_el.findtext('ControlCode').strip()
                    if not code:
                        raise FileFormatException("Empty control code in definition of course '%s'" % course_code)
                    (length, climb) = OCADXMLCourseImporter.__length(control_el, 'control')
                    seq = int(control_el.findtext('Sequence').strip())
                    if seq in controls:
                        raise DuplicateSequenceException("Duplicate control sequence number '%s' in course" % seq)
                    controls[seq] = (code, length, climb)

                # sort controls by sequence number
                keys = sorted(list(controls.keys()))

                for seq in keys:
                    (code, length, climb) = controls[seq]
                    control = store.find(Control, Control.code == str(code)).one()
                    if not control:
                        raise ControlNotFoundException("Control with code '%s' not found." % code)
                    course.append(control, length, climb)


            elif len(variations) > 1:
                raise CourseTypeException('Courses with variations are not yet supported.')
            else:
                raise CourseTypeException('Course has no variations (at least 1 needed).')

class CSVCourseImporter(CSVImporter):
    """
    Import courses from a CSV file. The file format is:
    code;length;climb;1;2;...
    Coursecode1;courselength1;courseclimb1;control1;control2;...
    Coursecode2;courselength2;courseclimb2;control1;control2;...

    The first line is the header, all following lines are course definitions. All lengths are
    in meters.
    """

    def import_data(self, store):

        for c in self.data:

            if self._verbose:
                print("Importing course %s." % c['code'])

            # create course
            course = store.find(Course, Course.code == c['code']).one()
            if course:
                print("A course with code %s already exists. Updating course." % c['code'])
                for s in course.sequence:
                    store.remove(s)
                store.remove(course)
            course = store.add(Course(c['code'], int(c['length']), int(c['climb'])))

            # add controls
            for i in range(len(c)-3):
                code = c[str(i+1)]

                if code == '':
                    # end of course
                    break

                control = store.find(Control, Control.code == code).one()
                if control is None:
                    # Create new control
                    control = Control(code, store=store)

                course.append(control)

class SICardException(Exception):
    pass

class InvalidSICardException(SICardException):
    pass

class NoSICardException(SICardException):
    pass

class AlreadyAssignedSICardException(SICardException):
    pass

class RunImportException(Exception):
    pass

class InvalidStationNumberException(Exception):
    pass

class FileFormatException(Exception):
    pass

class CourseTypeException(Exception):
    pass

class ControlNotFoundException(Exception):
    pass

class DuplicateSequenceException(Exception):
    pass
