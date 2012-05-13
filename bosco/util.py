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

import os, sys
from imp import find_module, load_module

def load_config(name='conf'):
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
