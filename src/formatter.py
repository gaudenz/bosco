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

class SOLVRankingFormatter(AbstractRankingFormatter):
    """Formats the Ranking for exporting to the SOLV result site."""

    def __init__(self, ranking, info, encoding = 'utf-8',
                 lineterminator = '\n'):
        """
        @param info: dict with informations about the course. Necessary keys:
                     code, length, climb, controlcount, reftime                     
        """
        super(type(self), self).__init__(ranking)
        self._info = info
        self._encoding = encoding
        self._lineterminator = lineterminator

    def __str__(self):

        info = self._info
        encoding = self._encoding
        

        outstr = StringIO()
        output = writer(outstr, delimiter=';',
                        lineterminator=self._lineterminator)
        output.writerow([info['code'], info['length'], info['climb'], info['controlcount']])
        for r in self._ranking:
            line = [r['rank'] or '',
                    r['item'].sicard.runner.surname.encode(encoding),
                    r['item'].sicard.runner.given_name.encode(encoding),
                    r['item'].sicard.runner.dateofbirth.strftime('%y'),
                    r['item'].sicard.runner.sex,
                    r['item'].sicard.runner.team.name.encode(encoding),
                    r['scoreing']['score'],
                    ]
            try:
                line.append(r['scoreing']['start'] - info['reftime'])
            except TypeError:
                line.append('')
            try:
                line.append(r['scoreing']['finish'] - info['reftime'])
            except TypeError:
                line.append('')
                    
            for p in r['item'].punches.order_by('punchtime'):
                if (not p.sistation.control is None
                    and p.sistation.id > SIStation.SPECIAL_MAX):
                     line.extend([p.sistation.control.code.encode(encoding),
                                  p.punchtime - r['scoreing']['start']])

            output.writerow(line)

        return outstr.getvalue()
