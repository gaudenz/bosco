#
#    Copyright (C) 2012  Gaudenz Steinlin <gaudenz@durcheinandertal.ch>
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
util.py - Utility functions
"""

import gettext
import os
import sys

from imp import find_module, load_module
from optparse import OptionParser

def load_config(name='conf'):
    # Install gettext functions, do this first so that it's available to
    # modules imported from config
    gettext.install('bosco', 'locale')

    oldpath = sys.path
    try:
        sys.path = [os.getcwd(), ]
        fp, pathname, description = find_module(name)
    finally:
        sys.path = oldpath

    try:
        return load_module(name, fp, pathname, description)
    finally:
        if fp:
            fp.close()


class RankingOptionParser(OptionParser):

    def __init__(self, event, *args, **kwargs):
        # super does not work here because OptionParser derives from OptionContainer
        # which is an old style class (see optparse.py)
        self._event = event
        OptionParser.__init__(self, *args, **kwargs)

        self.add_option('-r', '--rankings', action='store', default=None,
                        help='Comma separted list of rankings to show.')
        self.add_option('-l', '--list', action='store_true', default=False,
                        help='List all available rankings.')

    def parse_args(self):
        (options, args) = OptionParser.parse_args(self)

        # process rankings arguments
        if options.list:
            print('Available rankings:', end=' ')
            for (desc, r) in self._event.list_rankings():
                print("%s," % desc, end=' ')
            print()
            sys.exit()

        if options.rankings:
            ranking_codes = options.rankings.split(',')
            ranking_list = [ (desc, r) for desc, r in self._event.list_rankings() if desc in ranking_codes ]
        else:
            ranking_list = self._event.list_rankings()

        return (options, args, ranking_list)


class RankingFileOptionParser(RankingOptionParser):

    def parse_args(self):

        self.add_option(
            '-e', '--encoding', action='store', default='iso-8859-1',
            help='Output encoding. This defaults to iso-8859-1 because the '
                 'SOLV website is unable to handle more modern encodings.',
        )

        (options, args, ranking_list) = super().parse_args()

        # process file arguments
        if len(args) > 1:
            print("Can't write to more than one file!")
            sys.exit(1)
        if len(args) == 0:
            f = sys.stdout
        else:
            f = open(args[0], 'w', encoding=options.encoding)

        return (options, args, ranking_list, f)
