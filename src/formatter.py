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

import conf

class AbstractRankingFormatter(object):
    """Formats a ranking. str(rankingRormatter) returns the formatted ranking."""

    def __init__(self, ranking, entry_renderer = str):
        """
        @param ranking: the ranking to format
        @type ranking:  generator or list as returned by L{Rankable}s ranking method.
        @param entry_renderer: function to extract information about an entry
        """
        
        self._ranking = ranking
        self._entry_renderer = entry_renderer

    def __str__(self):
        """
        @return: Formatted Ranking
        """
        pass

class MakoRankingFormatter(AbstractRankingFormatter):
    """Uses the Mako Templating Engine to format a ranking as HTML."""

    _lookup = TemplateLookup(directories=[conf.template_dir])

    def __init__(self, ranking, template_file):
        super(type(self), self).__init__(ranking)
        self._template = MakoRankingFormatter._lookup.get_template(template_file)

    def __str__(self):
        return self._template.render(title = 'hier steht der titel', ranking = self._ranking)

        
    
