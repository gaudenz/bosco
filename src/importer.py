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

from storm.locals import *
from csv import reader
from optparse import OptionParser
from datetime import datetime, date
from elementtree.ElementTree import parse
from sys import exit
import re

import conf
from runner import Runner, Team, SICard, Category
from course import Control, Course, Course, SIStation
from run import Run, Punch

class Importer:
    """Base class for all Importer classes to import event
       data. This class provides the general interface for (GUI)
       import frontends."""
    
    def import_data(self, store):
        """Import runner data into store. Creates all the necessary objects
           and add them to the store, but don't commit the store."""
        pass

class CSVImporter(Importer):
    """Import form a CSV file. The first line of the file contains
       descriptive labels for the values. All further lines are read
       into a list of dictionaries using these labels."""

    def __init__(self, fname, encoding):

        # List of dicts
        self.data = []
        
        # Set up CSV reader
        csv = reader(open(fname, 'rb'), delimiter=';')

        # Read labels
        labels = csv.next()

        # Read values
        for line in csv:
            d = {}
            for i,v in enumerate(line):
                d[labels[i]] = v.decode(encoding)
                
            self.data.append(d)


class Team24hImporter(CSVImporter):
    """Import participant data for 24h event from CSV file."""

    RUNNER_NUMBERS       = ['A', 'B', 'C', 'D', 'E', 'F']
    TEAM_NUMBER_FORMAT   = u'%03d'
    RUNNER_NUMBER_FORMAT = u'%(team)s%(runner)s'
    
    def import_data(self, store):

        # Create categories
        cat_24h = Category(u'24h')
        next_24h = 1
        cat_12h = Category(u'12h')
        next_12h = 101

        for t in self.data:

            # search for team responsible by SOLV number
            responsible = store.find(Runner, Runner.solvnr == t['DatenbankId']).one()
            if not responsible:
                responsible = Runner(t['NName'], t['VName'])
                responsible.address1 = t['Straße']
                responsible.zipcode = t['PLZ']
                responsible.city = t['Wohnort']
                responsible.email = t['EMail']
                responsible.solvnr = t['DatenbankId']

            # Create the team
            if t['Kurz'] == '24h':
                team = Team(Team24hImporter.TEAM_NUMBER_FORMAT % next_24h,
                            t['Teamname'], responsible, cat_24h)
                next_24h += 1
            elif t['Kurz'] == '12h':
                team = Team(Team24hImporter.TEAM_NUMBER_FORMAT % next_12h,
                            t['Teamname'], responsible, cat_12h)
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
                    runner.sex = u'male'
                elif t['Memsex%s' % str(i)] == 'F':
                    runner.sex = u'female'
                runner.dateofbirth = date(int(t['Memyear%s' % str(i)]), 1, 1) 
                runner.number = Team24hImporter.RUNNER_NUMBER_FORMAT % \
                                {'team' : team.number,
                                 'runner' : Team24hImporter.RUNNER_NUMBERS[num]}

                # Add SI Card if valid
                if int(t['Memcardnr%s' % int(i)]) > 0:
                    runner.sicards.add(SICard(int(t['Memcardnr%s' % int(i)])))
                
                # Add runner to team
                team.members.add(runner)
                
                num += 1
                i += 1

            # Add team to store
            store.add(team)


class SIRunImporter(Importer):
    """Import SICard readout data from a backup file.
       File Format:
       Course Code;SICard Number;StartTime;FinishTime;CheckTime;ClearTime;Control Code 1;Time1;Control Code 2;Time2;...
       Time Format is YYYY-MM-DD HH:MM:SS.ssssss
       Example:
       SE1;345213;2008-02-20 12:14:00.000000;2008-02-20 13:27:06.080200;2008-02-20 12:10:21.000000;2008-02-20 12:10:07.002000;32;2008-02-20 12:19:23.000000;76;2008-02-20 12:20:57.300000;...
       """

    timestamp_re = re.compile('([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2}).([0-9]{6})')

    COURSE = 0
    CARDNR = 1
    START  = 2
    FINISH = 3
    CHECK  = 4
    CLEAR  = 5
    BASE   = 6
    
    def __init__(self, fname, encoding = 'utf-8'):
        csv = reader(open(fname, 'rb'), delimiter=';')
        self.__runs = []
        for line in csv:
            self.__runs.append([v.decode(encoding) for v in line])

    @staticmethod
    def __datetime(punchtime):
        """Create a datetime object from a punchtime given as string in the
           format YYYY-MM-DD HH:MM:SS.ssssss."""
        
        (year, month, day, hour, minute, second, microsecond) = \
               SIRunImporter.timestamp_re.match(punchtime).groups()
        
        return datetime(int(year), int(month), int(day), int(hour),
                        int(minute), int(second), int(microsecond))

    def import_data(self, store):

        for line in self.__runs:
            course_code = line[SIRunImporter.COURSE]
            cardnr = line[SIRunImporter.CARDNR]
            
            punches = []
            punches.append((SIStation.START,
                            self.__datetime(line[SIRunImporter.START])))
            punches.append((SIStation.FINISH,
                            self.__datetime(line[SIRunImporter.FINISH])))
            punches.append((SIStation.CHECK,
                            self.__datetime(line[SIRunImporter.CHECK])))
            punches.append((SIStation.CLEAR,
                            self.__datetime(line[SIRunImporter.CLEAR])))
            i = SIRunImporter.BASE
            while i < len(line):
                punches.append((int(line[i]), self.__datetime(line[i+1])))
                i += 2

            
            run = Run(int(cardnr), course_code, punches, store)
            run.complete = True
            store.add(run)


