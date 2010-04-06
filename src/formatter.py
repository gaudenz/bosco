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

from mako.template import Template
from mako.lookup import TemplateLookup
from datetime import datetime
from StringIO import StringIO
from csv import writer

from ranking import Validator
from course import SIStation

class AbstractRankingFormatter(object):
    """Formats a ranking. str(rankingRormatter) returns the formatted ranking."""

    validation_codes = {Validator.OK               : 'OK',
                        Validator.NOT_COMPLETED    : 'not yet finished',
                        Validator.MISSING_CONTROLS : 'missing controls',
                        Validator.DID_NOT_FINISH   : 'did not finish',
                        Validator.DISQUALIFIED     : 'disqualified',
                        Validator.DID_NOT_START    : 'did not (yet) start'}
    
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
        @type ranking:        list of dicts with keys 'ranking' and 'info'
                              the value of the 'ranking' key is an object of
                              class Ranking
        @param template_file: File name for the template
        @param header:        gerneral information for the ranking header
        @type header:         dict
        """
        super(type(self), self).__init__(rankings)
        lookup = TemplateLookup(directories=[template_dir])
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
                        Validator.DID_NOT_START    : 'gest'}

    def __init__(self, ranking, reftime, encoding = 'utf-8',
                 lineterminator = '\n'):
        """
        @reftime: reference time for the event (usually first starttime)
        """
        AbstractRankingFormatter.__init__(self, ranking)
        self._reftime = reftime
        self._encoding = encoding
        self._lineterminator = lineterminator

    def _print_score(self, r):
        if r['validation']['status'] == Validator.OK:
            return str(r['scoreing']['score'])
        else:
            return self.validation_codes[r['validation']['status']]
        
    def __str__(self):
        raise SOLVRankingFormatterException('Use a subclass and overrwrite this method.')


class CourseSOLVRankingFormatter(AbstractSOLVRankingFormatter):
    
    def __str__(self):

        encoding = self._encoding
        

        outstr = StringIO()
        output = writer(outstr, delimiter=';',
                        lineterminator=self._lineterminator)
        for ranking in self.rankings:
            output.writerow([str(ranking.rankable),
                             ranking.rankable.length,
                             ranking.rankable.climb,
                             ranking.rankable.controlcount()
                             ])
            for r in ranking:
                line = [r['rank'] or '',
                        r['item'].sicard.runner.surname.encode(encoding),
                        r['item'].sicard.runner.given_name.encode(encoding),
                        r['item'].sicard.runner.dateofbirth and r['item'].sicard.runner.dateofbirth.strftime('%y') or '',
                        r['item'].sicard.runner.sex,
                        r['item'].sicard.runner.team.name.encode(encoding),
                        self._print_score(r),
                        ]
                try:
                    line.append(r['scoreing']['start'] - self._reftime)
                except TypeError:
                    line.append('')
                try:
                    line.append(r['scoreing']['finish'] - self._reftime)
                except TypeError:
                    line.append('')
                    
                for p in r['item'].punches.order_by('COALESCE(manual_punchtime, card_punchtime)'):
                    if (not p.sistation.control is None
                        and p.sistation.id > SIStation.SPECIAL_MAX):
                        line.extend([p.sistation.control.code.encode(encoding),
                                     p.punchtime - r['scoreing']['start']])

                output.writerow(line)

        return outstr.getvalue()

class CategorySOLVRankingFormatter(AbstractSOLVRankingFormatter):
    
    def __str__(self):

        encoding = self._encoding
        

        outstr = StringIO()
        output = writer(outstr, delimiter=';',
                        lineterminator=self._lineterminator)
        for ranking in self.rankings:
            output.writerow([str(ranking.rankable)])
            
            for r in ranking:
                line = [r['rank'] or '',
                        str(r['item']),
                        self._print_score(r),
                        ]
                    
                output.writerow(line)

        return outstr.getvalue()
