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
formatter.py - Classes to to format rankings
"""

import pkg_resources
import json

from mako.lookup import TemplateLookup

from reportlab.lib import colors, pagesizes
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet

from datetime import datetime
from io import StringIO
from csv import writer

from .ranking import Validator, ValidationError, UnscoreableException
from .course import SIStation, Control
from .run import Punch, Run

def format_timedelta(delta):
    (hours, seconds) = divmod(delta.seconds, 3600)
    (minutes, seconds) = divmod(seconds, 60)
    if hours > 0:
        return "%i:%02i:%02i" % (hours, minutes, seconds)
    else:
        return "%i:%02i" % (minutes, seconds)

class AbstractFormatter:

    validation_codes = {Validator.OK               : 'OK',
                        Validator.NOT_COMPLETED    : 'not yet finished',
                        Validator.MISSING_CONTROLS : 'missing controls',
                        Validator.DID_NOT_FINISH   : 'did not finish',
                        Validator.DISQUALIFIED     : 'disqualified',
                        Validator.DID_NOT_START    : 'did not start'}

class AbstractRankingFormatter(AbstractFormatter):
    """Formats a ranking. str(rankingRormatter) returns the formatted ranking."""

    def __init__(self, rankings):
        """
        @param ranking: the ranking to format
        @type ranking:  generator or list as returned by L{Rankable}s ranking method.
        """
        
        self.rankings = rankings

    def __str__(self):
        """
        @return: Formatted Ranking
        """
        pass

class MakoRankingFormatter(AbstractRankingFormatter):
    """Uses the Mako Templating Engine to format a ranking as HTML."""

    def __init__(self, rankings, header, template_file, template_dir):
        """
        @type rankings:        list of dicts with keys 'ranking' and 'info'
                              the value of the 'ranking' key is an object of
                              class Ranking
        @param template_file: File name for the template
        @param template_dir:  template directory (inside the bosco module)
        @param header:        gerneral information for the ranking header
        @type header:         dict
        """
        super(type(self), self).__init__(rankings)
        lookup = TemplateLookup(directories=[pkg_resources.resource_filename('bosco', template_dir)])
        self._template = lookup.get_template(template_file)
        self._header = header

    def __str__(self):

        return self._template.render_unicode(header = self._header,
                                             validation_codes = self.validation_codes,
                                             now = datetime.now().strftime('%c'),
                                             rankings = self.rankings)

class AbstractSOLVRankingFormatter(AbstractRankingFormatter):
    """Formats the Ranking for exporting to the SOLV result site."""

    validation_codes = {Validator.OK               : 'OK',
                        Validator.NOT_COMPLETED    : '',
                        Validator.MISSING_CONTROLS : 'fehl',
                        Validator.DID_NOT_FINISH   : 'aufg',
                        Validator.DISQUALIFIED     : 'disq',
                        Validator.DID_NOT_START    : 'n. gest'}

    def __init__(self, ranking, reftime, control_replacements = None, control_exclude = None,
                 lineterminator = '\n'):
        """
        @reftime: reference time for the event (usually first starttime)
        """
        AbstractRankingFormatter.__init__(self, ranking)
        self._reftime = reftime
        self._control_replacements = control_replacements if control_replacements is not None else {}
        self._control_exclude = control_exclude if control_exclude is not None else ()
        self._lineterminator = lineterminator

    def _print_score(self, r):
        if r['validation']['status'] == Validator.OK:
            return str(r['scoreing']['score'])
        else:
            return self.validation_codes[r['validation']['status']]

    def _control_code(self, control):
        try:
            return self._control_replacements[control.code]
        except KeyError:
            return control.code

    def _writer(self):
        self._outstr = StringIO()
        return writer(self._outstr, delimiter=';',
                      lineterminator=self._lineterminator)

    def _output(self):
        return self._outstr.getvalue()

    def __str__(self):
        raise SOLVRankingFormatterException('Use a subclass and overrwrite this method.')


class CourseSOLVRankingFormatter(AbstractSOLVRankingFormatter):
    """
    Formatting a course ranking to be uploaded to the SOLV website
    Format: Rank;Name;Firstname;YearOfBirth;SexMF;FedNr;Zip;Town;Club;NationIOF;Start Nr;eCardNr;RunTime;StartTime;FinishTime;CtrlCode;SplitTime
    """
    def __str__(self):

        output = self._writer()
        for ranking in self.rankings:
            output.writerow([str(ranking.rankable),
                             ranking.rankable.length,
                             ranking.rankable.climb,
                             ranking.rankable.controlcount()
                             ])
            for r in ranking:
                line = [r['rank'] or '',
                        r['item'].sicard.runner.surname,
                        r['item'].sicard.runner.given_name,
                        r['item'].sicard.runner.dateofbirth and r['item'].sicard.runner.dateofbirth.strftime('%y') or '',
                        r['item'].sicard.runner.sex,
                        '', # FedNR (?)
                        '', # Zip
                        '', # Town
                        r['item'].sicard.runner.team and r['item'].sicard.runner.team.name or '', # Club
                        '', # NationIOF
                        '', # Start Nr
                        '', # eCardNr
                        self._print_score(r),
                        ]
                try:
                    line.append(r['scoreing']['start'] - self._reftime)
                except (TypeError, KeyError):
                    line.append('')
                try:
                    line.append(r['scoreing']['finish'] - self._reftime)
                except (TypeError, KeyError):
                    line.append('')

                try:
                    punchlist = r['validation']['reordered_punchlist']
                except KeyError:
                    punchlist = r['validation']['punchlist']
                for status, p in punchlist:
                    if status == 'missing' and not p.code in self._control_exclude:
                        # p is an object of class Control
                        line.extend([self._control_code(p), ''])
                    if not status == 'ok':
                        # ignore additional punches
                        continue
                    if (not p.sistation.control is None
                        and p.sistation.id > SIStation.SPECIAL_MAX
                        and not p.sistation.control.code in self._control_exclude):
                        try:
                            line.extend([self._control_code(p.sistation.control),
                                         p.punchtime - r['scoreing']['start']])
                        except (TypeError, KeyError):
                            line.extend([self._control_code(p.sistation.control),
                                         ''])

                output.writerow(line)

        return self._output()

class CategorySOLVRankingFormatter(AbstractSOLVRankingFormatter):
    
    def __str__(self):

        output = self._writer()

        for ranking in self.rankings:
            output.writerow([str(ranking.rankable)])
            
            for r in ranking:
                line = [r['rank'] or '',
                        r['item'],
                        self._print_score(r),
                        ]
                    
                output.writerow(line)

        return self._output()

class RelayCategorySOLVRankingFormatter(AbstractSOLVRankingFormatter):
    """
    As there is no real documenation for the SOLV ranking format this is modeled
    after the file for "Osterstaffel 2012" made with ORWare.
    """

    def __str__(self):

        output = self._writer()
        for ranking in self.rankings:
            output.writerow([str(ranking.rankable)])

            for r in ranking:
                line = [r['rank'] or '',
                        r['item'].number,
                        r['item'],
                        '', # TODO: put nation of team into database
                        self._print_score(r),
                        r['scoreing']['behind'] or '',
                        '', # RelayAltStart, whatever that could be...
                        len(r['runs']),
                        ]
                for leg in range(len(r['runs'])):
                    leg_run = r['runs'][leg]
                    leg_split = r['splits'][leg]
                    if leg_run is not None:
                        run = leg_run['item']
                        runner = run.sicard.runner
                        line.extend([runner.surname or '',
                                     runner.given_name or '',
                                     runner.dateofbirth and runner.dateofbirth.year or '',
                                     run.course.code,
                                     leg_run['rank'] or '',
                                     self._print_score(leg_run),
                                     leg_run['scoreing']['behind'] or '',
                                     ])
                    else:
                        # No valid run on this leg
                        line.extend([''] * 7)
                    line.extend(['', # LegAltStart, whatever that could be...
                                 leg_split['rank'] or '',
                                 self._print_score(leg_split),
                                 leg_split['scoreing']['behind'] or '',
                                 ])
                output.writerow(line)

        return self._output()

class RoundCountRankingFormatter(AbstractSOLVRankingFormatter):
    
    def __str__(self):

        output = self._writer()

        for ranking in self.rankings:
            lines = []
            for r in ranking:
                if isinstance(r['item'], Run):
                    runner = r['item'].sicard.runner
                    run = r['item']
                else:
                    runner = r['item']
                    run = r['item'].run
                number = runner and runner.number or 0
                lines.append([r['rank'] or '',
                              run.sicard.id,
                              runner and runner.category or '',
                              number, # change index below if position of this element changes
                              runner and runner.given_name or '',
                              runner and runner.surname or '',

                              self._print_score(r),
                              ])

            # reorder by number instead of rank
            lines.sort(key=lambda x: int(x[3]))
            output.writerow([str(ranking.rankable)])
            output.writerows(lines)

        return self._output()


class OlanaRankingFormatter(AbstractSOLVRankingFormatter):

    def __str__(self):
        results = {
            'name': '',
            'map': '',
            'date': '',
            'startTime': str(self._reftime),
            'categories': [],
        }

        for ranking in self.rankings:
            cat = {
                'name':     str(ranking.rankable),
                'distance': ranking.rankable.length,
                'ascent':   ranking.rankable.climb,
                'controls': ranking.rankable.controlcount(),
                'runners':   [],
            }

            for r in ranking:
                run_dict = {
                    'fullName':    '%s %s' % (r['item'].sicard.runner.given_name, r['item'].sicard.runner.surname),
                    'yearOfBirth': r['item'].sicard.runner.dateofbirth and r['item'].sicard.runner.dateofbirth.strftime('%y') or '',
                    'sex':         r['item'].sicard.runner.sex,
                    'club':        r['item'].sicard.runner.team and r['item'].sicard.runner.team.name or '',
                    'city':        '',
                    'nation':      '',
                    'time':        self._print_score(r),
                    'ecard':       r['item'].sicard.id,
                }

                try:
                    run_dict['startTime'] = str(r['scoreing']['start'] - self._reftime)
                except (TypeError, KeyError):
                    run_dict['startTime'] = ''

                try:
                    punchlist = r['validation']['reordered_punchlist']
                except KeyError:
                    punchlist = r['validation']['punchlist']
                splits = []
                for status, p in punchlist:
                    if status == 'missing' and not p.code in self._control_exclude:
                        # p is an object of class Control
                        splits.append([self._control_code(p), ''])
                    if not status == 'ok':
                        # ignore additional punches
                        continue
                    if (not p.sistation.control is None
                        and p.sistation.id > SIStation.SPECIAL_MAX
                        and not p.sistation.control.code in self._control_exclude):
                        try:
                            splits.append([self._control_code(p.sistation.control),
                                           str(p.punchtime - r['scoreing']['start'])])
                        except (TypeError, KeyError):
                            splits.append([self._control_code(p.sistation.control), ''])
                run_dict['splits'] = splits
                run_dict['course'] = ','.join([s[0] for s in splits])

                cat['runners'].append(run_dict)

            results['categories'].append(cat)

        return json.dumps(results)


class AbstractRunFormatter(AbstractFormatter):
    """Formats a Run."""

    def __init__(self, run, header, event):
        """
        @param run    run to format
        @param header header information
        @type  header dict
        @param event  event this run belongs to
        """
        self._run = run
        self._header = header
        self._event = event

    def __str__(self):
        """
        @return formatted run
        """
        pass

    def _raw_punchlist(self):
        try:
            punchlist = self._event.validate(self._run)['punchlist']
        except ValidationError:
            # create pseudo validation result
            punchlist = [ ('ignored', p) for p in self._run.punches ]

        return punchlist

    def _punchlist(self, with_finish=False):

        raw_punchlist = self._raw_punchlist()
        punchlist = []
        try:
            lastpunch = start = self._event.score(self._run)['start']
        except UnscoreableException:
            lastpunch = start = self._run.start_time or None

        for code, p in raw_punchlist:
            if isinstance(p, Punch):
                punchtime = p.manual_punchtime or p.card_punchtime
                punchlist.append((
                    p.sequence and str(p.sequence) or '',
                    p.sistation.control and p.sistation.control.code or '',
                    str(p.sistation.id),
                    p.card_punchtime and str(p.card_punchtime) or '',
                    p.manual_punchtime and str(p.manual_punchtime) or '',
                    (punchtime and start
                     and format_timedelta(punchtime - start) or ''),
                    (punchtime and lastpunch
                     and format_timedelta(punchtime - lastpunch) or ''),
                    str(int(p.ignore)),
                    str(code),
                ))
                if code == 'ok':
                    lastpunch = punchtime
            elif isinstance(p, Control):
                punchlist.append(('',
                                  p.code,
                                  '',
                                  '',
                                  '',
                                  '',
                                  '',
                                  str(int(False)),
                                  code))
            elif isinstance(p, SIStation):
                punchlist.append(('',
                                  '',
                                  str(p.id),
                                  '',
                                  '',
                                  '',
                                  '',
                                  str(int(False)),
                                  code))
        if with_finish:
            punchtime = self._run.manual_finish_time or self._run.card_finish_time
            punchlist.append(('',
                              'Finish',
                              '',
                              self._run.card_finish_time and str(self._run.card_finish_time) or '',
                              self._run.manual_finish_time and str(self._run.manual_finish_time) or '',
                              punchtime and start and format_timedelta(punchtime - start) or '',
                              punchtime and lastpunch and format_timedelta(punchtime - lastpunch) or '',
                              str(int(False)),
                              'finish'))
        return punchlist

class ReportlabRunFormatter(AbstractRunFormatter):

    def __str__(self):
        try:
            validation = self._event.validate(self._run)
        except ValidationError as validation_error:
            validation = None
        try:
            score = self._event.score(self._run)
        except UnscoreableException:
            score = None
        
        io = StringIO()
        doc = SimpleDocTemplate(io, 
                                pagesize=pagesizes.landscape(pagesizes.A5), 
                                leftMargin = 20, rightMargin = 20, topMargin = 20, bottomMargin = 20)

        styles = getSampleStyleSheet()
        elements = []
        
        elements.append(Paragraph(("%(event)s / %(map)s / %(place)s / %(date)s / %(organiser)s" %
                                   self._header),
                                  styles['Normal']))
        elements.append(Spacer(0, 10))

        runner = self._run.sicard.runner
        elements.append(Paragraph("%s %s" % (str(runner), runner.number and 
                                             ("(%s)" % runner.number) or ''), 
                                  styles['Heading1']))
        elements.append(Paragraph("SI-Card: %s" % str(self._run.sicard.id), 
                                  styles['Normal']))
        course = self._run.course
        elements.append(Paragraph("<b>%s</b>" % (course and course.code or 'unknown course'), 
                                  styles['Normal']))
        elements.append(Spacer(0, 10))

        if validation and validation['status'] == Validator.OK:
            elements.append(Paragraph('<b>Laufzeit %s</b>' % score['score'], styles['Normal']))
        elif validation:
            elements.append(Paragraph('<b>%s</b>' % AbstractFormatter.validation_codes[validation['status']], 
                                      styles['Normal']))
        else:
            elements.append(Paragraph('<b>Validation error: %s</b>' % validation_error.message,
                                      styles['Normal']))
        elements.append(Spacer(0, 10))

        (punchtable, tablestyles) = self._format_punchlist()

        tablestyles = [('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                       ('FONT', (0, 0), (-1, -1), 'Helvetica'),
                       ('TOPPADDING', (0, 0), (-1, -1), 0),
                       ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                       ] + tablestyles
        t = Table(punchtable, )
        t.setStyle(TableStyle(tablestyles))
        t.hAlign = 'LEFT'
        elements.append(t)
        elements.append(Spacer(0, 20))

        elements.append(Paragraph("printed by Bosco, Free Orienteering Software, "
                                  "http://bosco.durcheinandertal.ch", styles['Normal']))

        doc.build(elements)

        return io.getvalue()

    def _format_punchlist(self, cols=10):
        punchlist = self._punchlist(with_finish = True)
        
        # format into triples (control, time, time_to_last)
        punch_triples = []
        ctrl_nr = 1
        for i, p in enumerate(punchlist):
            if p[8] in ('ok', 'missing'):
                control = "%i (%s)" % (ctrl_nr, p[1])
                ctrl_nr += 1
            elif p[8] == 'finish':
                control = "Finish"
            elif p[8] in ('additional', 'ignored'):
                control = "+ (%s)" % (p[1] != '' and p[1] or p[2])
            punch_triples.append((control, p[5] or 'missing', p[6]))

        # rearrange punch_triples by row for the output table
        i = 0
        table = []
        styles = []
        row_items = ([], [], [])
        while i < len(punchlist):
            if i > 0 and i % cols == 0:
                # new row
                table.extend(row_items)
                row_items = ([], [], [])
                rowcount = len(table)
                styles.append(('TOPPADDING', (0, rowcount), (-1, rowcount), 20))

            for j in range(3):
                row_items[j].append(punch_triples[i][j])
            i += 1
        # add last row
        table.extend(row_items)
        return (table, styles)


class MakoRunFormatter(AbstractRunFormatter):
    """
    Format runs using the Mako templating engine
    """

    def __init__(self, run, header, event, template_file, template_dir):
        """
        @param run            Run to format
        @type run             Run
        @param header:        gerneral information for the ranking header
        @type header:         dict
        @param event          Event object
        @param template_file: File name for the template
        @param template_dir:  template directory (inside the bosco module)
        """
        super().__init__(run, header, event)
        lookup = TemplateLookup(directories=[pkg_resources.resource_filename('bosco', template_dir)])
        self._template = lookup.get_template(template_file)

    def __str__(self):

        try:
            validation = self._event.validate(self._run)
        except ValidationError as validation_error:
            validation = None
        try:
            score = self._event.score(self._run)
        except UnscoreableException:
            score = None

        if validation and validation['status'] == Validator.OK:
            result = f'<b>Laufzeit: {score and score["score"] or ""}</b>'
        elif validation:
            code = type(self).validation_codes[validation['status']]
            result = f'<b>{code}</b>'
        else:
            result = f'<b>Validation error: {validation_error.message}</b>'

        return self._template.render_unicode(
            header=self._header,
            run=self._run,
            runner=self._run.sicard.runner,
            result=result,
            score=score,
            punchlist=self._punchlist(with_finish=True),
        )