class OCADXMLCourseImporter(Importer):
    """Import Course Data from an OCAD XML File produced by OCAD 9."""

    # Known IOF Data Format versions
    KNOWN_VERSIONS = ('2.0.3', )

    # Known Root Tags
    KNOWN_ROOTTAGS = ('CourseData', )

    # XPaths to control point codes
    CONTROL_PATHS  = ('/StartPoint/StartPointCode',
                      '/FinishPoint/FinishPointCode',
                      '/Control/ControlCode',
                      )

    def __init__(self, fname, stations, finish, start):
        self.__tree = parse(fname)
        self.__stations = stations
        self.__finish = finish
        self.__start = start
        
        version = self.__tree.find('/IOFVersion').attrib['version']
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
        except (TypeError,ValueError):
            length = None
        try:
            climb = int(node.findtext(climb_tag))
        except (TypeError,ValueError):
            climb = None

        return (length, climb)

        
    def import_data(self, store):
        
        # read all control codes
        controls = {}

        # read start control codes
        for path in OCADXMLCourseImporter.CONTROL_PATHS:
            for code_el in self.__tree.findall(path):
                code = code_el.text.strip() and unicode(code_el.text.strip()) or None
                if not code:
                    raise FileFormatException('Empty Control Code in Control Definition')
                # search for control in Store
                control = store.find(Control, Control.code == code).one()
                if control is None:
                    # Create new control
                    control = store.add(Control(code))

                # add SI Stations if requested
                station = None
                if self.__start and code_el.tag == 'StartPointCode':
                    station = store.get(SIStation, SIStation.START)
                    if station is None:
                        station = store.add(SIStation(SIStation.START))
                elif self.__finish and code_el.tag == 'FinishPointCode':
                    station = store.get(SIStation, SIStation.FINISH)
                    if station is None:
                        station = store.add(SIStation(SIStation.FINISH))
                elif self.__stations and code_el.tag == 'ControlCode':
                    try:
                        station = store.get(SIStation, int(code))
                    except (TypeError, ValueError):
                        raise InvalidStationNumberException("Can't use code '%s' as si station number" % code)
                    if station is None:
                        station = store.add(SIStation(int(code)))
                if not station is None:
                    control.sistations.add(station)
                    
        # Read courses
        for c_el in self.__tree.findall('/Course'):
            variations = c_el.findall('CourseVariation')
            if len(variations) == 1:
                var = variations[0]
                # Get Course properties
                course_code = unicode(c_el.findtext('CourseName').strip())
                (length, climb) = OCADXMLCourseImporter.__length(var, 'total')
                course = Course(course_code, length, climb)
                store.add(course)

                # Set start point
                start_code = var.findtext('StartPointCode').strip()
                if start_code:
                    start = store.find(Control, Control.code == unicode(start_code)).one()
                    if start:
                        course.append(start)

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
                keys = controls.keys()
                keys.sort()
                
                for seq in keys:
                    (code, length, climb) = controls[seq]
                    control = store.find(Control, Control.code == unicode(code)).one()
                    if not control:
                        raise ControlNotFoundException("Control with code '%s' not found." % code)
                    course.append(control, length, climb)

                # Set finish point
                finish_code = var.findtext('FinishPointCode').strip()
                if finish_code:
                    (length, climb) = OCADXMLCourseImporter.__length(var, 'finish')
                    finish = store.find(Control, Control.code == unicode(finish_code)).one()
                    if finish:
                        course.append(finish)

                    

            elif len(variations) > 1:
                raise CourseTypeException('Courses with variations are not yet supported.')
            else:
                raise CourseTypeException('Course has no variations (at least 1 needed).')

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

if __name__ == '__main__':
    # Read program options
    opt = OptionParser(usage = 'usage: %prog [options] command importfile', 
                       description = 'Available commands are \'teams\', \'runs\' and \'courses\'.')
    opt.add_option('-e', '--encoding', action='store', default='utf-8',
                   help='Encoding of the imported file.')
    opt.add_option('-c', '--stations', action='store_true', default=False,
                   help='Automatically add SI-Stations with the same numbers as the controls.')
    opt.add_option('-f', '--finish', action='store_true', default=False,
                   help='Connect all finish points to the special SI Station for the finish.')
    opt.add_option('-s', '--start', action='store_true', default=False,
                   help='Connect all start points to the special SI Station for the start. Only use this option if you use SI Stations for the start.')
    (options, (command, filename)) = opt.parse_args()

    # Set up connection to datastore
    db = create_database(conf.db_uri)
    store = Store(db)


    if command == 'teams':
        # Import teams
        importer = Team24hImporter(filename, options.encoding)
    elif command == 'runs':
        # Import runs
        importer = SIRunImporter(filename, options.encoding)
    elif command == 'courses':
        # Import courses
        importer = OCADXMLCourseImporter(filename, options.stations,
                                         options.finish, options.start)
    else:
        print "Unknown command '%s'" % command
        exit(1)
        
    importer.import_data(store)
    store.commit()
